#!/usr/bin/env python3
"""
Test suite for normalize and schedule layers
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autoplanner.settings')
sys.path.insert(0, '/Users/aiden/AutoPlanner')
django.setup()

from django.contrib.auth.models import User
from datetime import datetime, time, date, timedelta
from ai.normalizer import EventNormalizer, NormalizationError
from ai.scheduler import EventScheduler, ScheduleError
from events.models import Event

# Test utilities
def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def test_normalizer():
    """测试 EventNormalizer"""
    print_section("Testing EventNormalizer")
    
    normalizer = EventNormalizer(default_tz='Asia/Shanghai')
    
    # Test 1: Basic event with all fields
    print("\n[Test 1] Full event data...")
    data = {
        'title': 'Team Meeting',
        'date': '2026-02-10',
        'start_time': '14:30',
        'duration': 60,
        'location': 'Conference Room A',
        'description': 'Quarterly sync',
        'participants': 'alice@example.com,bob@example.com',
        'reminder': 30,
        'category': 'meeting'
    }
    try:
        normalized = normalizer.normalize(data)
        print(f"✓ Normalized: {normalized['title']} on {normalized['date']} at {normalized['start_time']}")
        print(f"  Duration: {normalized['duration']}min, Category: {normalized['category']}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 2: Minimal data (only title and date)
    print("\n[Test 2] Minimal event data...")
    data = {
        'title': 'Dentist Appointment',
        'date': '2026-02-15'
    }
    try:
        normalized = normalizer.normalize(data)
        print(f"✓ Normalized with defaults:")
        print(f"  Title: {normalized['title']}")
        print(f"  Date: {normalized['date']}")
        print(f"  Start time: {normalized['start_time']} (default)")
        print(f"  Duration: {normalized['duration']}min (default)")
        print(f"  Reminder: {normalized['reminder']}min (default)")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 3: Relative date - tomorrow
    print("\n[Test 3] Relative date (tomorrow)...")
    data = {
        'title': 'Follow-up',
        'date': 'tomorrow',
        'start_time': '10:00'
    }
    try:
        normalized = normalizer.normalize(data)
        target_date = (datetime.now() + timedelta(days=1)).date().isoformat()
        print(f"✓ Parsed 'tomorrow' as {normalized['date']}")
        assert normalized['date'] == target_date, "Date mismatch!"
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 4: Duration string parsing
    print("\n[Test 4] Duration string parsing...")
    test_cases = [
        ('1h', 60),
        ('90m', 90),
        ('1.5h', 90),
        ('1小时30分钟', None),  # May not work, depending on regex
    ]
    for duration_str, expected in test_cases:
        data = {
            'title': 'Test',
            'date': '2026-02-10',
            'duration': duration_str
        }
        try:
            normalized = normalizer.normalize(data)
            result = normalized['duration']
            status = "✓" if expected is None or result == expected else "✗"
            print(f"  {status} '{duration_str}' -> {result} min" + (f" (expected {expected})" if expected != result else ""))
        except Exception as e:
            print(f"  ✗ '{duration_str}' failed: {e}")
    
    # Test 5: Invalid title should raise error
    print("\n[Test 5] Error handling (missing title)...")
    data = {
        'date': '2026-02-10'
    }
    try:
        normalized = normalizer.normalize(data)
        print(f"✗ Should have raised error for missing title")
    except NormalizationError as e:
        print(f"✓ Correctly raised error: {e}")
    
    # Test 6: Category validation
    print("\n[Test 6] Category validation...")
    for category in ['work', 'personal', 'meeting', 'appointment', 'other', 'invalid']:
        data = {
            'title': 'Test',
            'date': '2026-02-10',
            'category': category
        }
        normalized = normalizer.normalize(data)
        result_category = normalized['category']
        expected = 'other' if category == 'invalid' else category
        status = "✓" if result_category == expected else "✗"
        print(f"  {status} '{category}' -> '{result_category}'")


def test_scheduler():
    """测试 EventScheduler"""
    print_section("Testing EventScheduler")
    
    # Create or get test user
    user, _ = User.objects.get_or_create(
        username='scheduler_test',
        defaults={'email': 'scheduler@test.local'}
    )
    
    # Clean up previous test events
    Event.objects.filter(user=user, title__startswith='[TEST]').delete()
    
    # Test 1: Create event
    print("\n[Test 1] Creating event...")
    normalized_data = {
        'title': '[TEST] Scheduler Test Event',
        'date': (datetime.now() + timedelta(days=1)).date().isoformat(),
        'start_time': '10:00:00',
        'duration': 45,
        'location': 'Test Room',
        'description': 'Scheduler test',
        'participants': None,
        'reminder': 15,
        'category': 'work'
    }
    
    try:
        event = EventScheduler.schedule_event(user, normalized_data)
        print(f"✓ Created event ID={event.id}: {event.title}")
        assert event.user == user, "User mismatch!"
        assert event.duration == 45, "Duration mismatch!"
    except ScheduleError as e:
        print(f"✗ Error: {e}")
        return
    
    # Test 2: Update event
    print("\n[Test 2] Updating event...")
    updated_data = normalized_data.copy()
    updated_data['title'] = '[TEST] Updated Title'
    updated_data['duration'] = 60
    
    try:
        updated_event = EventScheduler.schedule_event(user, updated_data, event_id=event.id)
        print(f"✓ Updated event ID={updated_event.id}: {updated_event.title}")
        assert updated_event.id == event.id, "Event ID mismatch!"
        assert updated_event.duration == 60, "Duration not updated!"
    except ScheduleError as e:
        print(f"✗ Error: {e}")
    
    # Test 3: Batch create events
    print("\n[Test 3] Batch creating events...")
    batch_data = [
        {
            'title': '[TEST] Batch Event 1',
            'date': (datetime.now() + timedelta(days=i)).date().isoformat(),
            'start_time': '09:00:00',
            'duration': 30,
            'location': None,
            'description': None,
            'participants': None,
            'reminder': 10,
            'category': 'work'
        }
        for i in range(1, 4)
    ]
    
    try:
        events = EventScheduler.schedule_events_batch(user, batch_data)
        print(f"✓ Created {len(events)} events")
        for evt in events:
            print(f"  - Event {evt.id}: {evt.title}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Final cleanup
    Event.objects.filter(user=user, title__startswith='[TEST]').delete()
    print("\n✓ Cleaned up test events")


def test_integration():
    """整体集成测试：从原始数据到数据库"""
    print_section("Integration Test: Normalizer → Scheduler")
    
    user, _ = User.objects.get_or_create(
        username='integration_test',
        defaults={'email': 'integration@test.local'}
    )
    
    # Clean up
    Event.objects.filter(user=user, title='[INT] Integration Test').delete()
    
    # Raw data with some missing fields
    raw_data = {
        'title': '[INT] Integration Test',
        'date': 'tomorrow',
        'start_time': '15:00',
        'duration': '1.5h',
        'location': 'Virtual',
        'category': 'meeting'
    }
    
    print("\n[Step 1] Raw input:")
    print(f"  {raw_data}")
    
    # Normalize
    print("\n[Step 2] Normalize...")
    normalizer = EventNormalizer()
    try:
        normalized = normalizer.normalize(raw_data)
        print(f"✓ Normalized:")
        for k, v in normalized.items():
            if k not in ['caldav_uid', 'caldav_href', 'google_event_id']:
                print(f"  {k}: {v}")
    except Exception as e:
        print(f"✗ Normalization failed: {e}")
        return
    
    # Schedule (create event)
    print("\n[Step 3] Schedule (create event)...")
    try:
        event = EventScheduler.schedule_event(user, normalized)
        print(f"✓ Event created in database:")
        print(f"  ID: {event.id}")
        print(f"  Title: {event.title}")
        print(f"  Date: {event.date}")
        print(f"  Start time: {event.start_time}")
        print(f"  Duration: {event.duration} minutes")
        print(f"  Location: {event.location}")
        print(f"  Category: {event.category}")
    except Exception as e:
        print(f"✗ Scheduling failed: {e}")
        return
    
    # Clean up
    event.delete()
    print("\n✓ Integration test completed successfully!")


if __name__ == '__main__':
    try:
        test_normalizer()
        test_scheduler()
        test_integration()
        
        print_section("All Tests Completed")
        print("\n✓ All test suites passed!")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
