# Video Production Skill

**Skill ID**: `video_production`  
**Version**: 1.0  
**Category**: AI Video & Marketing

## Description

Complete video production pipeline for product marketing and promotional content. Creates professional video ads from static images with AI-generated motion, voiceover, and background music.

## Capabilities

### Video Generation
- Image-to-video animation using Kling, Minimax, or SVD models
- Ken Burns effects for static images
- Product showcase with subtle motion
- CTA card overlays

### Audio Production
- AI voiceover generation with emotion control
- Background music generation via MusicGen
- Audio mixing with proper volume balancing
- Voice + music composition

### Printify Integration
- Automatic mockup fetching from Printify products
- Uses real product images as video source
- Seamless product-to-video workflow

### Complete Promo Videos
- Script generation with Claude
- Voice synthesis with Bark TTS
- Video generation from mockups
- Background music generation
- Final composition with MoviePy

## Tools

### `create_product_promo_video`
Create a complete promotional video with all elements.

**Parameters:**
- `product_name` (required): Name of the product
- `product_description`: Description for script generation
- `image_url`: Direct image URL for the video
- `printify_product_id`: Printify product ID to fetch mockup from
- `duration`: Video duration in seconds (default: 10)
- `include_voiceover`: Add AI voiceover (default: true)
- `include_music`: Add background music (default: true)
- `tone`: Script tone - energetic, calm, professional, fun
- `music_style`: Music style description

### `generate_video_from_mockup`
Generate a simple video from a static image.

**Parameters:**
- `image_url` (required): URL of the source image
- `prompt` (required): Motion/action description
- `duration`: Video duration (5 or 10 seconds)
- `model`: Video model - kling, minimax, svd

### `printify_get_mockup_urls`
Fetch mockup images from a Printify product.

**Parameters:**
- `product_id` (required): Printify product ID

**Returns:** List of mockup URLs with position info

## Workflows

### Complete Product Video Ad
```
User: "Create a design, sell it as a mug, and make a video ad"

Workflow:
1. generate_image → Creates the design
2. printify_create_mug → Creates product on Printify
3. printify_get_mockup_urls → Fetches mockup images
4. create_product_promo_video → Creates video from mockup
   - Generates script
   - Creates voiceover
   - Generates video from mockup
   - Creates background music
   - Composes final video
```

### Quick Product Animation
```
User: "Animate my product image for Instagram"

Workflow:
1. generate_video_from_mockup → Creates animated video
   - Uses Kling for high quality
   - 5-10 second duration
   - Smooth product motion
```

### Printify Product to Video
```
User: "Create a video ad for product 1234567890"

Workflow:
1. printify_get_mockup_urls → Gets mockup from Printify
2. create_product_promo_video → Creates full promo video
   - Uses default mockup image
   - Generates branded script
   - Adds voiceover + music
```

## Video Models

### Kling (Default)
- Model: `kwaivgi/kling-v1.6-pro`
- Best for: Product showcases, smooth motion
- Duration: 5-10 seconds
- Quality: High

### Minimax
- Model: `minimax/video-01`
- Best for: Complex scenes, longer videos
- Duration: Up to 30 seconds
- Quality: Very high

### Stable Video Diffusion
- Model: `stability-ai/stable-video-diffusion`
- Best for: Subtle animation, product rotation
- Duration: Short clips
- Quality: Good for static subjects

## Audio Models

### Voiceover (Bark)
- Model: `cjwbw/bark`
- Features: Emotional speech, multiple voices
- Best for: Ad narration, product descriptions

### Background Music (MusicGen)
- Model: `meta/musicgen`
- Features: Style control, duration matching
- Best for: Commercial music, ad jingles

## Output Formats

- **Video**: MP4 (H.264 codec)
- **Audio**: MP3 for standalone, AAC in video
- **Resolution**: Matches input image
- **Frame rate**: 24 FPS

## Best Practices

1. **Image Quality**: Use high-resolution mockup images for best video quality
2. **Prompts**: Be specific about desired motion ("gentle rotation", "slow zoom")
3. **Duration**: 10-15 seconds is ideal for social media ads
4. **Music**: Match music energy to product personality
5. **Voiceover**: Keep scripts punchy and benefit-focused

## Dependencies

- `replicate_universal`: For AI video/audio generation
- `printify`: For mockup fetching (optional)
- `moviepy`: For final video composition
- `aiohttp`: For async file downloads

## Configuration

Required environment variables:
- `REPLICATE_API_TOKEN`: For video/audio generation
- `ANTHROPIC_API_KEY`: For script generation
- `PRINTIFY_API_KEY`: For mockup fetching (optional)
- `PRINTIFY_SHOP_ID`: For Printify integration (optional)

## Performance Metrics

- Video generation: 30-60 seconds
- Voiceover: 10-20 seconds
- Music: 20-40 seconds
- Full promo (parallel): 60-90 seconds total

## Version History

- v1.0 (2026-01-29): Initial video production skill
  - Image-to-video with Kling/Minimax
  - Voiceover with Bark
  - Music with MusicGen
  - Printify mockup integration
  - Full promo video composition
