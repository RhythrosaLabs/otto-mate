#!/bin/bash

# Otto Universal - Complex Workflow Test Suite
# Tests various autonomous capabilities

echo "🚀 Otto Universal - Autonomous Workflow Tests"
echo "=============================================="
echo ""

API_URL="http://localhost:8000/chat"

# Test 1: Multi-Product Creation
echo "[1/5] Test: Multi-Product Creation"
echo "Request: Create coffee mug designs and publish them"
curl -s -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Create 2 coffee-themed designs and make mugs for both on Printify",
    "thread_id": "test-multi-product"
  }' | jq -r '
    "✅ Status: " + (if .response then "SUCCESS" else "PENDING" end),
    "   Steps: " + (.steps_executed | length | tostring),
    "   Response length: " + (.response | length | tostring) + " chars"
  ' 2>/dev/null

echo ""
sleep 2

# Test 2: Content Generation
echo "[2/5] Test: Content Marketing"
echo "Request: Blog post with SEO"
curl -s -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Write a blog post about sustainable packaging trends and optimize for SEO",
    "thread_id": "test-content"
  }' | jq -r '
    "✅ Status: " + (if .response then "SUCCESS" else "PENDING" end),
    "   Steps: " + (.steps_executed | length | tostring)
  ' 2>/dev/null

echo ""
sleep 2

# Test 3: Design + Social Media
echo "[3/5] Test: Product with Marketing"  
echo "Request: Design product and create promotion"
curl -s -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Create a geometric t-shirt design and generate 3 Instagram captions for it",
    "thread_id": "test-design-social"
  }' | jq -r '
    "✅ Status: " + (if .response then "SUCCESS" else "PENDING" end),
    "   Steps: " + (.steps_executed | length | tostring)
  ' 2>/dev/null

echo ""
sleep 2

# Test 4: Research Workflow
echo "[4/5] Test: Market Research"
echo "Request: Research and design"
curl -s -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Research streetwear trends and create a design inspired by the findings",
    "thread_id": "test-research"
  }' | jq -r '
    "✅ Status: " + (if .response then "SUCCESS" else "PENDING" end),
    "   Steps: " + (.steps_executed | length | tostring)
  ' 2>/dev/null

echo ""
sleep 2

# Test 5: Complete Campaign
echo "[5/5] Test: Full Product Launch"
echo "Request: End-to-end campaign"
curl -s -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Create a nature design, make a mug on Printify, publish it, and write a blog post about it",
    "thread_id": "test-full-campaign"
  }' | jq -r '
    "✅ Status: " + (if .response then "SUCCESS" else "PENDING" end),
    "   Steps: " + (.steps_executed | length | tostring),
    "   Artifacts: " + (.artifacts | length | tostring)
  ' 2>/dev/null

echo ""
echo "=============================================="
echo "✨ Test suite complete!"
