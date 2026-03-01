# Tools Reference

Complete reference for all tools available in Otto Chat. Tools are organized by category and registered dynamically via the Tool Registry.

---

## Image Generation

### `generate_image`
Generate an AI image using the best available model.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `prompt` | string | — | Image description |
| `model` | string | `flux-pro` | Model to use |
| `aspect_ratio` | string | `1:1` | Aspect ratio (1:1, 2:3, 3:2, 16:9, 9:16) |
| `style` | string | — | Style preset (photorealistic, artistic, cinematic) |
| `width` | int | — | Custom width in pixels |
| `height` | int | — | Custom height in pixels |

**Available Models:**

| Model Key | Model ID | Best For |
|-----------|----------|----------|
| `flux-pro` | `black-forest-labs/flux-1.1-pro` | Highest quality, photorealistic |
| `flux-dev` | `black-forest-labs/flux-dev` | Fast iteration |
| `sdxl` | `stability-ai/sdxl` | Versatile, wide style range |
| `recraft` | `recraft-ai/recraft-v3` | Logos, icons, vector art |
| `ideogram` | `ideogram-ai/ideogram-v2` | Text in images |

### `generate_tshirt_design`
Generate a design optimized for t-shirt printing (square, high-contrast).

### `generate_product_mockup`
Generate a product mockup image.

### `generate_lifestyle_scene`
Generate a lifestyle/environmental scene.

### `remove_background`
Remove the background from an image.

| Parameter | Type | Description |
|-----------|------|-------------|
| `image_url` | string | URL of the image |

### `upscale_image`
Upscale an image using AI super-resolution.

| Parameter | Type | Description |
|-----------|------|-------------|
| `image_url` | string | URL of the image |
| `scale` | int | Scale factor (2, 4) |

### `add_text_overlay`
Add text overlay to an image.

### `adjust_image`
Apply adjustments (brightness, contrast, saturation, etc.).

### `edit_image_with_ai`
Edit an existing image with AI-powered instructions.

---

## Video Generation

### `generate_ai_video`
Generate a video using the best available model.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `prompt` | string | — | Video description |
| `model` | string | auto-select | Video model |
| `duration` | int | 5 | Duration in seconds |
| `style` | string | — | Style preset |

**Style Presets:**
- `cinematic` — Cinematic film look with dramatic lighting
- `commercial` — Clean, professional product video
- `luxury` — Premium, elegant aesthetic
- `dynamic` — Fast-paced, energetic
- `ambient` — Slow, atmospheric, mood-setting

### `create_promo_video`
Create a commercial-quality promotional video with script generation.

| Parameter | Type | Description |
|-----------|------|-------------|
| `product_name` | string | Product/brand name |
| `style` | string | Cinematic style preset |
| `scenes` | int | Number of scenes |

---

## Audio

### `generate_music`
Generate AI music.

| Parameter | Type | Description |
|-----------|------|-------------|
| `prompt` | string | Music description |
| `duration` | int | Duration in seconds |
| `genre` | string | Music genre |

### `generate_ambient`
Generate ambient/atmospheric audio.

### `text_to_speech`
Convert text to speech.

| Parameter | Type | Description |
|-----------|------|-------------|
| `text` | string | Text to speak |
| `voice` | string | Voice ID |

---

## E-Commerce — Printify

### `get_printify_shops`
List all connected Printify shops.

### `get_printify_products`
List products from a shop.

| Parameter | Type | Description |
|-----------|------|-------------|
| `shop_id` | string | Shop ID (optional, uses default) |
| `page` | int | Page number |

### `create_printify_product`
Create a new product on Printify.

| Parameter | Type | Description |
|-----------|------|-------------|
| `title` | string | Product title |
| `description` | string | Product description |
| `blueprint_id` | int | Product template ID |
| `image_url` | string | Design image URL |
| `variants` | array | Variant configuration |

### `upload_printify_image`
Upload a design image to Printify.

| Parameter | Type | Description |
|-----------|------|-------------|
| `image_url` | string | Image URL to upload |
| `filename` | string | Filename |

### `publish_printify_product`
Publish a product to sales channels.

| Parameter | Type | Description |
|-----------|------|-------------|
| `product_id` | string | Printify product ID |

### `get_blueprints`
Browse available product blueprints (templates).

**Common Blueprints:** T-shirts, hoodies, mugs, posters, framed prints, phone cases, tote bags, canvas prints, pillows, blankets, stickers.

---

## E-Commerce — Shopify

### `get_shopify_products`
List store products.

### `create_shopify_product`
Create a new Shopify product.

| Parameter | Type | Description |
|-----------|------|-------------|
| `title` | string | Product title |
| `description` | string | HTML description |
| `price` | string | Price |
| `images` | array | Image URLs |
| `variants` | array | Variant options |

### `get_shopify_orders`
View orders.

### `get_shopify_customers`
List customers.

### `update_shopify_inventory`
Adjust inventory levels.

