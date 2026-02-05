#!/bin/bash

# Quick parameter fix validation tests

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="test_outputs/fix_validation_${TIMESTAMP}"
API_URL="http://localhost:8000/chat"

mkdir -p "$OUTPUT_DIR"

echo "🔧 Parameter Fix Validation Tests"
echo "===================================="
echo ""

# Test 1: Competitor analysis with 'competitor' parameter
echo "[1/5] Testing analyze_competitor with 'competitor' parameter"
curl -s -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{"message": "Analyze Patagonia as a competitor in sustainable fashion", "thread_id": "test_competitor_param"}' \
  | tee "$OUTPUT_DIR/competitor_test.json" \
  | jq -r '"Status: " + (if .response then "✅ SUCCESS" else "❌ FAILED" end)'

echo ""
sleep 2

# Test 2: Product mockup with 'prompt' parameter  
echo "[2/5] Testing generate_product_mockup with full prompt"
curl -s -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{"message": "Create mockup: coffee mug with mountain logo on rustic wooden table, morning sunlight", "thread_id": "test_mockup_prompt"}' \
  | tee "$OUTPUT_DIR/mockup_test.json" \
  | jq -r '"Status: " + (if .response then "✅ SUCCESS" else "❌ FAILED" end)'

echo ""
sleep 2

# Test 3: Video with string duration
echo "[3/5] Testing video generation with string duration"
curl -s -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{"message": "Generate a 15 second product video showcasing a coffee mug", "thread_id": "test_video_duration_str"}' \
  | tee "$OUTPUT_DIR/video_test.json" \
  | jq -r '"Status: " + (if .response then "✅ SUCCESS" else "❌ FAILED" end)'

echo ""
sleep 2

# Test 4: Shopify product with aliases
echo "[4/5] Testing Shopify product with parameter aliases"
curl -s -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{"message": "Create a Shopify product with product_title Mountain Mug and product_description Beautiful mountain design", "thread_id": "test_shopify_aliases"}' \
  | tee "$OUTPUT_DIR/shopify_test.json" \
  | jq -r '"Status: " + (if .response then "✅ SUCCESS" else "❌ FAILED" end)'

echo ""
sleep 2

# Test 5: Combined workflow (the original husky mug failure)
echo "[5/5] Testing complete workflow: design + mockup + video"
curl -s -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{"message": "Create a husky design, generate a product mockup of it on a mug, and create a 15 second promotional video", "thread_id": "test_combined_workflow"}' \
  | tee "$OUTPUT_DIR/combined_test.json" \
  | jq -r '"Status: " + (if .response then "✅ SUCCESS" else "❌ FAILED" end), "Response length: " + (.response | length | tostring) + " chars"'

echo ""
echo "===================================="
echo "✅ Validation Complete!"
echo "Results saved to: $OUTPUT_DIR"
echo ""
echo "Check for errors:"
echo "  tail -50 logs/*.log | grep -E 'ERROR|unexpected keyword'"
