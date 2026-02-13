from rest_framework import serializers

from .models import Event


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = [
            'id',
            'title',
            'date',
            'start_time',
            'duration',
            'location',
            'description',
            'participants',
            'reminder',
            'category',
            'caldav_uid',
            'caldav_href',
            'google_event_id',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'caldav_uid', 'caldav_href', 'google_event_id', 'created_at', 'updated_at']
