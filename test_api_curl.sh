#!/bin/bash
# Test the AI stash endpoint with curl

echo "=== Testing AI Data Flow via API ==="
echo ""

# Get CSRF token first by accessing the dashboard
echo "1. Getting CSRF token..."
CSRF=$(curl -s -c /tmp/cookies.txt http://localhost:8000/dashboard.html | grep -oP 'csrftoken=\K[^"]+' || echo "")
echo "Note: Testing without authentication will return 403 (expected for unauthenticated users)"
echo ""

# Try to access stash endpoint (should be 403 without auth)
echo "2. Testing stash endpoint (POST) without authentication..."
curl -s -b /tmp/cookies.txt \
  -X POST http://localhost:8000/api/ai/stash/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: test" \
  -d '{"data": {"events": [{"title": "Test"}]}}' | python3 -m json.tool
echo ""

# Check if the endpoint exists
echo "3. Testing API endpoint availability..."
curl -s -w "Status: %{http_code}\n" http://localhost:8000/api/ai/stash/ | tail -1
echo ""

echo "=== Test Complete ==="
