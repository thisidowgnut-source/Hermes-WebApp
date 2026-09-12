import os
import re

html_path = r"C:\Users\megat\Hermes-WebApp\static\index.html"

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

if 'SOLID BENTO PATCH' in content:
    print("Solid patch already applied.")
    exit(0)

injection = """
<!-- ==========================================
     START: SOLID BENTO PATCH (NO GLASS)
     ========================================== -->
<style>
    /* Turn off glassmorphism and switch to solid OLED/Matte look */
    .glass {
        background: #09090b !important; /* Solid Zinc 950 */
        backdrop-filter: none !important;
        -webkit-backdrop-filter: none !important;
        border: 1px solid #27272a !important; /* Solid Zinc 800 */
        box-shadow: none !important; /* Flat look */
        border-radius: 8px !important; /* Sharper corners */
    }

    /* Keep the MagicUI border tracking if it exists, but remove inner glow */
    .glass::after {
        display: none !important;
    }
    
    /* Make the body background slightly lighter so the boxes contrast properly */
    body {
        background: #000000 !important; /* Pure black for contrast against Zinc 950 */
    }

    /* Terminal background adjustments */
    .module-overlay {
        background: #000000 !important; /* Solid black instead of transparent */
        backdrop-filter: none !important;
    }
</style>
<!-- ==========================================
     END: SOLID BENTO PATCH (NO GLASS)
     ========================================== -->
</body>
"""

new_content = content.replace('</body>', injection)

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Solid bento patch applied successfully to index.html.")
