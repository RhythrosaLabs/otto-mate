# Otto Universal - Vanilla JS Frontend

Modern vanilla JavaScript frontend for Otto Universal.

## Structure

```
vanilla-js/
├── public/          # Static files served directly
│   ├── index.html
│   ├── chat.html
│   ├── settings.html
│   ├── files.html
│   └── assets/
│       ├── css/     # Stylesheets
│       ├── js/      # Compiled/built JS
│       └── images/  # Images
├── src/             # Source files
│   ├── api/         # API client (symlinked from shared)
│   ├── components/  # UI components
│   ├── utils/       # Utilities
│   └── app.js       # Main entry point
└── README.md
```

## Development

### Using API Client

```javascript
import { OttoApiClient } from './api/client.js';

const client = new OttoApiClient({
    baseUrl: window.location.origin
});

// Send message
const response = await client.sendMessage(
    "Hello Otto",
    "session-123"
);

// Stream message
for await (const chunk of client.streamMessage("Hello", "session-123")) {
    console.log(chunk.type, chunk.content);
}
```

### Component Pattern

Components should be modular and reusable:

```javascript
// src/components/chat.js
export class ChatComponent {
    constructor(apiClient) {
        this.client = apiClient;
    }
    
    mount(selector) {
        const container = document.querySelector(selector);
        container.innerHTML = this.render();
        this.attachEvents();
    }
    
    render() {
        return `<div class="chat">...</div>`;
    }
    
    attachEvents() {
        // Event listeners
    }
}
```

## Building

No build step required! Pure vanilla JS with ES modules.

For production, consider:
- Minification (Terser)
- Bundling (Vite/Rollup)
- CSS processing (PostCSS)

## API Integration

All API calls go through the OttoApiClient:

- ✅ Type-safe (JSDoc comments)
- ✅ Error handling built-in
- ✅ Streaming support
- ✅ Works with any framework

## Migration from src/web

Old structure:
```
src/web/
├── chat.html        # Inline JS
├── settings.html    # Inline JS
└── css/             # Styles
```

New structure:
```
frontends/vanilla-js/
├── public/          # HTML files
│   └── assets/css/  # Styles
└── src/             # Extracted JS modules
```

Benefits:
- Cleaner code organization
- Reusable components
- Better testability
- Framework-agnostic API client
