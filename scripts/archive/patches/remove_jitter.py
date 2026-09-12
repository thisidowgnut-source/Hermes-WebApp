import os
import re

html_path = r"C:\Users\megat\Hermes-WebApp\static\index.html"

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Remove transform from .glass:hover which causes edge jitter
content = re.sub(r'\.glass:hover\s*\{\s*transform:\s*translateY\(-2px\);\s*\}', '', content)

# There might also be a transition conflict. Let's make sure .glass doesn't jump.
# In apply_colorful_patch, I might have added it but I removed colorful patch.
# Wait, let's just use regex to strip out any hover transform on .glass.

content = re.sub(r'transform:\s*translateY\([^)]+\)\s*;?', '', content)

# Actually, stripping ALL transforms might break the dock or overlays.
# Let's be precise. I will only remove it from .glass:hover in the magicui block.
# The user said "cursor goyang2" which could also be the custom cursor if there is one. 
# Let me look for custom cursor css.

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Removed transforms that might cause jitter.")
