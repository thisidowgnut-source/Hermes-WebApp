import os

html_path = r"C:\Users\megat\Hermes-WebApp\static\index.html"

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

if 'MAGIC UI BENTO PORT' in content:
    print("MagicUI patch already applied.")
    exit(0)

injection = """
<!-- ==========================================
     START: MAGIC UI BENTO PORT
     ========================================== -->
<style>
    /* 1. Base Bento Grid Layout Enhancements */
    /* Enhance the existing main grid to match MagicUI's precise spacing */
    main > div[style*="grid-template-columns"] {
        gap: 16px !important;
    }

    /* 2. MagicUI Bento Card Core (Applied to .glass) */
    .glass {
        position: relative !important;
        border-radius: 16px !important; /* Slightly more rounded for MagicUI feel */
        background: rgba(9, 9, 11, 0.7) !important; /* Zinc 950 */
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        overflow: hidden !important;
        /* Make sure child elements don't block the background glow */
        z-index: 1;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5) !important;
    }

    /* 3. The Magic Spotlight Glow (Border) */
    .glass::before {
        content: "";
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        border-radius: inherit;
        padding: 1px; /* border width */
        background: radial-gradient(
            400px circle at var(--mouse-x, -400px) var(--mouse-y, -400px),
            rgba(255, 255, 255, 0.3),
            transparent 40%
        ) !important;
        /* Mask to only show the border */
        -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
        -webkit-mask-composite: xor;
        mask-composite: exclude;
        pointer-events: none;
        z-index: -1;
    }

    /* 4. The Magic Spotlight Glow (Inner Background) */
    .glass::after {
        content: "";
        position: absolute;
        inset: 0;
        background: radial-gradient(
            400px circle at var(--mouse-x, -400px) var(--mouse-y, -400px),
            rgba(255, 255, 255, 0.04),
            transparent 40%
        ) !important;
        z-index: -1;
        pointer-events: none;
        opacity: 0;
        transition: opacity 0.3s;
    }

    .glass:hover::after {
        opacity: 1;
    }

    /* Subtle translation on hover to give physical feel */
    .glass:hover {
        transform: translateY(-2px);
    }
</style>

<script>
    // MagicUI Bento Grid Spotlight Logic
    document.querySelectorAll('.glass').forEach(card => {
        card.addEventListener('mousemove', e => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            card.style.setProperty('--mouse-x', `${x}px`);
            card.style.setProperty('--mouse-y', `${y}px`);
        });
        
        // Reset when mouse leaves so it doesn't stay stuck on the edge
        card.addEventListener('mouseleave', () => {
            card.style.setProperty('--mouse-x', `-400px`);
            card.style.setProperty('--mouse-y', `-400px`);
        });
    });
</script>
<!-- ==========================================
     END: MAGIC UI BENTO PORT
     ========================================== -->
</body>
"""

new_content = content.replace('</body>', injection)

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("MagicUI Bento port applied successfully to index.html.")
