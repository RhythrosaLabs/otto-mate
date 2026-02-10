# Features

Complete documentation of Otto Chat's capabilities.

---

## 🧠 Super Intelligent Planning Agent

The core of Otto Chat is its autonomous planning system powered by Claude Opus 4.

### How It Works

```
User Request: "Create a product line with 3 beach-themed posters"
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    TASK ANALYZER                            │
│  • Parses natural language request                          │
│  • Identifies required tools: generate_image, printify_*    │
│  • Determines complexity: MEDIUM                            │
│  • Checks for parallelization opportunities                 │
└─────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    PLAN GENERATOR                           │
│  Step 1: Generate beach sunset image      ─┐               │
│  Step 2: Generate beach palm tree image    ├─ PARALLEL     │
│  Step 3: Generate beach waves image       ─┘               │
│  Step 4: Upload all images to Printify    ─ SEQUENTIAL     │
│  Step 5: Create poster products           ─ PARALLEL       │
│  Step 6: Publish all products             ─ PARALLEL       │
└─────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    EXECUTION ENGINE                         │
│  • Executes steps respecting dependencies                   │
│  • Chains outputs (image URLs → product creation)           │
│  • Handles errors with smart retry                          │
│  • Reports progress in real-time                            │
└─────────────────────────────────────────────────────────────┘
                               │
                               ▼
                          RESULTS
```

### Context Preservation

Otto remembers your preferences across conversations:

| Preference | Example | How It's Remembered |
|------------|---------|---------------------|
| **Aspect Ratio** | "I always want portrait images" | Stored in session |
| **Image Model** | Last used Flux Pro | Default for next request |
| **Style** | "Make it photorealistic" | Applied to similar requests |
| **Product Type** | Prefers framed art | Used when ambiguous |

### Agent Delegation

Complex tasks are automatically routed to specialized agents:

| Agent | Specialization | Keywords |
|-------|----------------|----------|
| **Content Agent** | Writing, copywriting | blog, article, write, content |
| **Image Agent** | Image generation, editing | image, picture, photo, design |
| **Video Agent** | Video creation | video, animation, commercial |
| **Research Agent** | Web research, analysis | research, find, analyze, compare |
| **Analytics Agent** | Data analysis | data, metrics, statistics, trends |
| **E-Commerce Agent** | Printify, Shopify | product, store, shop, sell |
| **Audio Agent** | Music, voice | music, audio, voice, sound |
| **Automation Agent** | Browser, workflows | automate, browse, fill, click |

---

## 🎨 Image Generation

### Available Models

| Model | Quality | Speed | Best For |
|-------|---------|-------|----------|
| **Flux Pro 1.1** | ⭐⭐⭐⭐⭐ | Medium | High-quality production |
| **Flux Dev** | ⭐⭐⭐⭐ | Fast | Rapid prototyping |
| **SDXL** | ⭐⭐⭐⭐ | Fast | General purpose |
| **Recraft V3** | ⭐⭐⭐⭐⭐ | Medium | Logos, icons, vectors |
| **Ideogram V2** | ⭐⭐⭐⭐ | Medium | Text in images |
| **Stable Diffusion 3** | ⭐⭐⭐⭐ | Fast | Stylized art |

### Aspect Ratios

| Ratio | Dimensions | Use Case |
|-------|------------|----------|
| **Portrait** | 2:3 (832×1216) | Phone wallpapers, posters |
| **Landscape** | 3:2 (1216×832) | Banners, headers |
| **Square** | 1:1 (1024×1024) | Social media, products |
| **Wide** | 16:9 (1344×768) | YouTube thumbnails |
| **Ultra-wide** | 21:9 (1536×640) | Hero images |
| **Custom** | Any | Specific requirements |

### Style Presets

```
"Generate [style] image of [subject]"
```

| Style | Description | Example |
|-------|-------------|---------|
| **Photorealistic** | Like a photograph | Product photography |
| **Cinematic** | Film-like, dramatic | Movie posters |
| **Artistic** | Painterly, creative | Art prints |
| **Minimal** | Clean, simple | Logos, icons |
| **Vintage** | Retro, aged | Nostalgic themes |
| **Neon** | Glowing, cyberpunk | Tech, gaming |
| **Watercolor** | Soft, painted | Soft aesthetics |
| **3D Render** | CGI-quality | Products, tech |

