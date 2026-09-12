import os

html_path = r"C:\Users\megat\Hermes-WebApp\static\index.html"

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

if 'VIBRANT & COLORFUL UX PATCH' in content:
    print("Colorful patch already applied.")
    exit(0)

injection = """
<!-- ==========================================
     START: VIBRANT & COLORFUL UX PATCH
     ========================================== -->
<style>
    /* 1. Gradient Text & Glows for Headers */
    header h1 {
        background: linear-gradient(135deg, #e0e0e0 0%, #fff 100%);
        -webkit-background-clip: text;
    }
    
    .logo-pulse {
        color: #a855f7 !important;
        filter: drop-shadow(0 0 10px rgba(168, 85, 247, 0.6)) !important;
    }

    /* 2. Premium Bento Box Interaction & Ambient Tinting */
    .glass {
        transition: transform 0.4s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.4s ease, border-color 0.4s ease, background 0.4s ease !important;
    }
    
    .glass:hover {
        transform: translateY(-3px) scale(1.01) !important;
        background: rgba(255, 255, 255, 0.05) !important;
        border-color: rgba(255, 255, 255, 0.15) !important;
    }

    /* Assigning Ambient Neon Colors to Bento Boxes using existing structure */
    /* System Metrics Box */
    .glass:has(.ring-gauge) {
        --glow-color: 16, 185, 129; /* Emerald */
    }
    .glass:has(.ring-gauge):hover {
        box-shadow: 0 10px 30px -10px rgba(16, 185, 129, 0.3) !important;
        border-color: rgba(16, 185, 129, 0.3) !important;
    }

    /* Swarm Box */
    #swarm-bento-card {
        --glow-color: 168, 85, 247; /* Purple */
    }
    #swarm-bento-card:hover {
        box-shadow: 0 10px 30px -10px rgba(168, 85, 247, 0.4) !important;
        border-color: rgba(168, 85, 247, 0.4) !important;
    }

    /* Agent Stream Box */
    .glass:has(#agent-logs) {
        --glow-color: 59, 130, 246; /* Blue */
    }
    .glass:has(#agent-logs):hover {
        box-shadow: 0 10px 30px -10px rgba(59, 130, 246, 0.3) !important;
        border-color: rgba(59, 130, 246, 0.3) !important;
    }
    
    /* Topology Box */
    .glass:has(.topology-node) {
        --glow-color: 6, 182, 212; /* Cyan */
    }
    .glass:has(.topology-node):hover {
        box-shadow: 0 10px 30px -10px rgba(6, 182, 212, 0.3) !important;
        border-color: rgba(6, 182, 212, 0.3) !important;
    }

    /* 3. Colorful Quick Action Buttons on Hover */
    .btn-action {
        transition: all 0.3s ease !important;
    }
    /* Clean Temp (Red) */
    .btn-action:has(.lucide-trash-2):hover {
        background: rgba(239, 68, 68, 0.1) !important;
        border-color: rgba(239, 68, 68, 0.4) !important;
        color: #f87171 !important;
        box-shadow: 0 0 15px rgba(239, 68, 68, 0.2);
    }
    /* Lock PC (Amber) */
    .btn-action:has(.lucide-lock):hover {
        background: rgba(245, 158, 11, 0.1) !important;
        border-color: rgba(245, 158, 11, 0.4) !important;
        color: #fbbf24 !important;
        box-shadow: 0 0 15px rgba(245, 158, 11, 0.2);
    }
    /* Kill Zombies (Pink) */
    .btn-action:has(.lucide-skull):hover {
        background: rgba(236, 72, 153, 0.1) !important;
        border-color: rgba(236, 72, 153, 0.4) !important;
        color: #f472b6 !important;
        box-shadow: 0 0 15px rgba(236, 72, 153, 0.2);
    }
    /* Sync Tunnel (Emerald) */
    .btn-action:has(.lucide-link-2):hover {
        background: rgba(16, 185, 129, 0.1) !important;
        border-color: rgba(16, 185, 129, 0.4) !important;
        color: #34d399 !important;
        box-shadow: 0 0 15px rgba(16, 185, 129, 0.2);
    }

    /* 4. Dock Vibrant Active States */
    .dock-item {
        transition: transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1), background 0.3s, color 0.3s !important;
    }
    .dock-item.active {
        background: linear-gradient(180deg, rgba(255,255,255,0.12) 0%, rgba(255,255,255,0.02) 100%) !important;
        border-top: 1px solid rgba(255,255,255,0.4) !important;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.1), 0 -4px 15px rgba(255,255,255,0.05) !important;
    }
    .dock-item:hover {
        transform: translateY(-6px) scale(1.1) !important;
        z-index: 10;
    }
    .glow-indicator {
        background: linear-gradient(90deg, transparent, #a855f7, #3b82f6, transparent) !important;
        height: 3px !important;
        width: 30px !important;
        filter: blur(2px) !important;
        bottom: -8px !important;
        opacity: 0.8 !important;
    }

    /* 5. Cyberpunk Scrollbars */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: rgba(0,0,0,0.2); border-radius: 4px; }
    ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.15); border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(168, 85, 247, 0.6); }

    /* 6. Form Inputs & Textareas Focus Glow */
    input:focus, textarea:focus {
        border-color: rgba(168, 85, 247, 0.5) !important;
        box-shadow: 0 0 15px rgba(168, 85, 247, 0.2) !important;
        background: rgba(255,255,255,0.05) !important;
    }
</style>

<script>
    // Add dynamic colors to ring gauge based on usage thresholds
    function updateRingColors() {
        // CPU
        const cpuText = document.getElementById('cpu-val');
        if(cpuText) {
            let val = parseFloat(cpuText.textContent);
            if(!isNaN(val)) {
                let color = val > 80 ? '#ef4444' : val > 50 ? '#f59e0b' : '#10b981';
                document.getElementById('cpu-ring').setAttribute('stroke', color);
                cpuText.style.fill = color;
            }
        }
        // RAM
        const ramText = document.getElementById('ram-val');
        if(ramText) {
            let val = parseFloat(ramText.textContent);
            if(!isNaN(val)) {
                let color = val > 80 ? '#ef4444' : val > 60 ? '#f59e0b' : '#3b82f6';
                document.getElementById('ram-ring').setAttribute('stroke', color);
                ramText.style.fill = color;
            }
        }
        // Disk
        const diskText = document.getElementById('disk-val');
        if(diskText) {
            let val = parseFloat(diskText.textContent);
            if(!isNaN(val)) {
                let color = val > 90 ? '#ef4444' : val > 75 ? '#f59e0b' : '#a855f7';
                document.getElementById('disk-ring').setAttribute('stroke', color);
                diskText.style.fill = color;
            }
        }
    }

    // Attempt to hook into the existing metrics update loop if there is one
    // We just poll every 2 seconds to keep the rings colored
    setInterval(updateRingColors, 2000);
    
    // Add pulsing glow to the status dot text
    const statusText = document.getElementById('status-text');
    if(statusText) {
        statusText.style.color = '#a3e635';
        statusText.style.textShadow = '0 0 8px rgba(163, 230, 53, 0.4)';
    }
</script>
<!-- ==========================================
     END: VIBRANT & COLORFUL UX PATCH
     ========================================== -->
</body>
"""

new_content = content.replace('</body>', injection)

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Vibrant colorful patch applied successfully to index.html.")
