from django.conf import settings
from django.db import models


class Event(models.Model):
    CATEGORY_CHOICES = [
        ('work', 'Work'),
        ('personal', 'Personal'),
        ('meeting', 'Meeting'),
        ('appointment', 'Appointment'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='events',
    )
    title = models.CharField(max_length=200)
    date = models.DateField()
    start_time = models.TimeField()
    duration = models.PositiveIntegerField(help_text='Duration in minutes')
    location = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    participants = models.CharField(max_length=500, blank=True, null=True)
    reminder = models.PositiveIntegerField(default=15, help_text='Reminder minutes before')
    category = models.CharField(max_length=32, choices=CATEGORY_CHOICES, default='work')

    caldav_uid = models.CharField(max_length=255, blank=True, null=True)
    caldav_href = models.CharField(max_length=512, blank=True, null=True)
    google_event_id = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f'{self.title} ({self.date} {self.start_time})'

# Create your models here.
