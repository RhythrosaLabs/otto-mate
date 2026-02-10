# Features

Otto Chat combines 100+ tools with AI intelligence to automate your creative business.

## Core Capabilities

### 🧠 Super Intelligent Planning Agent

The brain of Otto Chat uses Claude Opus 4 to understand complex requests and break them into executable steps.

- **Multi-Step Execution** - Automatically decomposes complex tasks
- **Context Preservation** - Remembers preferences across conversations
- **Dependency Resolution** - Chains outputs between steps
- **Batch Operations** - Process multiple items in parallel
- **Agent Delegation** - Routes to specialized agents by task type

### 🔌 Third-Party Plugin System

Extend Otto with custom functionality.

- **Easy Installation** - Drop plugins into `/plugins` directory
- **Plugin Types** - Tool plugins and Integration plugins
- **Settings Schema** - Declarative JSON configuration
- **Hot Reloading** - No restart required
- **Management UI** - Enable/disable from Settings

See [[Plugin Development]] for details.

### 📋 Task Queue & Calendar

Manage and schedule your automation tasks.

- **Visual Queue** - See pending, running, completed tasks
- **Calendar View** - Schedule for specific dates
- **Progress Tracking** - Real-time progress indicators
- **Priority System** - Low, normal, high, urgent
- **Recurring Tasks** - Daily, weekly, monthly schedules
- **Dependencies** - Chain dependent tasks

---

## AI Generation Tools

### 🎨 Image Generation (15+ Models)

| Model | Best For |
|-------|----------|
| Flux Pro 1.1 | Highest quality, photorealistic |
| Flux Dev | Fast iteration, prototyping |
| SDXL | General purpose, stylized |
| Recraft V3 | Logos, icons, vector-style |
| Ideogram V2 | Text in images |

**Features:**
- Multiple aspect ratios (portrait, landscape, square, custom)
- Style presets (photorealistic, artistic, cinematic, product)
- Background removal
- AI upscaling (4x)
- Logo and icon generation

### 🎬 Video Generation (10+ Models)

| Model | Description |
|-------|-------------|
| Runway Gen-3 Alpha | High-quality video synthesis |
| Luma Dream Machine | Creative video generation |
| Minimax | Fast video generation |
| Kling AI | Realistic motion |

**Style Presets:**
- Cinematic - Film look with depth of field
- Commercial - Clean, professional
- Luxury - Premium brand aesthetic
- Dynamic - High energy, fast pacing
- Ambient - Calm, atmospheric

### 🎵 Audio Generation

- **AI Music** - Custom compositions
- **Ambient Sounds** - Soundscapes and backgrounds
- **Voice Synthesis** - Text-to-speech
- **Voiceovers** - Professional narration

---

## E-Commerce Integration

### 🖨️ Printify

Full print-on-demand workflow:

1. Generate design image
2. Auto-select product type
3. Create product listing
4. Publish to sales channels

**Supported Products:**
- T-shirts, hoodies, sweatshirts
- Mugs, tumblers, water bottles
- Posters, canvas prints, framed art
- Phone cases, laptop sleeves
- Tote bags, backpacks
- And 30+ more...

### 🛒 Shopify

- Product management
- Order tracking
- Customer management
- Inventory control

---

## Research & Intelligence

### 🔍 Web Search

- Google search via Serper API
- News aggregation
- Image and video search
- Smart result parsing

### 🌐 Web Scraping

- Extract page content
- Parse structured data
- Follow links
- Summarize webpages

### 📊 Competitive Intelligence

- Competitor analysis
- Market trend research
- Opportunity identification
- Multi-source citations

---

## Communication

### 📧 Email Marketing

- HTML email templates
- SendGrid & SMTP support
- AI-generated content
- Campaign management

### 🎙️ Voice Capabilities

- Speech-to-text (Whisper)
- Text-to-speech
- Voice commands

---

## User Interface

### 🎨 14 Visual Themes

| Theme | Description |
|-------|-------------|
| Classic | Purple gradient default |
| Midnight | Deep dark blues |
| Sunset | Warm orange/pink |
| Ocean | Cool blues and teals |
| Forest | Natural greens |
| Cherry | Vibrant reds |
| Retro | 80s-inspired neon |
| Copper | Warm metallics |
| Nordic | Clean, minimal |
| Matrix | Green terminal |
| Lavender | Soft purples |
| Neon | Bright cyberpunk |
| Monochrome | Black and white |
| Sakura | Cherry blossom pink |

### ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `⌘+Enter` | Send message |
| `⌘+,` | Settings |
| `⌘+Q` | Task queue |
| `⌘+J` | Jobs panel |
| `?` | Help modal |

### 📁 File Management

- Smart categorization
- Download all as ZIP
- Cloud storage ready
- Version tracking

---

## Reliability

- **Smart Retry** - Exponential backoff for rate limits
- **Error Recovery** - Graceful failure handling
- **Connection Resilience** - Auto-reconnection
- **Progress Persistence** - Resume interrupted tasks
