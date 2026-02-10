# Themes

Otto Chat includes 14 professionally designed color themes with both dark and light variants.

---

## Available Themes

### Dark Themes

| Theme | Primary | Accent | Best For |
|-------|---------|--------|----------|
| **Default Dark** | `#1a1a2e` | `#4f46e5` | General use |
| **Cyberpunk** | `#0d0d0d` | `#ff00ff` | Tech/gaming |
| **Forest** | `#1a2e1a` | `#22c55e` | Nature/eco |
| **Ocean** | `#0f172a` | `#06b6d4` | Calm/professional |
| **Sunset** | `#1f1a1e` | `#f97316` | Warm/creative |
| **Midnight** | `#0a0a14` | `#8b5cf6` | Late night |
| **Monochrome** | `#121212` | `#888888` | Minimal |

### Light Themes

| Theme | Primary | Accent | Best For |
|-------|---------|--------|----------|
| **Default Light** | `#f8fafc` | `#4f46e5` | General use |
| **Cream** | `#fdfaf5` | `#d97706` | Warm/readable |
| **Paper** | `#fafafa` | `#525252` | Minimal |
| **Sky** | `#f0f9ff` | `#0284c7` | Fresh/clean |
| **Lavender** | `#faf5ff` | `#9333ea` | Creative |
| **Mint** | `#f0fdf4` | `#16a34a` | Fresh/natural |
| **Rose** | `#fff1f2` | `#e11d48` | Soft/feminine |

---

## Theme Colors Reference

### Default Dark
```css
--bg-primary: #1a1a2e;
--bg-secondary: #16162a;
--bg-tertiary: #252544;
--text-primary: #f1f5f9;
--text-secondary: #94a3b8;
--accent: #4f46e5;
--accent-hover: #6366f1;
--border: #2e2e4a;
```

### Cyberpunk
```css
--bg-primary: #0d0d0d;
--bg-secondary: #1a1a1a;
--bg-tertiary: #262626;
--text-primary: #00ffff;
--text-secondary: #ff00ff;
--accent: #ff00ff;
--accent-hover: #ff66ff;
--border: #ff00ff33;
```

### Forest
```css
--bg-primary: #1a2e1a;
--bg-secondary: #152815;
--bg-tertiary: #1f3a1f;
--text-primary: #d4f5d4;
--text-secondary: #86c086;
--accent: #22c55e;
--accent-hover: #4ade80;
--border: #2d4a2d;
```

### Ocean
```css
--bg-primary: #0f172a;
--bg-secondary: #0c1420;
--bg-tertiary: #1e293b;
--text-primary: #e2e8f0;
--text-secondary: #64748b;
--accent: #06b6d4;
--accent-hover: #22d3ee;
--border: #1e3a5f;
```

### Sunset
```css
--bg-primary: #1f1a1e;
--bg-secondary: #1a1518;
--bg-tertiary: #2d252b;
--text-primary: #fde6d8;
--text-secondary: #d4a088;
--accent: #f97316;
--accent-hover: #fb923c;
--border: #3d2d36;
```

### Midnight
```css
--bg-primary: #0a0a14;
--bg-secondary: #050510;
--bg-tertiary: #15152a;
--text-primary: #e8e8ff;
--text-secondary: #8888bb;
--accent: #8b5cf6;
--accent-hover: #a78bfa;
--border: #25254a;
```

### Monochrome
```css
--bg-primary: #121212;
--bg-secondary: #0a0a0a;
--bg-tertiary: #1f1f1f;
--text-primary: #e0e0e0;
--text-secondary: #888888;
--accent: #888888;
--accent-hover: #aaaaaa;
--border: #2a2a2a;
```

---

## Light Theme Colors

### Default Light
```css
--bg-primary: #f8fafc;
--bg-secondary: #f1f5f9;
--bg-tertiary: #e2e8f0;
--text-primary: #1e293b;
--text-secondary: #475569;
--accent: #4f46e5;
--accent-hover: #6366f1;
--border: #cbd5e1;
```

### Cream
```css
--bg-primary: #fdfaf5;
--bg-secondary: #faf5eb;
--bg-tertiary: #f5ecdc;
--text-primary: #422006;
--text-secondary: #78350f;
--accent: #d97706;
--accent-hover: #f59e0b;
--border: #e6d5c0;
```

### Paper
```css
--bg-primary: #fafafa;
--bg-secondary: #f5f5f5;
--bg-tertiary: #e5e5e5;
--text-primary: #171717;
--text-secondary: #525252;
--accent: #525252;
--accent-hover: #737373;
--border: #d4d4d4;
```

### Sky
```css
--bg-primary: #f0f9ff;
--bg-secondary: #e0f2fe;
--bg-tertiary: #bae6fd;
--text-primary: #0c4a6e;
--text-secondary: #0369a1;
--accent: #0284c7;
--accent-hover: #0ea5e9;
--border: #7dd3fc;
```

