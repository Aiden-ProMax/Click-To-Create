import logging
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from django.conf import settings
from django.core.cache import cache
from events.serializers import EventSerializer

import secrets

from .services import parse_with_openai
from .normalizer import EventNormalizer, NormalizationError
from .scheduler import EventScheduler, ScheduleError

logger = logging.getLogger(__name__)


class ParseInputView(APIView):
    """
    解析用户输入（自然语言或粘贴内容）
    输入：text（自然语言）或 files（上传的文件）
    输出：JSON 格式的结构化事件数据（未规范化）
    
    POST /api/ai/parse/
    {
        "text": "Tomorrow at 3pm, team sync for 1 hour"
    }
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        text = request.data.get('text', '').strip()
        files = request.data.get('files', [])

        if not text and not files:
            return Response({
                'ok': False,
                'error': 'text or files required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            result = parse_with_openai(text)
            # If content is long/messy, constrain description to 2000 chars (prefer AI summary)
            if text and (len(text) >= 120 or text.count('\n') >= 2):
                events = result.get('events') if isinstance(result, dict) else None
                if isinstance(events, list):
                    for event in events:
                        if isinstance(event, dict):
                            desc = event.get('description') or ''
                            if not desc:
                                desc = text
                            if len(desc) > 2000:
                                desc = desc[:1999].rstrip() + '…'
                            event['description'] = desc
            logger.info("AI raw parsed result: %s", result)
            return Response({
                'ok': True,
                'data': result
            })
        except Exception as exc:
            logger.exception('AI parsing failed')
            return Response({
                'ok': False,
                'error': str(exc)
            }, status=status.HTTP_400_BAD_REQUEST)


class NormalizeEventView(APIView):
    """
    规范化事件字段（补全、转换、校验）
    输入：原始事件数据（可能缺失字段）
    输出：规范化后的完整字段
    
    POST /api/ai/normalize/
    {
        "events": [
            {
                "title": "Meeting",
                "date": "tomorrow",
                "start_time": "14:30",
                "duration": "1h"
            }
        ]
    }
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        events_data = request.data.get('events', [])

        if not events_data:
            return Response({
                'ok': False,
                'error': 'events list is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        normalizer = EventNormalizer(
            default_tz=settings.TIME_ZONE or 'UTC'
        )

        normalized_events = []
        errors = []

        for i, event_data in enumerate(events_data):
            try:
                normalized = normalizer.normalize(event_data)
                normalized_events.append(normalized)
            except NormalizationError as e:
                logger.warning(f"Event {i} normalization failed: {e}")
                errors.append({
                    'index': i,
                    'title': event_data.get('title', 'Unknown'),
                    'error': str(e)
                })

        return Response({
            'ok': len(normalized_events) > 0,
            'normalized_events': normalized_events,
            'errors': errors if errors else None
        })


class ScheduleEventsView(APIView):
    """
    从规范化数据创建或更新事件
    输入：规范化后的完整字段列表
    输出：创建的 Event 实例
    
    POST /api/ai/schedule/
    {
        "events": [
            {
                "title": "Meeting",
                "date": "2026-02-06",
                "start_time": "14:30:00",
                "duration": 60,
                ...
            }
        ]
    }
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        events_data = request.data.get('events', [])

        if not events_data:
            return Response({
                'ok': False,
                'error': 'events list is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        created_events = []
        errors = []

        for i, event_data in enumerate(events_data):
            try:
                event = EventScheduler.schedule_event(
                    user=request.user,
                    normalized_data=event_data
                )
                serializer = EventSerializer(event)
                created_events.append(serializer.data)
            except ScheduleError as e:
                logger.warning(f"Event {i} scheduling failed: {e}")
                errors.append({
                    'index': i,
                    'title': event_data.get('title', 'Unknown'),
                    'error': str(e)
                })

        return Response({
            'ok': len(created_events) > 0,
            'created_events': created_events,
            'errors': errors if errors else None
        }, status=status.HTTP_201_CREATED if created_events else status.HTTP_400_BAD_REQUEST)


class ParseNormalizeScheduleView(APIView):
    """
    端到端流程：parse → normalize → schedule
    一次性请求直接从自然语言文本创建事件
    
    POST /api/ai/process/
    {
        "text": "Tomorrow at 3pm team meeting for 1 hour in room A"
    }
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        text = request.data.get('text', '').strip()

        if not text:
            return Response({
                'ok': False,
                'error': 'text is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Step 1: Parse
        logger.info(f"Processing: {text[:100]}")
        try:
            parsed = parse_with_openai(text)
        except Exception as exc:
            logger.exception('AI parsing failed')
            return Response({
                'ok': False,
                'error': f'Parsing failed: {str(exc)}'
            }, status=status.HTTP_400_BAD_REQUEST)

        events_to_parse = parsed.get('events', [])
        if not events_to_parse:
            return Response({
                'ok': False,
                'error': 'No events found in parsed text'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Step 2: Normalize
        normalizer = EventNormalizer(
            default_tz=settings.TIME_ZONE or 'UTC'
        )
        normalized_events = []
        normalize_errors = []

        for i, event_data in enumerate(events_to_parse):
            try:
                normalized = normalizer.normalize(event_data)
                normalized_events.append(normalized)
            except NormalizationError as e:
                logger.warning(f"Event {i} normalization failed: {e}")
                normalize_errors.append({
                    'index': i,
                    'title': event_data.get('title', 'Unknown'),
                    'error': str(e)
                })

        if not normalized_events:
            return Response({
                'ok': False,
                'error': 'All events failed normalization',
                'errors': normalize_errors
            }, status=status.HTTP_400_BAD_REQUEST)

        # Step 3: Schedule
        created_events = []
        schedule_errors = []

        for i, event_data in enumerate(normalized_events):
            try:
                event = EventScheduler.schedule_event(
                    user=request.user,
                    normalized_data=event_data
                )
                serializer = EventSerializer(event)
                created_events.append(serializer.data)
            except ScheduleError as e:
                logger.warning(f"Event {i} scheduling failed: {e}")
                schedule_errors.append({
                    'index': i,
                    'title': event_data.get('title', 'Unknown'),
                    'error': str(e)
                })

        all_errors = normalize_errors + schedule_errors

        return Response({
            'ok': len(created_events) > 0,
            'created_events': created_events,
            'errors': all_errors if all_errors else None
        }, status=status.HTTP_201_CREATED if created_events else status.HTTP_400_BAD_REQUEST)


class AiDataStashView(APIView):
    """
    Store large AI payload server-side to avoid URL/sessionStorage issues.
    POST /api/ai/stash/  { "data": {...} }
    GET  /api/ai/stash/<key>/  -> { "ok": true, "data": {...} }
    """
    permission_classes = [permissions.IsAuthenticated]
    cache_ttl_seconds = 600

    def post(self, request):
        payload = request.data.get('data')
        if payload is None:
            return Response({'ok': False, 'error': 'data is required'}, status=status.HTTP_400_BAD_REQUEST)
        key = secrets.token_urlsafe(16)
        cache_key = f'ai_stash:{key}'
        cache.set(cache_key, payload, timeout=self.cache_ttl_seconds)
        return Response({'ok': True, 'key': key, 'ttl': self.cache_ttl_seconds})

    def get(self, request, key: str):
        cache_key = f'ai_stash:{key}'
        payload = cache.get(cache_key)
        if payload is None:
            return Response({'ok': False, 'error': 'not_found'}, status=status.HTTP_404_NOT_FOUND)
        # One-time read to prevent stale reuse
        cache.delete(cache_key)
        return Response({'ok': True, 'data': payload})
