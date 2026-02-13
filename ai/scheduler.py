"""
Schedule layer: 从规范化字段生成事件实体
输入：规范化后的完整字段字典
输出：创建或更新的 Event 模型实例
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, time

from events.models import Event

logger = logging.getLogger(__name__)


class ScheduleError(Exception):
    """日程生成失败"""
    pass


class EventScheduler:
    """事件调度器：从规范化数据生成事件实体"""

    @staticmethod
    def schedule_event(
        user,
        normalized_data: Dict[str, Any],
        event_id: Optional[int] = None
    ) -> Event:
        """
        创建或更新一个 Event 实例
        
        :param user: Django User 实例（事件所有者）
        :param normalized_data: 规范化后的字段字典
        :param event_id: 如果指定，则更新现有事件；否则创建新事件
        :return: 创建或更新的 Event 实例（已保存）
        :raises ScheduleError: 创建/更新失败
        """
        
        try:
            # 类型转换
            date_obj = datetime.fromisoformat(normalized_data['date']).date()
            all_day = normalized_data.get('all_day') is True or not normalized_data.get('start_time') or not normalized_data.get('duration')
            if all_day:
                time_obj = time(0, 0)
                duration_min = 1440
            else:
                time_obj = time.fromisoformat(normalized_data['start_time'])
                duration_min = int(normalized_data['duration'])
            
            event_data = {
                'title': normalized_data['title'],
                'date': date_obj,
                'start_time': time_obj,
                'duration': duration_min,
                'location': normalized_data.get('location'),
                'description': normalized_data.get('description'),
                'participants': normalized_data.get('participants'),
                'reminder': normalized_data.get('reminder', 15),
                'category': normalized_data.get('category', 'other'),
            }
            
            # 保留现有的集成字段（如果存在）
            if event_id:
                try:
                    event = Event.objects.get(id=event_id, user=user)
                    # 更新字段
                    for key, value in event_data.items():
                        setattr(event, key, value)
                    event.save()
                    logger.info(f"Updated event {event.id}: {event.title}")
                    return event
                except Event.DoesNotExist:
                    raise ScheduleError(f"Event {event_id} not found for user {user.id}")
            
            else:
                # 创建新事件
                event = Event.objects.create(
                    user=user,
                    **event_data
                )
                logger.info(f"Created event {event.id}: {event.title}")
                return event
                
        except ScheduleError:
            raise
        except Exception as e:
            logger.exception(f"Failed to schedule event: {e}")
            raise ScheduleError(f"Event scheduling failed: {str(e)}")

    @staticmethod
    def schedule_events_batch(
        user,
        normalized_events: list
    ) -> list:
        """
        批量创建事件
        
        :param user: Django User 实例
        :param normalized_events: 规范化后的事件列表
        :return: 创建的 Event 实例列表
        """
        created_events = []
        errors = []
        
        for i, event_data in enumerate(normalized_events):
            try:
                event = EventScheduler.schedule_event(user, event_data)
                created_events.append(event)
            except ScheduleError as e:
                errors.append({
                    'index': i,
                    'title': event_data.get('title', 'Unknown'),
                    'error': str(e)
                })
                logger.warning(f"Batch event {i} failed: {e}")
        
        if errors:
            logger.warning(f"Batch scheduling completed with {len(errors)} error(s)")
        
        return created_events
