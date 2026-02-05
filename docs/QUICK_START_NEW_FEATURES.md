# 🚀 Quick Start Guide - New Features

## What's New

Otto now has **Extensions** and **Profile** management built directly into the Settings panel!

---

## 📍 Access Settings

1. Open your browser to: `http://localhost:8000`
2. Click **Settings** in the top navigation
3. Or go directly to: `http://localhost:8000/settings.html`

---

## 🔌 Extensions Panel

### What Are Extensions?
Extensions are integrations that give Otto superpowers. Think of them as plugins you can turn on/off.

### Available Extensions (11 Total)

**E-commerce:**
- 🛍️ Printify - Create print-on-demand products
- 🛒 Shopify - Manage your store

**AI Models:**
- 🤖 Replicate - Access 1000+ AI models
- 🔗 Model Chaining - Chain multiple AI models

**Automation:**
- 🌐 Browser - Automate web tasks

**Research:**
- 🔍 Web Search - Search the internet

**Storage:**
- 💾 File Storage - Manage files and images

**Productivity:**
- ✍️ Content Generation - Generate marketing copy
- 💻 Code Execution - Run code snippets
- 📊 Data Processing - Convert and process data
- 📋 Task Queue - Background task management

### How to Use

1. **View Extensions:** Click "Extensions" in sidebar
2. **Search:** Type in search box to filter
3. **Filter by Category:** Click category buttons (E-commerce, AI Models, etc.)
4. **Enable/Disable:** Toggle switch in top-right of each card
5. **Check Status:** 
   - ✓ Configured = Ready to use (has API keys)
   - ⚠ Not Configured = Needs API key setup
6. **Configure:** Click "Manage Connections" link to add API keys
7. **Apply Changes:** Restart server after toggling

### Status Badges

- **✓ Configured** (green) = Extension has all required API keys
- **⚠ Not Configured** (orange) = Missing API keys (shows which ones)

### Example Use Cases

- **New user:** Disable extensions you don't need to reduce clutter
- **E-commerce seller:** Enable Printify + Shopify, disable others
- **Content creator:** Enable Replicate + Content Generation + Web Search
- **Developer:** Enable Code Execution + Browser + File Storage

---

## 👤 Profile Panel

### What Is Profile?
Your profile tells Otto about you, your business, and your goals. Otto remembers everything across ALL chat sessions.

### Profile Fields

**Basic Info:**
- Name
- Email
- Company Name
- Industry (e.g., "Fashion", "Tech", "Food")
- Target Audience (e.g., "Young professionals", "Parents")
- Website

**Brand Voice:**
- Describe your brand's tone and style
- Examples: "Professional and friendly", "Casual and fun", "Authoritative expert"

**Memory Lists:**

1. **Facts** - Things Otto should always remember
   - Example: "I sell sustainable fashion"
   - Example: "My store launched in 2024"
   - Example: "I have 50,000 Instagram followers"

2. **Learnings** - Insights Otto has discovered
   - Example: "User prefers dark product photography"
   - Example: "Best posting time is 9am EST"
   - Example: "Customers respond well to eco-friendly messaging"

3. **Goals** - What you're working towards
   - Example: "Launch 10 new products this quarter"
   - Example: "Grow email list to 5000 subscribers"
   - Example: "Improve website conversion rate"

### How to Use

1. **Open Profile:** Click "Profile" in sidebar
2. **Fill Basic Info:** Enter name, company, industry, etc.
3. **Add Facts:** Type in "Add a fact" box, click Add
4. **Add Learnings:** Type what Otto has learned, click Add
5. **Add Goals:** Type your goals, click Add
6. **Remove Items:** Click × button next to any fact/learning/goal
7. **Save:** Click "Save Profile" button
8. **Reload:** Click "Reload" to refresh from server

### Why Use Profile?

**Before Profile:**
```
You: "Create a product for my brand"
Otto: "What's your brand about?"
```

**With Profile:**
```
You: "Create a product for my brand"
Otto: "I'll create a sustainable fashion product for [Your Company], 
      targeting young professionals with your professional and friendly 
      brand voice. This aligns with your goal to launch 10 new products 
      this quarter."
```

### Pro Tips

- **Be specific:** "I sell minimalist home decor" > "I sell products"
- **Update regularly:** Add learnings as you work with Otto
- **Set SMART goals:** Specific, measurable goals get better results
- **Brand voice matters:** Helps Otto write in YOUR style
- **Facts persist:** Once added, Otto remembers FOREVER (across all chats)

