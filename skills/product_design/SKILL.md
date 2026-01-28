# Product Design Skill

## Description
AI-powered product design creation for print-on-demand, including t-shirts, mugs, posters, and lifestyle products with trend analysis and brand consistency.

## Capabilities
- **Design Generation**: Create original designs using AI models
- **Mockup Creation**: Generate realistic product mockups
- **Lifestyle Scenes**: Place products in lifestyle photography
- **Brand Consistency**: Maintain visual identity across designs
- **Trend Integration**: Apply current design trends
- **Format Optimization**: Ensure correct dimensions and DPI

## Tools Required
- `generate_image`
- `generate_tshirt_design`
- `generate_product_mockup`
- `generate_lifestyle_scene`
- `upscale_image`
- `remove_background`
- `replicate_smart_generate`
- `replicate_run_model`
- `search_web` (for trend research)
- `get_trending_topics`

## Workflows

### Complete Design Creation
```yaml
name: Create Product Design from Concept
steps:
  1. Analyze design request and brand guidelines
  2. Research current trends in niche
  3. Generate 3-5 design variations
  4. Select best design based on criteria
  5. Upscale to print quality (300 DPI, 4500x5400px)
  6. Remove background if needed
  7. Create product mockups (t-shirt, mug, etc.)
  8. Generate lifestyle scene
  9. Save all assets with metadata

success_criteria:
  - Design matches brand guidelines
  - Print-ready quality (300 DPI minimum)
  - Multiple mockup angles
  - Lifestyle scene for marketing
```

### Trend-Based Design
```yaml
name: Create Trending Design
steps:
  1. Get trending topics in target niche
  2. Analyze trending visual styles
  3. Generate design incorporating trends
  4. Test on multiple product types
  5. Create variant designs

success_criteria:
  - Aligns with current trends
  - Unique enough to avoid copyright
  - Works on multiple product types
```

### Design Optimization
```yaml
name: Optimize Existing Design
steps:
  1. Analyze current design
  2. Upscale if low resolution
  3. Enhance colors and contrast
  4. Remove artifacts
  5. Create print-ready version
  6. Generate new mockups

success_criteria:
  - Minimum 300 DPI
  - Proper color profile (RGB for digital, CMYK for print)
  - Clean edges and backgrounds
```

## Design Guidelines

### T-Shirt Designs
- **Dimensions**: 4500x5400 pixels (standard print area)
- **DPI**: 300 minimum
- **Color Mode**: RGB
- **Safe Area**: Keep important elements 2 inches from edges
- **File Format**: PNG with transparent background

### Mug Designs
- **Dimensions**: 2475x1155 pixels (11oz mug)
- **DPI**: 300 minimum
- **Wrap Style**: Consider handle placement
- **Color Mode**: RGB

### Poster Designs
- **Dimensions**: Variable by size (18x24" = 5400x7200px at 300 DPI)
- **DPI**: 300 minimum
- **Bleed Area**: Add 0.125" bleed on all sides
- **Safe Zone**: Keep text 0.25" from trim

## Prompting Strategies

### High-Quality Design Prompts
```
For photorealistic: "highly detailed, photorealistic, 8k uhd, professional photography"
For illustrations: "vector art style, clean lines, professional illustration, trending on dribbble"
For minimalist: "minimalist design, clean aesthetic, negative space, modern typography"
For vintage: "retro aesthetic, vintage texture, distressed effect, classic typography"
```

### AI Model Selection
- **Flux Pro**: Best for photorealistic and detailed designs
- **SDXL**: Great for artistic styles and illustrations
- **Midjourney**: Excellent aesthetic quality (via replicate)
- **Stable Diffusion**: Good for specific styles and controlnet

## Error Handling

### Low Resolution Output
- Use upscale_image tool to enhance
- Regenerate with explicit resolution requirements
- Try different AI models

### Inconsistent Style
- Provide detailed style reference
- Use consistent prompting patterns
- Include negative prompts to avoid unwanted elements

### Copyright Concerns
- Avoid specific brand names or characters
- Use "inspired by" rather than direct copies
- Generate original concepts
- Add unique elements to differentiate

## Best Practices
- Always research trends before creating
- Generate multiple variations
- Test designs on actual product mockups
- Maintain a design library for consistency
- Document successful prompts
- Use brand guidelines if provided
- Check print requirements before finalizing
- Save high-res originals
- Create both light and dark background versions

## Dependencies
- Replicate API access
- Image storage system
- Brand guidelines (optional)
- Design trend knowledge base

## Metadata
- **Domain**: creative, ecommerce
- **Complexity**: Medium-High
- **Automation Level**: Semi-Automated
- **Human Verification**: Recommended (aesthetic review)
