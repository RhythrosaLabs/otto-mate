#!/usr/bin/env python3
"""Fix the formatMessage function in chat.html using simple string replace"""

# Read the file
with open('src/web/chat.html', 'r') as f:
    content = f.read()

# Find the start of the function
start_marker = 'function formatMessage(content) {'
start_idx = content.find(start_marker)

if start_idx == -1:
    print("Could not find formatMessage function")
    exit(1)

# Find the end - look for the next function definition after formatMessage
# The function ends with "return formatted;" followed by closing brace
search_start = start_idx + len(start_marker)
end_marker = 'return formatted;'
end_idx = content.find(end_marker, search_start)

if end_idx == -1:
    print("Could not find 'return formatted;'")
    exit(1)

# Find the closing brace after return formatted;
brace_idx = content.find('}', end_idx)
if brace_idx == -1:
    print("Could not find closing brace")
    exit(1)

# New function
new_function = '''function formatMessage(content) {
            let formatted = content;
            const urls = [];
            // Extract URLs first
            formatted = formatted.replace(/(https?:\\/\\/[^\\s<>"']+|\\/files\\/[a-f0-9]+)/gi, function(url) {
                urls.push(url);
                return '__URL_' + (urls.length - 1) + '__';
            });
            // Escape HTML
            formatted = escapeHtml(formatted);
            // Markdown
            formatted = formatted
                .replace(/\\*\\*(.+?)\\*\\*/g, '<strong>$1</strong>')
                .replace(/\\*(.+?)\\*/g, '<em>$1</em>')
                .replace(/`(.+?)`/g, '<code>$1</code>')
                .replace(/\\n/g, '<br>');
            // Render URLs
            urls.forEach(function(url, i) {
                var html;
                var lower = url.toLowerCase();
                if (lower.match(/\\.(png|jpg|jpeg|gif|webp|svg|bmp)(\\?|$)/) || lower.indexOf('replicate.delivery') >= 0) {
                    html = '<div class="media-embed"><img src="' + url + '" style="max-width:100%;border-radius:12px"/></div>';
                } else if (lower.match(/\\.(mp4|webm|mov)(\\?|$)/)) {
                    html = '<div class="media-embed"><video controls style="max-width:100%;border-radius:12px"><source src="' + url + '"></video></div>';
                } else if (lower.match(/\\.(mp3|wav|ogg)(\\?|$)/)) {
                    html = '<div class="media-embed"><audio controls><source src="' + url + '"></audio></div>';
                } else if (url.indexOf('/files/') === 0) {
                    html = '<div class="media-embed"><img src="' + url + '" style="max-width:100%;border-radius:12px"/></div>';
                } else {
                    html = '<a href="' + url + '" target="_blank" style="color:var(--accent)">' + url + '</a>';
                }
                formatted = formatted.replace('__URL_' + i + '__', html);
            });
            return formatted;
        }'''

# Replace
new_content = content[:start_idx] + new_function + content[brace_idx+1:]

with open('src/web/chat.html', 'w') as f:
    f.write(new_content)

print(f"Replaced function from position {start_idx} to {brace_idx}")
print("Done!")
