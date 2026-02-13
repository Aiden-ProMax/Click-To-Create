#!/usr/bin/env python3
"""
Test script to verify the complete AI data flow
- AI Parse API
- Stash endpoint
- Frontend data loading from stash
"""
import os
import sys
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autoplanner.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from django.core.cache import cache

def test_stash_endpoint():
    """Test the stash endpoint for storing and retrieving AI data"""
    print("\n=== Testing Stash Endpoint ===")
    
    client = APIClient()
    
    # Create a test user
    try:
        user = User.objects.get(username='testuser')
    except User.DoesNotExist:
        user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass')
    
    client.force_authenticate(user=user)
    
    # Test data that mimics AI parse output
    test_data = {
        "events": [
            {
                "title": "Team Meeting",
                "date": "2026-02-11",
                "start_time": "14:00",
                "duration": 60,
                "all_day": False,
                "location": "Conference Room A",
                "description": "Weekly team sync",
                "participants": "alice@example.com,bob@example.com",
                "reminder": 15,
                "category": "meeting",
                "timezone": "America/Los_Angeles",
                "repeat": "weekly",
                "notes": None
            }
        ]
    }
    
    # POST to stash
    print(f"1. Posting test data to /api/ai/stash/")
    print(f"   Data: {json.dumps(test_data, indent=2)[:200]}...")
    
    response = client.post('/api/ai/stash/', 
        data=json.dumps({'data': test_data}),
        content_type='application/json'
    )
    
    print(f"   Response status: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    if response.status_code != 200:
        print("❌ Stash POST failed")
        return False
    
    stash_key = response.json().get('key')
    print(f"✅ Stash key received: {stash_key}")
    
    # GET from stash
    print(f"\n2. Fetching data from /api/ai/stash/{stash_key}/")
    response = client.get(f'/api/ai/stash/{stash_key}/')
    
    print(f"   Response status: {response.status_code}")
    response_data = response.json()
    print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
    
    if response.status_code != 200:
        print("❌ Stash GET failed")
        return False
    
    retrieved_data = response_data.get('data')
    if not retrieved_data:
        print("❌ No data returned from stash")
        return False
    
    print(f"✅ Data retrieved from stash")
    
    # Verify structure
    if 'events' in retrieved_data and isinstance(retrieved_data['events'], list):
        print(f"✅ Data structure is valid: events array with {len(retrieved_data['events'])} items")
    else:
        print("❌ Data structure is invalid")
        return False
    
    # Try to GET again (should fail - one-time read)
    print(f"\n3. Testing one-time read (second fetch should fail)")
    response = client.get(f'/api/ai/stash/{stash_key}/')
    if response.status_code == 404:
        print(f"✅ Stash correctly deleted after one-time read")
    else:
        print(f"⚠️  Expected 404 but got {response.status_code}")
    
    return True

def test_normalize_schedule():
    """Test the normalize → schedule flow"""
    print("\n=== Testing Normalize → Schedule Flow ===")
    
    client = APIClient()
    
    # Create a test user
    try:
        user = User.objects.get(username='testuser2')
    except User.DoesNotExist:
        user = User.objects.create_user(username='testuser2', email='test2@example.com', password='testpass')
    
    client.force_authenticate(user=user)
    
    # Test raw event data
    raw_event = {
        "title": "Lunch Meeting",
        "date": "2026-02-11",
        "start_time": "12:00",
        "duration": 60,
        "location": "Restaurant",
        "description": "Lunch with team",
        "participants": None,
        "category": "personal"
    }
    
    # Normalize
    print(f"1. Normalizing event")
    print(f"   Input: {json.dumps(raw_event, indent=2)[:150]}...")
    
    response = client.post('/api/ai/normalize/', 
        data=json.dumps({'events': [raw_event]}),
        content_type='application/json'
    )
    
    print(f"   Response status: {response.status_code}")
    response_data = response.json()
    
    if response.status_code != 200 or not response_data.get('ok'):
        print(f"❌ Normalization failed: {response_data}")
        return False
    
    normalized = response_data.get('normalized_events', [])[0] if response_data.get('normalized_events') else None
    if not normalized:
        print("❌ No normalized event returned")
        return False
    
    print(f"✅ Normalization successful")
    print(f"   Output: {json.dumps(normalized, indent=2)[:150]}...")
    
    # Schedule
    print(f"\n2. Scheduling event (creating)")
    response = client.post('/api/ai/schedule/', 
        data=json.dumps({'events': [normalized]}),
        content_type='application/json'
    )
    
    print(f"   Response status: {response.status_code}")
    response_data = response.json()
    
    if response.status_code != 201 or not response_data.get('ok'):
        print(f"❌ Scheduling failed: {response_data}")
        return False
    
    created = response_data.get('created_events', [])[0] if response_data.get('created_events') else None
    if not created:
        print("❌ No created event returned")
        return False
    
    print(f"✅ Event created successfully")
    print(f"   Event ID: {created.get('id')}")
    print(f"   Title: {created.get('title')}")
    
    return True

if __name__ == '__main__':
    print("=" * 50)
    print("AI Data Flow Test Suite")
    print("=" * 50)
    
    try:
        success = True
        success = test_stash_endpoint() and success
        success = test_normalize_schedule() and success
        
        print("\n" + "=" * 50)
        if success:
            print("✅ All tests passed!")
        else:
            print("❌ Some tests failed")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
