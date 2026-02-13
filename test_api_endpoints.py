#!/usr/bin/env python3
"""
Test the new AI API endpoints: normalize, schedule, and end-to-end process
"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = 'http://localhost:8000'

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_response(response):
    print(f"Status: {response.status_code}")
    try:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
    except:
        print(f"Response: {response.text}")

print_section("Testing AI API Endpoints")

# Setup: Register and login
print("\n[Setup] Registering and logging in...")
session = requests.Session()

# Get CSRF token
response = session.get(f'{BASE_URL}/api/auth/csrf/')
csrf_token = response.json().get('csrfToken')
headers = {'X-CSRFToken': csrf_token}

# Register
user_data = {
    'username': f'aitest_{datetime.now().timestamp()}',
    'email': f'aitest_{datetime.now().timestamp()}@example.com',
    'password': 'TestPassword123!',
    'first_name': 'AI',
    'last_name': 'Test'
}
session.post(f'{BASE_URL}/api/auth/register/', json=user_data, headers=headers)

# Login
session.post(
    f'{BASE_URL}/api/auth/login/',
    json={'username': user_data['username'], 'password': user_data['password']},
    headers=headers
)

# Get fresh CSRF token
response = session.get(f'{BASE_URL}/api/auth/csrf/')
csrf_token = response.json().get('csrfToken')
headers['X-CSRFToken'] = csrf_token

print("✓ Setup complete")

# Test 1: Normalize endpoint
print_section("Test 1: Normalize Endpoint")

normalize_data = {
    'events': [
        {
            'title': 'API Test Normalize',
            'date': 'tomorrow',
            'start_time': '14:00',
            'duration': '1.5h',
            'location': 'Conference Room',
            'category': 'meeting'
        }
    ]
}

response = session.post(
    f'{BASE_URL}/api/ai/normalize/',
    json=normalize_data,
    headers=headers
)
print_response(response)

if response.status_code == 200:
    data = response.json()
    if data['ok'] and data['normalized_events']:
        print("✓ Normalize endpoint works!")

# Test 2: Schedule endpoint (using output from normalize)
print_section("Test 2: Schedule Endpoint")

if response.status_code == 200 and data['ok']:
    schedule_data = {
        'events': data['normalized_events']
    }
    
    response = session.post(
        f'{BASE_URL}/api/ai/schedule/',
        json=schedule_data,
        headers=headers
    )
    print_response(response)
    
    if response.status_code == 201:
        schedule_result = response.json()
        if schedule_result['ok'] and schedule_result['created_events']:
            print("✓ Schedule endpoint works!")
            created_event_id = schedule_result['created_events'][0]['id']

# Test 3: Parse endpoint (requires valid OpenAI API key)
print_section("Test 3: Parse Endpoint (Optional - requires OpenAI)")

parse_data = {
    'text': 'Schedule a meeting tomorrow at 3pm for 1 hour with alice@example.com'
}

response = session.post(
    f'{BASE_URL}/api/ai/parse/',
    json=parse_data,
    headers=headers
)

if response.status_code == 200:
    data = response.json()
    print_response(response)
    if data['ok']:
        print("✓ Parse endpoint works!")
    else:
        print(f"✗ Parse failed: {data.get('error', 'Unknown error')}")
else:
    print(f"Status: {response.status_code}")
    print("Note: Parse endpoint requires valid OPENAI_API_KEY")
    if response.status_code == 400:
        try:
            print(f"Error: {response.json().get('error', response.text)}")
        except:
            print(f"Response: {response.text}")

# Test 4: End-to-end process endpoint (optional, requires OpenAI)
print_section("Test 4: End-to-End Process (Optional - requires OpenAI)")

process_data = {
    'text': 'Create two events: 1) Coffee break at 10am tomorrow and 2) Team standup at 11:30am'
}

response = session.post(
    f'{BASE_URL}/api/ai/process/',
    json=process_data,
    headers=headers
)

print(f"Status: {response.status_code}")
if response.status_code in [201, 400]:
    try:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        if response.status_code == 201 and data.get('ok'):
            print("✓ Process endpoint works end-to-end!")
    except:
        print(f"Response: {response.text}")
else:
    print("Note: Process endpoint requires valid OPENAI_API_KEY")

# Test 5: Verify events were created
print_section("Test 5: Verify Events in Database")

response = session.get(f'{BASE_URL}/api/events/', headers=headers)
if response.status_code == 200:
    events = response.json()
    print(f"✓ User has {len(events)} event(s)")
    for evt in events[-3:]:  # Show last 3 events
        print(f"  - {evt['title']} on {evt['date']} at {evt['start_time']}")

print_section("API Endpoint Tests Complete")
print("\n✓ All tests completed!")
