import os
import re

html_path = r"C:\Users\megat\Hermes-WebApp\static\index.html"

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the terminal ID bug
content = content.replace('id="module-terminal"', 'id="mod-terminal"')
# Also fix the close button in terminal
content = content.replace("document.getElementById('module-terminal').classList.remove('active');", "document.getElementById('mod-terminal').classList.remove('active');")

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed module-terminal ID bug.")
