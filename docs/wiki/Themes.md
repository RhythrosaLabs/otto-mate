# Themes

Otto Chat includes 14+ visual themes for the web interface.

---

## Available Themes

| Theme | Description | Colors |
|-------|-------------|--------|
| **Aurora** (default) | Modern gradient design | Purple → Pink → Teal |
| **Light** | Clean, bright interface | White, light gray |
| **Dark** | Dark mode with soft contrast | Dark gray, subtle accents |
| **Midnight** | Deep dark blue | Navy, steel blue |
| **Sunset** | Warm golden tones | Orange, amber, coral |
| **Ocean** | Cool marine palette | Deep blue, turquoise, teal |
| **Forest** | Natural greens | Emerald, sage, moss |
| **Cherry** | Bold red aesthetics | Cherry red, pink, rose |
| **Retro** | Vintage/nostalgic feel | Warm browns, beige, orange |
| **Copper** | Metallic warm tones | Copper, bronze, gold |
| **Nordic** | Scandinavian minimalism | Cool whites, pale blue |
| **Matrix** | Cyberpunk terminal | Black, bright green |
| **Lavender** | Soft purple palette | Lavender, lilac, violet |
| **Neon** | Vibrant glowing colors | Electric blue, magenta, green |
| **Monochrome** | Grayscale elegance | Black, white, gray |
| **Sakura** | Japanese cherry blossom | Soft pink, white, green |

---

## Switching Themes

### Via Keyboard Shortcut
Press **⌘+,** (Cmd+Comma) to open Settings, then select a theme.

### Via Settings Page
Navigate to `/settings-page` and use the theme selector.

### Via API
```bash
curl -X PUT http://localhost:8000/api/settings \
  -H "Content-Type: application/json" \
  -d '{"theme": "midnight"}'
```

---

## Theme Features

- **Light/Dark Optimization** — Every theme is optimized for readability in both light and dark modes
- **Gradient Sidebars** — Smooth gradient transitions in the sidebar
- **Animated Elements** — Subtle hover and transition animations
- **Particle Effects** — Optional ambient particle effects
- **Consistent Styling** — All UI components (buttons, inputs, modals, cards) respect the active theme
- **Message Styling** — User and AI messages styled differently per theme
- **Code Highlighting** — Syntax highlighting adapts to theme colors

---

## CSS Architecture

Themes are implemented as CSS custom properties (variables) in `src/web/static/css/`:

- `base.css` — Reset and foundation styles
- `themes.css` — All theme definitions as CSS custom properties
- `layout.css` — Page layout and grid
- `sidebar.css` — Sidebar styling
- `chat.css` — Chat interface styling
- `editor.css` — Editor and preview styling
- `modals.css` — Modal dialogs
- `components.css` — Reusable components

### Theme Variables

Each theme defines variables like:
```css
[data-theme="midnight"] {
  --bg-primary: #0d1117;
  --bg-secondary: #161b22;
  --text-primary: #c9d1d9;
  --text-secondary: #8b949e;
  --accent-primary: #58a6ff;
  --accent-secondary: #1f6feb;
  --border-color: #30363d;
  --sidebar-bg: linear-gradient(180deg, #0d1117, #161b22);
  --message-user-bg: #1f6feb;
  --message-ai-bg: #21262d;
  /* ... */
}
```
