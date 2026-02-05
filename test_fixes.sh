#!/bin/bash

# Test Video & Mockup Fixes

echo "🧪 Testing Video Duration & Mockup Parameter Fixes"
echo "=================================================="
echo ""

API_URL="http://localhost:8000/chat"

# Test 1: Video with string duration
echo "[1/3] Video Duration String Parsing"
echo "Request: Generate 15 second video (should parse to 10s)"
curl -s -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Generate a 15 second video showing a nature scene with mountains",
    "thread_id": "test-video-string-duration"
  }' | jq -r '
    "Status: " + (if .response then "SUCCESS" else "PENDING" end),
    "Response length: " + (.response | length | tostring),
    "Check logs for: Video duration constrained to 10 seconds"
  ' 2>/dev/null

echo ""
echo ""
sleep 2

# Test 2: Mockup with prompt parameter
echo "[2/3] Mockup Prompt Parameter"
echo "Request: Mockup with full scene description (prompt parameter)"
curl -s -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Create a product mockup: coffee mug on wooden table, cozy cafe setting, warm lighting",
    "thread_id": "test-mockup-prompt"
  }' | jq -r '
    "Status: " + (if .response then "SUCCESS" else "PENDING" end),
    "Artifacts: " + (.artifacts | length | tostring)
  ' 2>/dev/null

echo ""
echo ""
sleep 2

# Test 3: Combined workflow (what failed before)
echo "[3/3] Combined Video Ad Workflow"
echo "Request: Product mockup + 15s video ad"
curl -s -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Create a mug mockup showing a husky design, then generate a 15 second product video ad for it",
    "thread_id": "test-combined-fix"
  }' | jq -r '
    "Status: " + (if .response then "SUCCESS" else "PENDING" end),
    "Steps: " + (.steps_executed | length | tostring),
    "Artifacts: " + (.artifacts | length | tostring)
  ' 2>/dev/null

echo ""
echo ""
echo "=================================================="
echo "✅ Tests complete! Check server logs for details:"
echo "   tail -50 logs/*.log | grep -E '(duration constrained|Auto-saving|prompt)'"
