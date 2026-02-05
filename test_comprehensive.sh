#!/bin/bash

# Otto Universal - Comprehensive Test Suite with Output Saving
# Tests complex autonomous workflows and saves all artifacts

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="test_outputs/${TIMESTAMP}"
API_URL="http://localhost:8000/chat"

# Create timestamped output directory
mkdir -p "$OUTPUT_DIR"/{images,videos,text,products,logs}

echo "🚀 Otto Universal - Comprehensive Autonomous Tests"
echo "===================================================="
echo "Output Directory: $OUTPUT_DIR"
echo ""

# Function to save and display results
test_workflow() {
    local test_num=$1
    local test_name=$2
    local message=$3
    local thread_id=$4
    
    echo "[$test_num] $test_name"
    echo "─────────────────────────────────────────────────────────"
    echo "Request: ${message:0:80}..."
    
    # Make request and save full response
    response=$(curl -s -X POST "$API_URL" \
        -H "Content-Type: application/json" \
        -d "{\"message\": \"$message\", \"thread_id\": \"$thread_id\"}")
    
    # Save full JSON response
    echo "$response" > "$OUTPUT_DIR/logs/${thread_id}_response.json"
    
    # Extract and display summary
    if echo "$response" | jq -e '.response' > /dev/null 2>&1; then
        echo "✅ SUCCESS"
        
        # Save response text
        echo "$response" | jq -r '.response' > "$OUTPUT_DIR/text/${thread_id}_response.txt"
        
        # Count steps and artifacts
        steps=$(echo "$response" | jq '.steps_executed | length' 2>/dev/null || echo "0")
        artifacts=$(echo "$response" | jq '.artifacts | length' 2>/dev/null || echo "0")
        response_len=$(echo "$response" | jq -r '.response | length' 2>/dev/null || echo "0")
        
        echo "   Response: $response_len chars"
        echo "   Steps: $steps"
        echo "   Artifacts: $artifacts"
        
        # Extract artifact URLs if present
        if [ "$artifacts" -gt 0 ]; then
            echo "$response" | jq -r '.artifacts[] | "\(.type): \(.url // .name)"' 2>/dev/null | head -3 | while read line; do
                echo "   • $line"
            done
        fi
    else
        echo "❌ FAILED"
        echo "$response" | jq -r '.error // .message // "Unknown error"' 2>/dev/null
    fi
    
    echo ""
}

# Test Suite
echo "Starting test suite at $(date)"
echo ""

# Test 1: Design Generation
test_workflow \
    "1/10" \
    "🎨 AI Design Generation" \
    "Create a vibrant abstract design with neon colors and geometric patterns suitable for t-shirts" \
    "test_design_generation"

sleep 2

# Test 2: Product Creation
test_workflow \
    "2/10" \
    "🛍️ Multi-Product Creation" \
    "Create a coffee-themed design and make both a t-shirt and mug on Printify with it, then publish both" \
    "test_multi_product"

sleep 2

# Test 3: Content Marketing
test_workflow \
    "3/10" \
    "📝 Blog Post + SEO" \
    "Research sustainable fashion trends and write an SEO-optimized blog post about eco-friendly materials. Include trending keywords and publish to Shopify" \
    "test_blog_seo"

sleep 2

# Test 4: Video Generation
test_workflow \
    "4/10" \
    "🎥 Video Content" \
    "Generate a 10 second promotional video showing a sunset over mountains with inspirational text overlay" \
    "test_video_gen"

sleep 2

# Test 5: Product Mockup
test_workflow \
    "5/10" \
    "🖼️ Product Mockup" \
    "Create a product mockup of a white coffee mug with a minimalist mountain design on a wooden desk with morning coffee setup" \
    "test_mockup"

sleep 2

# Test 6: Social Media Campaign
test_workflow \
    "6/10" \
    "📱 Social Media Marketing" \
    "Generate 5 Instagram post captions for promoting a new eco-friendly product line. Include relevant hashtags and engaging CTAs" \
    "test_social_media"

sleep 2

# Test 7: Market Research
test_workflow \
    "7/10" \
    "🔍 Market Research + Design" \
    "Research current streetwear trends, then create a design inspired by the findings and generate a compelling product description" \
    "test_market_research"

sleep 2

# Test 8: Email Campaign
test_workflow \
    "8/10" \
    "📧 Email Marketing" \
    "Create a 5-email drip campaign for launching a new product. Include welcome email, value proposition, social proof, urgency, and closing emails" \
    "test_email_campaign"

sleep 2

# Test 9: Complete Product Launch
test_workflow \
    "9/10" \
    "🚀 Full Product Launch" \
    "Create a nature-inspired design, make a mug on Printify, publish it, write a blog post about the design story, and generate 3 social media posts to promote it" \
    "test_full_launch"

sleep 2

# Test 10: Competitive Analysis
test_workflow \
    "10/10" \
    "📊 Competitive Analysis" \
    "Research top sustainable fashion brands, analyze their strategies, and generate a report with 3 actionable insights for improving product positioning" \
    "test_competitive_analysis"

echo ""
echo "===================================================="
echo "✨ Test Suite Complete!"
echo ""
echo "📁 Results saved to: $OUTPUT_DIR"
echo ""
echo "Summary:"
ls -lh "$OUTPUT_DIR/logs" | grep -c "_response.json" | xargs -I {} echo "   • {} test responses saved"
echo "   • Text outputs: $OUTPUT_DIR/text/"
echo "   • Full logs: $OUTPUT_DIR/logs/"
echo ""
echo "To view results:"
echo "   cat $OUTPUT_DIR/text/*.txt"
echo "   jq . $OUTPUT_DIR/logs/*.json"
echo ""
echo "To check for errors:"
echo "   grep -r ERROR logs/*.log | tail -20"
