#!/bin/bash

# Test UI Markdown Rendering and Printify Improvements
# Created: 2026-01-29

API_URL="http://localhost:8000/chat"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="test_outputs/ui_printify_test_${TIMESTAMP}"

mkdir -p "$OUTPUT_DIR"

echo "================================"
echo "🧪 Testing UI & Printify Fixes"
echo "================================"
echo ""

# Test 1: Markdown Rendering
echo "[1/3] Testing Markdown UI Rendering..."
response=$(curl -s -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Explain the features of a modern AI assistant using:\n\n## Headers\n- **Bold** lists\n- *Italic* emphasis\n- `code` snippets\n\nMake it well-formatted!",
    "thread_id": "test-markdown-'$TIMESTAMP'"
  }')

echo "$response" > "$OUTPUT_DIR/markdown_test.json"
markdown_response=$(echo "$response" | jq -r '.response')
echo "$markdown_response" > "$OUTPUT_DIR/markdown_test.txt"

# Check for markdown elements in response
if echo "$markdown_response" | grep -q "##\|**\|*\|##"; then
    echo "✅ SUCCESS - Response contains markdown formatting"
    echo "   Length: $(echo "$markdown_response" | wc -c) chars"
else
    echo "❌ FAILED - No markdown detected"
fi

echo ""

# Test 2: Printify Product Creation (Canvas)
echo "[2/3] Testing Printify Canvas Creation..."
response=$(curl -s -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Design a minimalist mountain landscape and publish it on Printify as a canvas print (16x20 inches)",
    "thread_id": "test-printify-canvas-'$TIMESTAMP'"
  }')

echo "$response" > "$OUTPUT_DIR/printify_canvas_test.json"
printify_response=$(echo "$response" | jq -r '.response')
echo "$printify_response" > "$OUTPUT_DIR/printify_canvas_test.txt"

# Check for success indicators
if echo "$printify_response" | grep -qi "successfully\|published\|created"; then
    echo "✅ SUCCESS - Printify product creation attempted"
    echo "   Response: $(echo "$printify_response" | head -c 200)..."
elif echo "$printify_response" | grep -qi "uploaded\|image id"; then
    echo "⚠️  PARTIAL - Image uploaded, product creation may have issues"
    echo "   Response: $(echo "$printify_response" | head -c 200)..."
else
    echo "❌ FAILED - Printify creation failed"
    echo "   Response: $(echo "$printify_response" | head -c 200)..."
fi

echo ""

# Test 3: Complex Markdown Response
echo "[3/3] Testing Complex Markdown with Lists and Code..."
response=$(curl -s -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Create a markdown guide showing:\n1. Numbered lists\n2. Bullet points with **bold** and *italic*\n3. Code blocks with \`\`\`python\nprint('hello')\n\`\`\`\n4. Headers H1, H2, H3",
    "thread_id": "test-complex-markdown-'$TIMESTAMP'"
  }')

echo "$response" > "$OUTPUT_DIR/complex_markdown_test.json"
complex_response=$(echo "$response" | jq -r '.response')
echo "$complex_response" > "$OUTPUT_DIR/complex_markdown_test.txt"

# Check for various markdown elements
has_headers=$(echo "$complex_response" | grep -c "^#" || echo 0)
has_lists=$(echo "$complex_response" | grep -c "^\* \|^- \|^[0-9]\." || echo 0)
has_code=$(echo "$complex_response" | grep -c "\`\`\`\|\`" || echo 0)

if [ "$has_headers" -gt 0 ] && [ "$has_lists" -gt 0 ]; then
    echo "✅ SUCCESS - Complex markdown generated"
    echo "   Headers: $has_headers, Lists: $has_lists, Code: $has_code"
else
    echo "⚠️  PARTIAL - Some markdown elements missing"
    echo "   Headers: $has_headers, Lists: $has_lists, Code: $has_code"
fi

echo ""
echo "================================"
echo "📊 Test Summary"
echo "================================"
echo "Output saved to: $OUTPUT_DIR"
echo ""
echo "To view results:"
echo "  cat $OUTPUT_DIR/markdown_test.txt"
echo "  cat $OUTPUT_DIR/printify_canvas_test.txt"
echo "  cat $OUTPUT_DIR/complex_markdown_test.txt"
echo ""
echo "To test UI rendering, open:"
echo "  http://localhost:8000"
echo ""
