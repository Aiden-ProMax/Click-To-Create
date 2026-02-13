from django.conf import settings
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from events.models import Event
from .services import sync_event_to_caldav


class SyncEventView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        event_id = request.data.get('event_id')
        if not event_id:
            return Response({'detail': 'event_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            event = Event.objects.get(id=event_id, user=request.user)
        except Event.DoesNotExist:
            return Response({'detail': 'Event not found'}, status=status.HTTP_404_NOT_FOUND)

        profile = getattr(request.user, 'profile', None)
        if not profile:
            return Response({'detail': 'Missing Radicale profile'}, status=status.HTTP_400_BAD_REQUEST)

        remote_event = sync_event_to_caldav(
            event=event,
            username=profile.radicale_username,
            password=profile.radicale_password,
        )

        if remote_event is not None:
            event.caldav_uid = getattr(remote_event, 'uid', None) or event.caldav_uid
            event.caldav_href = str(getattr(remote_event, 'url', None) or getattr(remote_event, 'href', '')) or event.caldav_href
            event.save(update_fields=['caldav_uid', 'caldav_href'])

        return Response({'detail': 'ok', 'caldav_href': event.caldav_href})


class CalDAVLinkView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile = getattr(request.user, 'profile', None)
        if not profile:
            return Response({'detail': 'Missing Radicale profile'}, status=status.HTTP_400_BAD_REQUEST)

        base_url = settings.RADICALE_BASE_URL or request.build_absolute_uri('/')[:-1]
        calendar = settings.RADICALE_DEFAULT_CALENDAR
        # Standard Radicale path: /<user>/<calendar>/
        link = f"{base_url.rstrip('/')}/{profile.radicale_username}/{calendar}/"
        return Response({'caldav_url': link})
