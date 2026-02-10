# Themes

Otto Chat includes 14 beautiful themes to customize your experience.

## Available Themes

| Theme | Primary Colors | Best For |
|-------|----------------|----------|
| **Classic** | Purple/Pink gradient | Default, modern look |
| **Midnight** | Deep blues | Night work, reduced eye strain |
| **Sunset** | Orange/Pink warm | Creative, energetic mood |
| **Ocean** | Blues and teals | Calm, focused work |
| **Forest** | Natural greens | Nature-inspired, peaceful |
| **Cherry** | Vibrant reds | Bold, energetic |
| **Retro** | 80s neon | Fun, nostalgic |
| **Copper** | Warm metallics | Professional, elegant |
| **Nordic** | Clean whites/grays | Minimalist, light |
| **Matrix** | Terminal green | Developer, hacker aesthetic |
| **Lavender** | Soft purples | Gentle, relaxing |
| **Neon** | Bright cyberpunk | Bold, futuristic |
| **Monochrome** | Black and white | Classic, distraction-free |
| **Sakura** | Cherry blossom pink | Spring, delicate |

## Changing Themes

### Via Settings

1. Click the ⚙️ Settings button
2. Find "Theme" dropdown in Preferences
3. Select your preferred theme
4. Changes apply immediately

### Keyboard Shortcut

Press `⌘+,` (Mac) or `Ctrl+,` (Windows) to open Settings.

---

## Theme Previews

### Classic (Default)
```
Background: Deep purple-black (#0a0a0f)
Accent: Purple gradient (#8b5cf6 → #ec4899)
Text: White (#ffffff)
```

### Midnight
```
Background: Navy blue (#0f172a)
Accent: Blue (#3b82f6)
Text: Light gray (#e2e8f0)
```

### Sunset
```
Background: Dark warm (#1a0f0f)
Accent: Orange/Pink (#f97316 → #ec4899)
Text: Warm white (#fef3c7)
```

### Ocean
```
Background: Deep teal (#0f1729)
Accent: Cyan (#06b6d4)
Text: Light blue (#e0f2fe)
```

### Forest
```
Background: Dark green (#0f1f0f)
Accent: Green (#22c55e)
Text: Light green (#dcfce7)
```

### Matrix
```
Background: Pure black (#000000)
Accent: Terminal green (#00ff00)
Text: Green (#4ade80)
Font: Monospace
```

---

## Light Mode Support

All themes are optimized for both dark and light modes. The system respects your OS preference or can be manually toggled.

### Light Mode Adjustments

- Higher contrast text colors
- Lighter backgrounds
- Adjusted accent colors for visibility
- Softer shadows

---

## Custom Themes (Advanced)

You can create custom themes by modifying CSS variables:

```css
:root {
  /* Background colors */
  --bg-primary: #0a0a0f;
  --bg-secondary: #12121a;
  --bg-tertiary: #1a1a24;
  
  /* Accent colors */
  --accent-purple: #8b5cf6;
  --accent-pink: #ec4899;
  --accent-blue: #3b82f6;
  --accent-cyan: #06b6d4;
  
  /* Text colors */
  --text: #ffffff;
  --text-muted: #9ca3af;
  --text-dim: #6b7280;
  
  /* Gradients */
  --sidebar-gradient: linear-gradient(180deg, 
    rgba(139, 92, 246, 0.08) 0%, 
    transparent 100%);
}
```

### Adding a Custom Theme

1. Edit `src/web/chat.html`
2. Find the theme selector section
3. Add your theme option
4. Add CSS variables for your theme

---

## Theme-Aware Components

These UI elements automatically adapt to themes:

- **Chat bubbles** - Background and text colors
- **Sidebars** - Gradients and borders
- **Buttons** - Accent colors and hover states
- **Inputs** - Borders and focus states
- **Cards** - Backgrounds and shadows
- **Toggles** - Active/inactive states
- **Progress bars** - Fill colors
- **Badges** - Status colors

---

## Accessibility

All themes meet WCAG 2.1 contrast requirements:

- **AA Standard** - Minimum 4.5:1 for normal text
- **AAA Standard** - 7:1 for enhanced contrast (available in settings)

### High Contrast Mode

Optional high contrast mode increases readability:

1. Open Settings
2. Enable "High Contrast" toggle
3. Text and UI elements become more distinct