---

## 🎯 Quick Workflows

### Workflow 1: First-Time Setup
1. Go to Settings → Profile
2. Fill in Name, Company, Industry, Target Audience
3. Add 3-5 key facts about your business
4. Add 2-3 current goals
5. Save profile
6. Go to Settings → Extensions
7. Disable extensions you don't need
8. Restart server
9. Start chatting!

### Workflow 2: E-commerce Seller
**Profile:**
- Company: [Your Store Name]
- Industry: Fashion / Home / Food (your niche)
- Target Audience: [Your ideal customer]
- Fact: "I use Printify for print-on-demand"
- Fact: "My Shopify store is [URL]"
- Goal: "Launch [X] new products per month"

**Extensions:**
- ✅ Enable: Printify, Shopify, Replicate, Content Generation, File Storage
- ❌ Disable: Browser, Code Execution, Data Processing, Task Queue

### Workflow 3: Content Creator
**Profile:**
- Company: [Your Brand]
- Industry: Content Creation
- Target Audience: [Your followers]
- Brand Voice: "Energetic and inspiring with humor"
- Fact: "I post on Instagram, YouTube, TikTok"
- Goal: "Create [X] pieces of content per week"

**Extensions:**
- ✅ Enable: Replicate, Content Generation, Web Search, File Storage
- ❌ Disable: Printify, Shopify, Code Execution, Browser

### Workflow 4: Developer/Technical
**Profile:**
- Company: [Your Project]
- Industry: Software / Tech
- Goal: "Build [X feature] this sprint"
- Fact: "I use Python and React"

**Extensions:**
- ✅ Enable: Code Execution, Browser, Web Search, File Storage, Model Chaining
- ❌ Disable: Printify, Shopify, Content Generation

---

## 🔑 API Keys Setup

If you see "⚠ Not Configured" on extensions:

1. Click "🔑 Manage Connections" in settings sidebar
2. Or go to: `http://localhost:8000/onboarding`
3. Enter API keys for services you want to use
4. Return to Extensions panel
5. Status will change to "✓ Configured"

**Where to Get Keys:**
- Printify: https://printify.com/app/account/api
- Shopify: Your store admin → Apps → Create private app
- Replicate: https://replicate.com/account/api-tokens
- Serper (Web Search): https://serper.dev/api-key
- Anthropic Claude: https://console.anthropic.com/

---

## 💡 Tips & Tricks

### Extensions
- **Start with everything enabled** - See what Otto can do
- **Gradually disable** - Remove what you don't use
- **Check tool counts** - Shows how many capabilities each extension adds
- **Search works well** - Try "ecom", "AI", "web", etc.
- **Restart required** - Changes apply after server restart

### Profile
- **Add facts as you go** - While chatting, if Otto asks something, add it as a fact
- **Update learnings** - When Otto discovers something useful, capture it
- **Review monthly** - Update goals and facts as your business evolves
- **Be conversational** - Write facts like you're talking: "I love bold colors"
- **Multiple goals OK** - Add short-term and long-term goals

### Integration
- **User ID support** - Future: Multiple users can have separate profiles
- **Profile context is automatic** - Otto always has access, no need to repeat yourself
- **Extensions filter tools** - Disabled extensions = tools hidden from Otto
- **Memory persists** - Profile stored in `data/profiles/default.json`

---

## 🆘 Troubleshooting

**Extensions not loading:**
- Check server console for errors
- Ensure server is running: `python run.py`
- Refresh browser (Cmd+R / Ctrl+R)

**Profile not saving:**
- Check network tab for API errors
- Ensure `/profile` endpoint is accessible
- Try clicking Reload to sync

**Extension toggle not working:**
- Check server logs
- Ensure you have write permissions to settings
- Try restarting server

**Changes not applying:**
- **Important:** Extension enable/disable requires server restart
- Profile changes apply immediately
- Clear browser cache if CSS looks wrong

---

## 📱 Mobile Support

Both Extensions and Profile panels are mobile-responsive:
- Grid becomes single column on small screens
- Filters become scrollable
- Sidebar collapses into horizontal tabs
- Forms stack vertically

---

## 🎉 You're Ready!

Your Otto setup is now complete with:
- ✅ 11 manageable extensions
- ✅ Persistent user profile
- ✅ Beautiful settings interface
- ✅ AI that remembers everything

**Next:** Start chatting and watch Otto use your profile context automatically!

Questions? Check `IMPLEMENTATION_COMPLETE.md` for full technical details.
