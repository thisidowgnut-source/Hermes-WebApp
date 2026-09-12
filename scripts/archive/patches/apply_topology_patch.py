import os

html_path = r"C:\Users\megat\Hermes-WebApp\static\index.html"

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

if 'TOPOLOGY ANIMATION PATCH' in content:
    print("Topology patch already applied.")
    exit(0)

injection = """
<!-- ==========================================
     START: TOPOLOGY ANIMATION PATCH
     ========================================== -->
<style>
    /* 1. Animated Data Flow lines */
    @keyframes data-flow-pulse {
        0% { background-position: -200% 0; }
        100% { background-position: 200% 0; }
    }
    
    .topology-line {
        background: linear-gradient(90deg, 
            rgba(255,255,255,0.05) 0%, 
            rgba(6, 182, 212, 0.6) 50%, 
            rgba(255,255,255,0.05) 100%
        ) !important;
        background-size: 200% 100% !important;
        animation: data-flow-pulse 2s infinite linear !important;
        height: 2px !important;
        box-shadow: 0 0 5px rgba(6, 182, 212, 0.3) !important;
        border: none !important;
        opacity: 0.8;
    }
    .topology-line::after {
        display: none !important; /* Remove old ugly arrow */
    }

    /* 2. Enhanced Topology Nodes */
    .topology-icon {
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.1), 0 4px 10px rgba(0,0,0,0.5) !important;
        background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.02) 100%) !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
        border-radius: 10px !important;
        transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
    }

    .topology-node:hover .topology-icon {
        transform: translateY(-4px) scale(1.15) !important;
        box-shadow: 0 0 20px rgba(6, 182, 212, 0.5) !important;
        border-color: rgba(6, 182, 212, 0.8) !important;
        background: linear-gradient(135deg, rgba(6, 182, 212, 0.2) 0%, rgba(255,255,255,0.05) 100%) !important;
    }
    
    .topology-node:hover i {
        color: #fff !important;
        filter: drop-shadow(0 0 8px rgba(255,255,255,0.9)) !important;
        transform: scale(1.1);
        transition: transform 0.2s;
    }

    /* 3. Text & Dots below icons */
    .topology-node span {
        font-weight: 600 !important;
        letter-spacing: 0.5px !important;
        color: rgba(255,255,255,0.6) !important;
        transition: color 0.3s !important;
    }
    
    .topology-node:hover span {
        color: rgba(255,255,255,0.95) !important;
        text-shadow: 0 0 5px rgba(6, 182, 212, 0.5);
    }
</style>
<!-- ==========================================
     END: TOPOLOGY ANIMATION PATCH
     ========================================== -->
</body>
"""

new_content = content.replace('</body>', injection)

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Topology visual patch applied successfully to index.html.")
