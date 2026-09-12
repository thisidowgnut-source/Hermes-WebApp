import os
import re

html_path = r"C:\Users\megat\Hermes-WebApp\static\index.html"

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Remove Colorful Patch
content = re.sub(r'<!-- ==========================================\s*START: VIBRANT & COLORFUL UX PATCH.*?END: VIBRANT & COLORFUL UX PATCH\s*========================================== -->', '', content, flags=re.DOTALL)

# Remove Topology Patch
content = re.sub(r'<!-- ==========================================\s*START: TOPOLOGY ANIMATION PATCH.*?END: TOPOLOGY ANIMATION PATCH\s*========================================== -->', '', content, flags=re.DOTALL)

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Reverted ugly patches.")
