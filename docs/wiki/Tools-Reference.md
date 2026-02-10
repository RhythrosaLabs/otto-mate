# Tools Reference

Complete documentation of all 100+ tools available in Otto Chat.

---

## Tool Categories

| Category | Count | Description |
|----------|-------|-------------|
| [Image Generation](#image-generation) | 15+ | AI image creation and editing |
| [Video Generation](#video-generation) | 10+ | AI video creation |
| [Audio Generation](#audio-generation) | 8 | Music, voice, sound effects |
| [Printify](#printify) | 15+ | Print-on-demand |
| [Shopify](#shopify) | 12 | E-commerce |
| [Research](#research) | 8 | Web search and scraping |
| [Browser](#browser) | 8 | Browser automation |
| [Content](#content) | 7 | Text generation |
| [File Storage](#file-storage) | 7 | File management |
| [Plugin Tools](#plugin-tools) | 10+ | From installed plugins |

---

## Image Generation

### generate_image_flux_pro

Generate high-quality images using Flux Pro 1.1.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `prompt` | string | Yes | - | Image generation prompt |
| `aspect_ratio` | string | No | "1:1" | Aspect ratio |
| `num_outputs` | int | No | 1 | Number of images (1-4) |
| `guidance` | float | No | 3.5 | Guidance scale (1-10) |
| `output_format` | string | No | "png" | png, jpg, webp |

**Aspect Ratios:**
- `1:1` (1024×1024) - Square
- `16:9` (1344×768) - Widescreen
- `9:16` (768×1344) - Portrait/Phone
- `4:3` (1152×896) - Standard
- `3:4` (896×1152) - Portrait
- `2:3` (832×1216) - Tall Portrait
- `3:2` (1216×832) - Landscape

**Example:**
```json
{
  "prompt": "A majestic mountain landscape at golden hour, photorealistic",
  "aspect_ratio": "16:9",
  "guidance": 4.0
}
```

---

### generate_image_flux_dev

Fast image generation for prototyping with Flux Dev.

| Parameter | Type | Required | Default |
|-----------|------|----------|---------|
| `prompt` | string | Yes | - |
| `aspect_ratio` | string | No | "1:1" |
| `num_inference_steps` | int | No | 28 |

---

### generate_image_sdxl

Generate images using Stable Diffusion XL.

| Parameter | Type | Required | Default |
|-----------|------|----------|---------|
| `prompt` | string | Yes | - |
| `negative_prompt` | string | No | "" |
| `width` | int | No | 1024 |
| `height` | int | No | 1024 |
| `num_inference_steps` | int | No | 30 |
| `guidance_scale` | float | No | 7.5 |
| `seed` | int | No | random |

---

### generate_image_recraft

Generate logos, icons, and vector-style images with Recraft V3.

| Parameter | Type | Required | Default |
|-----------|------|----------|---------|
| `prompt` | string | Yes | - |
| `style` | string | No | "any" |
| `size` | string | No | "1024x1024" |

**Styles:** `any`, `realistic`, `digital_illustration`, `vector_illustration`, `icon`

**Best for:** Logos, icons, brand assets, clean illustrations

---

### generate_image_ideogram

Generate images with text using Ideogram V2.

| Parameter | Type | Required | Default |
|-----------|------|----------|---------|
| `prompt` | string | Yes | - |
| `aspect_ratio` | string | No | "1:1" |
| `style` | string | No | "auto" |

**Best for:** Images containing readable text, signs, banners

---

### generate_logo

Create professional logos.

| Parameter | Type | Required | Default |
|-----------|------|----------|---------|
| `company_name` | string | Yes | - |
| `style` | string | No | "modern" |
| `colors` | array | No | auto |
| `industry` | string | No | "" |

**Styles:** `modern`, `minimal`, `vintage`, `playful`, `corporate`, `luxury`

---

### upscale_image

Upscale image resolution by 4x.

| Parameter | Type | Required |
|-----------|------|----------|
| `image_url` | string | Yes |
| `scale` | int | No (default: 4) |

---

### remove_background

Remove background from an image.

| Parameter | Type | Required |
|-----------|------|----------|
| `image_url` | string | Yes |

**Returns:** PNG with transparent background

---

### enhance_image

Enhance image quality and details.

| Parameter | Type | Required |
|-----------|------|----------|
| `image_url` | string | Yes |
| `enhancement_type` | string | No |

**Enhancement Types:** `auto`, `face`, `cartoon`, `general`

---

### colorize_image

Add color to black and white images.

| Parameter | Type | Required |
|-----------|------|----------|
| `image_url` | string | Yes |

---

### inpaint_image

Edit parts of an image.

| Parameter | Type | Required |
|-----------|------|----------|
| `image_url` | string | Yes |
| `mask_url` | string | Yes |
| `prompt` | string | Yes |

---

### style_transfer

Apply artistic style to an image.

| Parameter | Type | Required |
|-----------|------|----------|
| `content_image` | string | Yes |
| `style` | string | Yes |

**Styles:** `van_gogh`, `monet`, `picasso`, `anime`, `sketch`, `watercolor`

---

## Video Generation

### generate_ai_video

Generate video from text or image.

| Parameter | Type | Required | Default |
|-----------|------|----------|---------|
| `prompt` | string | Yes* | - |
| `image_url` | string | Yes* | - |
| `model` | string | No | "runway" |
| `duration` | int | No | 5 |

*One of `prompt` or `image_url` required

**Models:** `runway`, `luma`, `minimax`, `kling`

---

### generate_video_runway

Generate video with Runway Gen-3 Alpha.

| Parameter | Type | Required | Default |
|-----------|------|----------|---------|
| `prompt` | string | Yes | - |
| `image_url` | string | No | - |
| `duration` | int | No | 5 |
| `aspect_ratio` | string | No | "16:9" |

---

### generate_video_luma

Generate video with Luma Dream Machine.

| Parameter | Type | Required |
|-----------|------|----------|
| `prompt` | string | Yes |
| `image_url` | string | No |

---

### create_promo_video

Create a professional promotional video.

| Parameter | Type | Required | Default |
|-----------|------|----------|---------|
| `product_name` | string | Yes | - |
| `description` | string | Yes | - |
| `style` | string | No | "cinematic" |
| `duration` | int | No | 30 |

**Styles:** `cinematic`, `commercial`, `luxury`, `dynamic`, `ambient`

---

### assemble_video_with_audio

Combine video with audio/music.

| Parameter | Type | Required |
|-----------|------|----------|
| `video_url` | string | Yes |
| `audio_url` | string | Yes |
| `volume` | float | No (0-1) |

---

### create_full_commercial

End-to-end commercial production.

| Parameter | Type | Required |
|-----------|------|----------|
| `brand_name` | string | Yes |
| `product` | string | Yes |
| `message` | string | Yes |
| `style` | string | No |
| `include_music` | bool | No |

---

## Audio Generation

### generate_music

Generate AI music.

| Parameter | Type | Required | Default |
|-----------|------|----------|---------|
| `prompt` | string | Yes | - |
| `duration` | int | No | 30 |
| `genre` | string | No | "auto" |

**Genres:** `ambient`, `electronic`, `cinematic`, `corporate`, `jazz`, `classical`, `lo-fi`, `hip-hop`

---

### generate_ambient

Generate ambient soundscapes.

| Parameter | Type | Required |
|-----------|------|----------|
| `description` | string | Yes |
| `duration` | int | No |

---

### text_to_speech

Convert text to speech.

| Parameter | Type | Required | Default |
|-----------|------|----------|---------|
| `text` | string | Yes | - |
| `voice` | string | No | "alloy" |
| `speed` | float | No | 1.0 |

**Voices:** `alloy`, `echo`, `fable`, `onyx`, `nova`, `shimmer`

---

### generate_voiceover

Create professional voiceover narration.

| Parameter | Type | Required |
|-----------|------|----------|
| `script` | string | Yes |
| `voice_style` | string | No |
| `emotion` | string | No |

---

## Printify

### get_printify_shops

List all connected Printify shops.

| Parameter | Type | Required |
|-----------|------|----------|
| (none) | - | - |

---

### get_printify_products

Get products from a shop.

| Parameter | Type | Required | Default |
|-----------|------|----------|---------|
| `shop_id` | string | No | default shop |
| `page` | int | No | 1 |
| `limit` | int | No | 20 |

---

### get_blueprints

Get available product templates.

| Parameter | Type | Required |
|-----------|------|----------|
| `category` | string | No |

**Categories:** `apparel`, `drinkware`, `wall_art`, `accessories`, `home`

---

### upload_printify_image

Upload design image to Printify.

| Parameter | Type | Required |
|-----------|------|----------|
| `image_url` | string | Yes |
| `filename` | string | No |

---

### create_printify_product

Create a new product.

| Parameter | Type | Required |
|-----------|------|----------|
| `title` | string | Yes |
| `description` | string | Yes |
| `blueprint_id` | int | Yes |
| `image_id` | string | Yes |
| `variants` | array | No |

---

### publish_printify_product

Publish product to sales channels.

| Parameter | Type | Required |
|-----------|------|----------|
| `product_id` | string | Yes |
| `title` | bool | No |
| `description` | bool | No |
| `images` | bool | No |

---

### smart_create_product

AI-powered product creation.

| Parameter | Type | Required |
|-----------|------|----------|
| `product_type` | string | Yes |
| `design_prompt` | string | Yes |
| `title` | string | No |

**Product Types:** `t-shirt`, `hoodie`, `mug`, `poster`, `canvas`, `framed_art`, `phone_case`, `tote_bag`

---

## Shopify

### get_shopify_products

List store products.

| Parameter | Type | Required | Default |
|-----------|------|----------|---------|
| `limit` | int | No | 50 |
| `status` | string | No | "active" |

---

### create_shopify_product

Create a new product.

| Parameter | Type | Required |
|-----------|------|----------|
| `title` | string | Yes |
| `body_html` | string | Yes |
| `vendor` | string | No |
| `product_type` | string | No |
| `variants` | array | Yes |

---

### update_shopify_product

Update existing product.

| Parameter | Type | Required |
|-----------|------|----------|
| `product_id` | string | Yes |
| `updates` | object | Yes |

---

### get_shopify_orders

Get store orders.

| Parameter | Type | Required | Default |
|-----------|------|----------|---------|
| `status` | string | No | "any" |
| `limit` | int | No | 50 |

---

### get_shopify_customers

List customers.

| Parameter | Type | Required |
|-----------|------|----------|
| `limit` | int | No |
| `email` | string | No |

---

### update_shopify_inventory

Update inventory levels.

| Parameter | Type | Required |
|-----------|------|----------|
| `inventory_item_id` | string | Yes |
| `available` | int | Yes |

---

## Research

### web_search

Search the web via Google.

| Parameter | Type | Required | Default |
|-----------|------|----------|---------|
| `query` | string | Yes | - |
| `num_results` | int | No | 10 |

---

### search_news

Search news articles.

| Parameter | Type | Required |
|-----------|------|----------|
| `query` | string | Yes |
| `time_range` | string | No |

**Time Ranges:** `hour`, `day`, `week`, `month`, `year`

---

### search_images

Search for images.

| Parameter | Type | Required |
|-----------|------|----------|
| `query` | string | Yes |
| `num_results` | int | No |

---

### scrape_webpage

Extract content from a webpage.

| Parameter | Type | Required |
|-----------|------|----------|
| `url` | string | Yes |
| `selector` | string | No |

---

### scrape_structured

Extract structured data (JSON-LD, microdata).

| Parameter | Type | Required |
|-----------|------|----------|
| `url` | string | Yes |

---

### get_page_links

Extract all links from a page.

| Parameter | Type | Required |
|-----------|------|----------|
| `url` | string | Yes |
| `internal_only` | bool | No |

---

### summarize_url

Summarize webpage content.

| Parameter | Type | Required |
|-----------|------|----------|
| `url` | string | Yes |
| `max_length` | int | No |

---

## Browser

### browser_navigate

Open a URL in browser.

| Parameter | Type | Required |
|-----------|------|----------|
| `url` | string | Yes |
| `wait_for` | string | No |

---

### browser_screenshot

Capture page screenshot.

| Parameter | Type | Required |
|-----------|------|----------|
| `full_page` | bool | No |

---

### browser_click

Click an element.

| Parameter | Type | Required |
|-----------|------|----------|
| `selector` | string | Yes |

---

### browser_type

Enter text in a field.

| Parameter | Type | Required |
|-----------|------|----------|
| `selector` | string | Yes |
| `text` | string | Yes |

---

### browser_scroll

Scroll the page.

| Parameter | Type | Required |
|-----------|------|----------|
| `direction` | string | Yes |
| `amount` | int | No |

---

### browser_extract

Extract data from page.

| Parameter | Type | Required |
|-----------|------|----------|
| `selector` | string | Yes |
| `attribute` | string | No |

---

## Content

### generate_blog_post

Generate a blog article.

| Parameter | Type | Required | Default |
|-----------|------|----------|---------|
| `topic` | string | Yes | - |
| `length` | string | No | "medium" |
| `tone` | string | No | "professional" |
| `keywords` | array | No | [] |

**Lengths:** `short` (300 words), `medium` (800 words), `long` (1500+ words)

---

### generate_product_description

Create e-commerce product copy.

| Parameter | Type | Required |
|-----------|------|----------|
| `product_name` | string | Yes |
| `features` | array | Yes |
| `target_audience` | string | No |

---

### generate_social_post

Create social media content.

| Parameter | Type | Required |
|-----------|------|----------|
| `topic` | string | Yes |
| `platform` | string | No |
| `include_hashtags` | bool | No |

---

### generate_email

Draft an email.

| Parameter | Type | Required |
|-----------|------|----------|
| `purpose` | string | Yes |
| `recipient_type` | string | No |
| `tone` | string | No |

---

### summarize_text

Summarize long text.

| Parameter | Type | Required |
|-----------|------|----------|
| `text` | string | Yes |
| `max_length` | int | No |
| `style` | string | No |

---

### rewrite_text

Rewrite content in different style.

| Parameter | Type | Required |
|-----------|------|----------|
| `text` | string | Yes |
| `target_style` | string | Yes |

---

### generate_ideas

Brainstorm ideas.

| Parameter | Type | Required |
|-----------|------|----------|
| `topic` | string | Yes |
| `num_ideas` | int | No |
| `constraints` | array | No |

---

## File Storage

### save_file

Store a file with metadata.

| Parameter | Type | Required |
|-----------|------|----------|
| `content` | string/bytes | Yes |
| `filename` | string | Yes |
| `category` | string | No |
| `metadata` | object | No |

---

### save_image_from_url

Download and save an image.

| Parameter | Type | Required |
|-----------|------|----------|
| `url` | string | Yes |
| `filename` | string | No |

---

### save_generated_image

Save AI-generated image.

| Parameter | Type | Required |
|-----------|------|----------|
| `url` | string | Yes |
| `prompt` | string | No |
| `model` | string | No |

---

### get_file

Retrieve file by ID.

| Parameter | Type | Required |
|-----------|------|----------|
| `file_id` | string | Yes |

---

### list_files

Browse files.

| Parameter | Type | Required |
|-----------|------|----------|
| `category` | string | No |
| `limit` | int | No |

---

### delete_file

Remove a file.

| Parameter | Type | Required |
|-----------|------|----------|
| `file_id` | string | Yes |

---

### get_storage_stats

Get storage statistics.

| Parameter | Type | Required |
|-----------|------|----------|
| (none) | - | - |

---

## Plugin Tools

Tools provided by installed plugins. See [[Plugin Development]] for creating custom tools.

### web_scraper Plugin

| Tool | Description |
|------|-------------|
| `scrape_page` | Advanced web scraping |
| `extract_links` | Get all page links |
| `extract_tables` | Extract tables as JSON |
| `search_page` | Search within page content |

### notification_sender Plugin

| Tool | Description |
|------|-------------|
| `send_email` | Send email notifications |
| `send_slack` | Post to Slack |
| `send_discord` | Post to Discord |
| `send_webhook` | Generic webhook POST |

### database_connector Plugin

| Tool | Description |
|------|-------------|
| `query_database` | Execute SQL queries |
| `list_tables` | List database tables |
| `describe_table` | Get table schema |
| `insert_data` | Insert records |
