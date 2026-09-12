import os

html_path = r"C:\Users\megat\Hermes-WebApp\static\index.html"

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Make sure not to apply it twice
if 'MOBILE-FIRST OPTIMIZATION PATCH' in content:
    print("Mobile patch already applied.")
    exit(0)

injection = """
<!-- ==========================================
     START: MOBILE-FIRST OPTIMIZATION PATCH
     ========================================== -->
<style>
    /* 1. Mobile-First Quick Actions Grid */
    .quick-actions-grid {
        display: grid !important;
        grid-template-columns: repeat(2, 1fr) !important;
        gap: 8px !important;
        flex-shrink: 0;
    }
    @media (min-width: 640px) {
        .quick-actions-grid {
            grid-template-columns: repeat(4, 1fr) !important;
        }
    }

    /* 2. Dock Mobile Overflow Fix */
    .dock-outer {
        max-width: 100vw;
        overflow-x: auto;
        -ms-overflow-style: none; 
        scrollbar-width: none;
        padding-left: 10px;
        padding-right: 10px;
    }
    .dock-outer::-webkit-scrollbar {
        display: none;
    }
    .dock-panel {
        width: max-content;
        margin: 0 auto;
        padding: 8px 12px !important;
    }

    /* 3. Header Responsiveness */
    @media (max-width: 640px) {
        header {
            flex-direction: column !important;
            align-items: flex-start !important;
            gap: 16px !important;
        }
        header > div:last-child {
            width: 100%;
            justify-content: space-between;
        }
        .text-rotate {
            font-size: 16px !important;
        }
    }

    /* 4. Command Palette Mobile Fix */
    @media (max-width: 640px) {
        #cmd-palette {
            width: 95% !important;
            max-width: 95% !important;
        }
        #cmd-input {
            /* 16px prevents iOS Safari auto-zoom on focus */
            font-size: 16px !important;
        }
    }

    /* 5. Modules Inner Padding for Mobile */
    @media (max-width: 640px) {
        main {
            padding: 12px 12px 100px 12px !important; /* extra padding at bottom for dock scroll */
        }
        .glass {
            padding: 12px !important;
        }
    }

    /* 6. Touch Targets */
    @media (max-width: 640px) {
        .btn-action {
            min-height: 40px; /* larger touch target */
        }
        .dock-item {
            width: 48px !important;
            height: 48px !important;
        }
    }
    
    /* 7. Forms / Input Mobile Fixes */
    @media (max-width: 640px) {
        form, .glass > div {
            flex-direction: column !important;
        }
        input, select, textarea {
            width: 100% !important;
        }
        .ring-gauge svg {
            width: 40px !important;
            height: 40px !important;
        }
    }
</style>

<script>
    // Retrofit the Quick Actions Grid to use the new mobile-first class
    const quickActions = Array.from(document.querySelectorAll('main > div')).find(el => el.style.cssText.includes('repeat(4, 1fr)'));
    if (quickActions) {
        quickActions.classList.add('quick-actions-grid');
        quickActions.style.gridTemplateColumns = ''; // Strip inline style to let CSS take over
    }
    
    // Ensure form flex containers are allowed to wrap/stack properly
    const flexRows = document.querySelectorAll('div[style*="display: flex; gap: 8px;"]');
    flexRows.forEach(row => {
        if (!row.classList.contains('quick-actions-grid')) {
            row.style.flexWrap = 'wrap';
        }
    });
</script>
<!-- ==========================================
     END: MOBILE-FIRST OPTIMIZATION PATCH
     ========================================== -->
</body>
"""

new_content = content.replace('</body>', injection)

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Mobile-first patch applied successfully to index.html.")