---

## Research

### `search_web`
Google search via Serper API.

| Parameter | Type | Description |
|-----------|------|-------------|
| `query` | string | Search query |
| `num_results` | int | Number of results (default: 10) |

### `research_topic`
Deep multi-source research on a topic.

| Parameter | Type | Description |
|-----------|------|-------------|
| `topic` | string | Research topic |
| `depth` | string | Research depth (quick, standard, deep) |

### `browse_url`
Navigate to a URL and extract content.

| Parameter | Type | Description |
|-----------|------|-------------|
| `url` | string | URL to browse |
| `extract` | string | What to extract (text, links, images) |

### `analyze_competitor`
Analyze a competitor's online presence.

| Parameter | Type | Description |
|-----------|------|-------------|
| `url` | string | Competitor URL |

### `get_trending_topics`
Get currently trending topics.

### `search_images`
Search for images online.

---

## Browser Automation

### `browser_navigate`
Open a URL in the headless browser.

### `browser_screenshot`
Capture a screenshot of the current page.

### `browser_click`
Click an element on the page.

| Parameter | Type | Description |
|-----------|------|-------------|
| `selector` | string | CSS selector |

### `browser_type`
Type text into a form field.

| Parameter | Type | Description |
|-----------|------|-------------|
| `selector` | string | CSS selector |
| `text` | string | Text to type |

### `browser_scroll`
Scroll the page.

### `browser_extract`
Extract structured data from the page.

### `browser_execute_script`
Run JavaScript on the page.

### `browser_wait`
Wait for an element to appear.

### `browser_close`
Close the browser.

---

## Content Generation

### `generate_blog_post`
Generate an AI-written blog post.

| Parameter | Type | Description |
|-----------|------|-------------|
| `topic` | string | Blog topic |
| `tone` | string | Writing tone |
| `length` | string | Short, medium, long |
| `keywords` | array | SEO keywords |

### `generate_product_description`
Generate e-commerce product copy.

### `generate_social_media_posts`
Generate social media content for multiple platforms.

| Parameter | Type | Description |
|-----------|------|-------------|
| `topic` | string | Post topic |
| `platforms` | array | Target platforms |
| `tone` | string | Brand voice |

### `generate_email_campaign`
Generate email marketing content.

### `generate_seo_content`
Generate SEO-optimized content.

### `generate_ad_copy`
Generate advertising copy.

### `improve_text`
Enhance existing text content.

---

## Code & File Operations

### `ai_file_editor`
AI-powered file editing operations.

**Operations:** `edit`, `review`, `refactor`, `fix`, `explain`

### `code_execution`
Execute code in a sandboxed environment.

| Parameter | Type | Description |
|-----------|------|-------------|
| `code` | string | Code to execute |
| `language` | string | Programming language |

### `codebase_awareness`
Analyze and understand codebase structure.

### `save_file`
Store a file with metadata.

### `get_file`
Retrieve a file by ID.

### `list_files`
Browse files by category.

### `save_image_from_url`
Download and save an image from a URL.

---

## Task & Scheduling

### `task_queue` (multiple operations)
Manage the persistent task queue.

**Operations:** `create`, `list`, `get`, `cancel`, `update_priority`

### `scheduler`
APScheduler-based task scheduling.

**Operations:** `add_job`, `remove_job`, `list_jobs`, `pause_job`, `resume_job`

---

## Social Media

### `social_poster`
Post content to social media platforms.

| Parameter | Type | Description |
|-----------|------|-------------|
| `content` | string | Post content |
| `platform` | string | Target platform |
| `images` | array | Attached images |

### `social_media_ads`
Create social media advertisements.

---

## Email

### `email_marketing`
Send marketing emails.

| Parameter | Type | Description |
|-----------|------|-------------|
| `to` | string/array | Recipient(s) |
| `subject` | string | Email subject |
| `body` | string | Email body (HTML) |
| `provider` | string | sendgrid or smtp |

---

## Advanced

### `model_chaining`
Chain multiple AI models in a pipeline.

| Parameter | Type | Description |
|-----------|------|-------------|
| `pipeline` | array | Ordered list of model operations |

### `agent_delegation`
Delegate a task to a specialized agent.

| Parameter | Type | Description |
|-----------|------|-------------|
| `task` | string | Task description |
| `agent_type` | string | Target agent role |

### `replicate_universal`
Run any model on Replicate.

| Parameter | Type | Description |
|-----------|------|-------------|
| `model` | string | Replicate model ID |
| `input` | object | Model inputs |

### `universal_editor`
Edit any media type (image, video, audio, 3D).

| Parameter | Type | Description |
|-----------|------|-------------|
| `file_url` | string | Input file URL |
| `operation` | string | Edit operation |
| `params` | object | Operation parameters |

---

## Listing Available Tools at Runtime

```bash
# Via API
curl http://localhost:8000/tools

# Via chat
"What tools do you have available?"

# Via slash command
/help
```