### Image Editing Tools

| Tool | Function | Example |
|------|----------|---------|
| `remove_background` | Remove background | Product photos |
| `upscale_image` | 4x resolution | Print preparation |
| `enhance_image` | Improve quality | Old photos |
| `colorize` | Add color to B&W | Historical images |
| `inpaint` | Edit parts of image | Fix imperfections |
| `style_transfer` | Apply art styles | Create variations |

### Example Commands

```
"Generate a photorealistic image of a coffee cup on a wooden table"

"Create a minimalist logo for 'TechFlow' in blue and white"

"Generate a wide landscape of mountains at sunset, cinematic style"

"Make a portrait image of an astronaut cat in space, artistic style"

"Upscale this image to 4K quality"

"Remove the background from this product photo"
```

---

## 🎬 Video Generation

### Available Models

| Model | Duration | Quality | Style |
|-------|----------|---------|-------|
| **Runway Gen-3 Alpha** | 4-10s | ⭐⭐⭐⭐⭐ | Realistic |
| **Luma Dream Machine** | 5-10s | ⭐⭐⭐⭐⭐ | Creative |
| **Minimax** | 5s | ⭐⭐⭐⭐ | Fast |
| **Kling AI** | 5-10s | ⭐⭐⭐⭐ | Realistic motion |

### Cinematic Style Presets

| Preset | Look | Best For |
|--------|------|----------|
| **Cinematic** | Film grain, letterbox | Trailers, drama |
| **Commercial** | Clean, bright | Ads, promos |
| **Luxury** | Slow, elegant | Premium brands |
| **Dynamic** | Fast cuts, energy | Sports, action |
| **Ambient** | Calm, peaceful | Meditation, spa |

### Video Creation Tools

| Tool | Function |
|------|----------|
| `generate_ai_video` | Text/image to video |
| `create_promo_video` | Full commercial production |
| `generate_video_thumbnails` | Extract key frames |
| `assemble_video_with_audio` | Combine video + music |
| `create_full_commercial` | End-to-end commercial |

### Example Commands

```
"Create a 5-second video of ocean waves at sunset"

"Generate a luxury commercial for my watch brand"

"Make a promo video for 'Bean There Coffee' with cinematic style"

"Create a dynamic product reveal video for sneakers"
```

---

## 🎵 Audio Generation

### Capabilities

| Feature | Description |
|---------|-------------|
| **AI Music** | Custom compositions in any genre |
| **Ambient Sounds** | Soundscapes and backgrounds |
| **Voice Synthesis** | Text-to-speech with emotions |
| **Voiceovers** | Professional narration |
| **Sound Effects** | UI sounds, transitions |

### Music Genres

```
ambient, electronic, cinematic, corporate, jazz, classical, 
lo-fi, hip-hop, rock, pop, epic, peaceful, dramatic
```

### Example Commands

```
"Create 30 seconds of upbeat corporate music"

"Generate ambient forest sounds for meditation"

"Create a voiceover saying 'Welcome to Bean There Coffee' in a warm voice"

"Generate a dramatic orchestral intro for a video"
```

---

## 🛍️ E-Commerce Integration

### Printify (Print-on-Demand)

#### Supported Product Types

| Category | Products |
|----------|----------|
| **Apparel** | T-shirts, hoodies, sweatshirts, tank tops |
| **Drinkware** | Mugs, tumblers, water bottles |
| **Wall Art** | Posters, canvas, framed prints |
| **Accessories** | Phone cases, tote bags, backpacks |
| **Home** | Blankets, pillows, towels |
| **Stationery** | Notebooks, stickers |

#### Workflow

```
1. Generate/upload image
2. Auto-select product template
3. Create product with title & description
4. Set pricing
5. Publish to sales channels
```

#### Example Commands

```
"Create a t-shirt with a space cat design"

"Generate 5 beach-themed posters and publish to my store"

"Make a mug design with 'Best Dad Ever' text"

"Create a framed art product from this sunset image"
```

### Shopify

#### Capabilities

