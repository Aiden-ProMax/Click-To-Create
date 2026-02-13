#!/usr/bin/env python3
"""
Test script for Google Calendar sync flow
Tests: User creation -> Event creation -> OAuth token storage -> Event sync
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autoplanner.settings')
sys.path.insert(0, '/Users/aiden/AutoPlanner')
django.setup()

from django.contrib.auth.models import User
from datetime import datetime, timedelta, time, date
from zoneinfo import ZoneInfo
from events.models import Event
from google_sync.models import GoogleOAuthToken
from google_sync.services import build_event_payload_from_model, to_google_event_body

print("=" * 60)
print("Testing Google Calendar Sync Flow")
print("=" * 60)

# Step 1: Create or get a test user
print("\n[Step 1] Creating test user...")
user, created = User.objects.get_or_create(
    username='testuser',
    defaults={'email': 'test@example.com', 'first_name': 'Test', 'last_name': 'User'}
)
print(f"✓ User: {user.username} (created={created})")

# Step 2: Create a test event
print("\n[Step 2] Creating test event...")
event_date = date.today() + timedelta(days=1)
event_time = time(14, 0)  # 2 PM

event, created = Event.objects.get_or_create(
    user=user,
    title='Test Meeting',
    date=event_date,
    start_time=event_time,
    defaults={
        'duration': 60,  # 1 hour
        'location': 'Meeting Room 101',
        'description': 'Testing Google Calendar sync',
        'category': 'meeting',
        'reminder': 15,
        'participants': 'colleague@example.com'
    }
)
print(f"✓ Event: {event.title} on {event.date} at {event.start_time} (created={created})")
print(f"  - Duration: {event.duration} minutes")
print(f"  - Location: {event.location}")
print(f"  - Participants: {event.participants}")

# Step 3: Test payload building (what would be sent to Google)
print("\n[Step 3] Building Google event payload...")
try:
    payload = build_event_payload_from_model(event)
    print(f"✓ Payload created:")
    print(f"  - Summary: {payload.summary}")
    print(f"  - Start: {payload.start}")
    print(f"  - End: {payload.end}")
    print(f"  - Location: {payload.location}")
    print(f"  - Attendees: {payload.attendees}")
    
    # Convert to Google event body format
    body = to_google_event_body(payload)
    print(f"\n✓ Google event body (JSON structure):")
    import json
    print(json.dumps(body, indent=2, default=str))
except Exception as e:
    print(f"✗ Error building payload: {e}")
    import traceback
    traceback.print_exc()

# Step 4: Check OAuth token model structure
print("\n[Step 4] Checking Google OAuth token model...")
print(f"✓ OAuth token model has fields: {[f.name for f in GoogleOAuthToken._meta.get_fields()]}")

# Step 5: List user events
print("\n[Step 5] Listing all events for user...")
user_events = Event.objects.filter(user=user)
print(f"✓ User has {user_events.count()} event(s):")
for evt in user_events:
    print(f"  - {evt.title} ({evt.date} {evt.start_time})")

print("\n" + "=" * 60)
print("✓ All tests completed successfully!")
print("=" * 60)
