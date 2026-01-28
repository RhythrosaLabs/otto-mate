#!/usr/bin/env python3
"""Fix the formatMessage function in chat.html"""

import re

with open('src/web/chat.html', 'r') as f:
    content = f.read()

# Find the formatMessage function and replace it
old_pattern = r'function formatMessage\(content\) \{[^}]+return formatted;\s*\}'

new_func = r'''function formatMessage(content) {
            let formatted = content;
            const urls = [];
            formatted = formatted.replace(/(https?:\/\/[^\s<>"']+|\/files\/[a-f0-9]+)/gi, (url) => {
                urls.push(url);
                return '__URL_' + (urls.length - 1) + '__';
            });
            formatted = escapeHtml(formatted);
            formatted = formatted
                .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
                .replace(/\*(.+?)\*/g, '<em>$1</em>')
                .replace(/`(.+?)`/g, '<code>$1</code>')
                .replace(/\n/g, '<br>');
            urls.forEach((url, i) => {
                let html;
                const lower = url.toLowerCase();
                if (lower.match(/\.(png|jpg|jpeg|gif|webp|svg|bmp)(\?|$)/) || lower.includes('replicate.delivery')) {
                    html = '<div class="media-embed"><img src="' + url + '" style="max-width:100%;border-radius:12px"/></div>';
                } else if (lower.match(/\.(mp4|webm|mov)(\?|$)/)) {
                    html = '<div class="media-embed"><video controls style="max-width:100%;border-radius:12px"><source src="' + url + '"></video></div>';
                } else if (lower.match(/\.(mp3|wav|ogg)(\?|$)/)) {
                    html = '<div class="media-embed"><audio controls><source src="' + url + '"></audio></div>';
                } else if (url.startsWith('/files/')) {
                    html = '<div class="media-embed"><img src="' + url + '" style="max-width:100%;border-radius:12px"/></div>';
                } else {
                    html = '<a href="' + url + '" target="_blank">' + url + '</a>';
                }
                formatted = formatted.replace('__URL_' + i + '__', html);
            });
            return formatted;
        }'''

# Try to replace
new_content = re.sub(old_pattern, new_func, content, flags=re.DOTALL)

if new_content == content:
    # Pattern didn't match, try a different approach
    # Find line number
    lines = content.split('\n')
    start_line = None
    end_line = None
    for i, line in enumerate(lines):
        if 'function formatMessage(content)' in line:
            start_line = i
        if start_line and 'return formatted;' in line and i > start_line:
            # Find closing brace
            for j in range(i, min(i+5, len(lines))):
                if lines[j].strip() == '}':
                    end_line = j
                    break
            if end_line:
                break
    
    if start_line and end_line:
        new_lines = lines[:start_line] + [new_func] + lines[end_line+1:]
        new_content = '\n'.join(new_lines)
        print(f"Replaced lines {start_line} to {end_line}")
    else:
        print(f"Could not find function boundaries (start={start_line}, end={end_line})")
else:
    print("Regex replacement succeeded")

with open('src/web/chat.html', 'w') as f:
    f.write(new_content)

print("Done!")