| Feature | Description |
|---------|-------------|
| **Product Management** | Create, update, delete products |
| **Order Tracking** | View and manage orders |
| **Inventory** | Update stock levels |
| **Customers** | View customer data |
| **Analytics** | Sales and traffic data |

---

## 🔍 Research & Intelligence

### Web Search

| Tool | Function |
|------|----------|
| `web_search` | Google search via Serper |
| `search_news` | Current news articles |
| `search_images` | Image search |
| `search_videos` | Video search |

### Web Scraping

| Tool | Function |
|------|----------|
| `scrape_webpage` | Extract page content |
| `scrape_structured` | Extract structured data |
| `get_page_links` | Get all links |
| `summarize_url` | Summarize webpage |

### Research Capabilities

```
"Research the top AI startups of 2025"

"Find and compare pricing of 5 project management tools"

"Analyze competitor websites: nike.com, adidas.com, puma.com"

"Get the latest news about renewable energy"

"Summarize this article: [URL]"
```

---

## 🌐 Browser Automation

### Capabilities

| Tool | Function |
|------|----------|
| `browser_navigate` | Open URL |
| `browser_screenshot` | Capture page |
| `browser_click` | Click elements |
| `browser_type` | Enter text |
| `browser_scroll` | Scroll page |
| `browser_extract` | Extract data |

### Example Workflows

```
"Go to google.com and search for 'best coffee shops in NYC'"

"Navigate to amazon.com/best-sellers and screenshot the page"

"Fill out the contact form on example.com with my info"
```

---

## 📧 Email Marketing

### Providers

| Provider | Features |
|----------|----------|
| **SendGrid** | High deliverability, templates |
| **SMTP** | Any email server |

### Capabilities

```
"Send a promotional email to hello@example.com about our new launch"

"Generate and send a newsletter about our latest products"

"Create an email template for customer onboarding"
```

---

## 🔌 Plugin System

Extend Otto with custom functionality. See [[Plugin Development]] for details.

### Included Plugins

| Plugin | Description | Tools |
|--------|-------------|-------|
| **Web Scraper** | Advanced web scraping | scrape_page, extract_links, extract_tables |
| **Notification Sender** | Multi-channel notifications | send_email, send_slack, send_discord |
| **Database Connector** | SQL database queries | query_database, list_tables, insert_data |

### Creating Plugins

```python
from src.core.plugin_system import ToolPlugin

class MyPlugin(ToolPlugin):
    async def my_tool(self, input: str) -> dict:
        return {"result": f"Processed: {input}"}
```

---

## 📋 Task Queue & Calendar

### Task States

| State | Description |
|-------|-------------|
| **Pending** | Waiting to start |
| **Running** | Currently executing |
| **Completed** | Finished successfully |
| **Failed** | Encountered error |
| **Scheduled** | Waiting for time |

### Features

- **Real-time progress** tracking
- **Priority system** (low, normal, high, urgent)
- **Recurring tasks** (daily, weekly, monthly)
- **Dependencies** between tasks
- **Calendar view** for scheduled tasks

---

## 🎨 User Interface

### 14 Visual Themes

| Theme | Colors |
|-------|--------|
| Classic | Purple/Pink |
| Midnight | Deep Blue |
| Sunset | Orange/Pink |
| Ocean | Blue/Teal |
| Forest | Green |
| Cherry | Red |
| Retro | Neon 80s |
| Copper | Warm Metal |
| Nordic | Clean White |
| Matrix | Terminal Green |
| Lavender | Soft Purple |
| Neon | Cyberpunk |
| Monochrome | B&W |
| Sakura | Cherry Blossom |

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `⌘+Enter` | Send message |
| `⌘+,` | Settings |
| `⌘+Q` | Queue |
| `⌘+J` | Jobs |
| `?` | Help |

---

## 🔒 Security

| Feature | Description |
|---------|-------------|
| **Environment Variables** | API keys never in code |
| **CORS** | Configurable origins |
| **Rate Limiting** | Prevent abuse |
| **Input Validation** | Pydantic models |

---

## ⚡ Performance

| Feature | Description |
|---------|-------------|
| **Parallel Execution** | Run independent tasks together |
| **Smart Retry** | Exponential backoff |
| **Connection Pooling** | Efficient API usage |
| **Caching** | Reduce redundant calls |
