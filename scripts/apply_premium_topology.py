import os
import re

html_path = r"C:\Users\megat\Hermes-WebApp\static\index.html"

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

if 'PREMIUM ZINC TOPOLOGY PATCH' in content:
    print("Premium patch already applied.")
    exit(0)

injection = """
<!-- ==========================================
     START: PREMIUM ZINC TOPOLOGY PATCH
     ========================================== -->
<style>
    /* Reset all generic glow and slop from previous designs */
    
    .topology-node {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 8px; /* More breathing room */
        position: relative;
        z-index: 2;
    }

    .topology-icon {
        width: 42px !important;
        height: 42px !important;
        border-radius: 6px !important; /* Sharper corners */
        background: #09090b !important; /* Zinc 950 */
        border: 1px solid #27272a !important; /* Zinc 800 */
        display: flex;
        align-items: center;
        justify-content: center;
        transition: border-color 0.2s, background 0.2s;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5) !important;
    }

    .topology-icon i {
        color: #a1a1aa !important; /* Zinc 400 */
        width: 18px !important;
        height: 18px !important;
        transition: color 0.2s;
    }

    .topology-node:hover .topology-icon {
        border-color: #52525b !important; /* Zinc 600 */
        background: #18181b !important; /* Zinc 900 */
    }

    .topology-node:hover .topology-icon i {
        color: #f4f4f5 !important; /* Zinc 100 */
    }

    .topology-node span {
        font-family: 'Inter', sans-serif !important;
        font-size: 9px !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        color: #71717a !important; /* Zinc 500 */
    }

    .topology-line {
        flex: 1;
        height: 1px;
        background: repeating-linear-gradient(
            to right,
            #3f3f46,
            #3f3f46 4px,
            transparent 4px,
            transparent 8px
        ) !important; /* Dotted/Dashed zinc line instead of gradient */
        position: relative;
        top: -8px; /* Align perfectly with the icons */
        z-index: 1;
        opacity: 0.5;
    }

    .topology-line::after {
        display: none !important; /* Remove old arrow */
    }

    /* Emerald Pulse for active status dots */
    @keyframes emerald-pulse {
        0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.4); }
        70% { box-shadow: 0 0 0 4px rgba(16, 185, 129, 0); }
        100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }

    .topology-node .status-dot {
        width: 6px !important;
        height: 6px !important;
        background-color: #10b981 !important; /* Emerald 500 */
        border: none !important;
        animation: emerald-pulse 2s infinite;
    }
</style>
<!-- ==========================================
     END: PREMIUM ZINC TOPOLOGY PATCH
     ========================================== -->
</body>
"""

new_content = content.replace('</body>', injection)

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Premium Zinc topology patch applied successfully to index.html.")