### Lavender
```css
--bg-primary: #faf5ff;
--bg-secondary: #f3e8ff;
--bg-tertiary: #e9d5ff;
--text-primary: #3b0764;
--text-secondary: #6b21a8;
--accent: #9333ea;
--accent-hover: #a855f7;
--border: #d8b4fe;
```

### Mint
```css
--bg-primary: #f0fdf4;
--bg-secondary: #dcfce7;
--bg-tertiary: #bbf7d0;
--text-primary: #14532d;
--text-secondary: #166534;
--accent: #16a34a;
--accent-hover: #22c55e;
--border: #86efac;
```

### Rose
```css
--bg-primary: #fff1f2;
--bg-secondary: #ffe4e6;
--bg-tertiary: #fecdd3;
--text-primary: #4c0519;
--text-secondary: #881337;
--accent: #e11d48;
--accent-hover: #f43f5e;
--border: #fda4af;
```

---

## Changing Themes

### Via UI

1. Click the Settings icon in the sidebar (or press `Ctrl+,`)
2. Navigate to **Appearance** section
3. Select from the theme dropdown
4. Theme changes apply immediately

### Via Keyboard

Press `Ctrl+T` to cycle through themes.

### Via API

```bash
# Get current theme
curl http://localhost:8000/api/settings

# Set theme
curl -X PUT http://localhost:8000/api/settings \
  -H "Content-Type: application/json" \
  -d '{"theme": "cyberpunk"}'
```

---

## Creating Custom Themes

### Step 1: Create Theme File

Create a new CSS file in `frontends/vanilla-js/css/themes/`:

```css
/* my-theme.css */
:root[data-theme="my-theme"] {
  /* Backgrounds */
  --bg-primary: #1a1a2e;
  --bg-secondary: #16162a;
  --bg-tertiary: #252544;
  --bg-hover: #2e2e4a;
  
  /* Text */
  --text-primary: #f1f5f9;
  --text-secondary: #94a3b8;
  --text-muted: #64748b;
  
  /* Accent */
  --accent: #4f46e5;
  --accent-hover: #6366f1;
  --accent-muted: #4f46e533;
  
  /* Borders */
  --border: #2e2e4a;
  --border-strong: #404060;
  
  /* Status Colors */
  --success: #22c55e;
  --warning: #f59e0b;
  --error: #ef4444;
  --info: #3b82f6;
  
  /* Component Specific */
  --input-bg: var(--bg-secondary);
  --button-bg: var(--accent);
  --message-user: var(--accent);
  --message-assistant: var(--bg-tertiary);
  --sidebar-bg: var(--bg-secondary);
  --scrollbar: #444;
  --scrollbar-hover: #555;
}
```

### Step 2: Import Theme

Add to `frontends/vanilla-js/css/main.css`:

```css
@import 'themes/my-theme.css';
```

### Step 3: Register Theme

Add to theme list in `frontends/vanilla-js/js/settings.js`:

```javascript
const themes = [
  // ... existing themes
  { id: 'my-theme', name: 'My Theme', type: 'dark' }
];
```

---

## CSS Variables Reference

### Required Variables

| Variable | Description |
|----------|-------------|
| `--bg-primary` | Main background |
| `--bg-secondary` | Sidebar, cards |
| `--bg-tertiary` | Active states, nested elements |
| `--text-primary` | Main text color |
| `--text-secondary` | Subdued text |
| `--accent` | Primary action color |
| `--border` | Standard borders |

### Optional Variables

| Variable | Default Fallback |
|----------|-----------------|
| `--bg-hover` | Lighter `--bg-tertiary` |
| `--text-muted` | Lighter `--text-secondary` |
| `--accent-hover` | Lighter `--accent` |
| `--accent-muted` | `--accent` at 20% opacity |
| `--border-strong` | Darker `--border` |

---

## Theme Best Practices

### Contrast Ratios

Ensure accessibility with proper contrast:

| Element | Minimum Ratio |
|---------|--------------|
| Body text | 4.5:1 |
| Large text | 3:1 |
| UI components | 3:1 |

### Testing

1. Check readability in both bright and dark environments
2. Test all component states (hover, active, disabled)
3. Verify color-blind accessibility
4. Test on different screen types (OLED, LCD)

### Light Theme Considerations

- Ensure sufficient contrast for text on light backgrounds
- Use subtle shadows instead of heavy borders
- Consider eye strain for extended use

### Dark Theme Considerations

- Avoid pure black (`#000000`) - use dark grays instead
- Ensure white text isn't too bright (use `#f1f5f9` instead of `#ffffff`)
- Add subtle background differentiation between sections
