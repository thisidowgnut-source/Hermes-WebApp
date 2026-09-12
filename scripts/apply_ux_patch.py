import os

html_path = r"C:\Users\megat\Hermes-WebApp\static\index.html"

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Make sure not to apply it twice
if 'id="toast-container"' in content:
    print("Patch already applied.")
    exit(0)

injection = """
<!-- ==========================================
     START: UX IMPROVEMENT PATCH
     ========================================== -->
<style>
    /* Typography Scaling for Better Readability */
    body { font-size: 13px !important; }
    .module-title { font-size: 12px !important; color: rgba(255,255,255,0.8) !important; letter-spacing: 0.15em !important; }
    .btn-action { font-size: 11px !important; }
    .dock-label { font-size: 11px !important; background: rgba(18, 15, 23, 0.98) !important; padding: 6px 12px !important; }
    .log-agent, .log-system, .log-error { font-size: 12px !important; }
    #status-text { font-size: 10px !important; color: rgba(255,255,255,0.6) !important; }
    
    /* Command Palette */
    #cmd-palette-overlay {
        position: fixed; inset: 0; background: rgba(0,0,0,0.6); backdrop-filter: blur(8px);
        z-index: 9999; display: none; align-items: flex-start; justify-content: center; padding-top: 15vh;
        opacity: 0; transition: opacity 0.2s;
    }
    #cmd-palette-overlay.active { display: flex; opacity: 1; }
    #cmd-palette {
        width: 100%; max-width: 500px; background: rgba(18, 15, 23, 0.95);
        border: 1px solid rgba(255,255,255,0.1); border-radius: 12px;
        box-shadow: 0 20px 40px rgba(0,0,0,0.5); overflow: hidden;
    }
    #cmd-input {
        width: 100%; padding: 16px; background: transparent; border: none;
        border-bottom: 1px solid rgba(255,255,255,0.1); color: #fff; font-size: 14px; outline: none;
    }
    .cmd-item {
        padding: 12px 16px; cursor: pointer; display: flex; align-items: center; gap: 10px; color: rgba(255,255,255,0.6); font-size: 12px;
    }
    .cmd-item:hover, .cmd-item.selected {
        background: rgba(255,255,255,0.08); color: #fff;
    }
    .cmd-shortcut {
        margin-left: auto; font-size: 10px; background: rgba(255,255,255,0.15); padding: 2px 6px; border-radius: 4px;
    }

    /* Toast Notifications */
    #toast-container {
        position: fixed; bottom: 90px; right: 20px; z-index: 10000;
        display: flex; flex-direction: column; gap: 10px; pointer-events: none;
    }
    .toast {
        background: rgba(18, 15, 23, 0.95); border: 1px solid rgba(255,255,255,0.15);
        color: #fff; padding: 12px 16px; border-radius: 8px; font-size: 11px;
        box-shadow: 0 8px 20px rgba(0,0,0,0.4);
        transform: translateX(120%); transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.3s;
        display: flex; align-items: center; gap: 10px;
    }
    .toast.show { transform: translateX(0); }
    .toast.success { border-left: 3px solid #10b981; }
    .toast.error { border-left: 3px solid #ef4444; }
    .toast.info { border-left: 3px solid #3b82f6; }
</style>

<!-- DOMPurify for XSS Protection -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/dompurify/3.0.6/purify.min.js"></script>

<!-- Toast Container -->
<div id="toast-container"></div>

<!-- Command Palette -->
<div id="cmd-palette-overlay" onclick="closeCmdPalette(event)">
    <div id="cmd-palette" onclick="event.stopPropagation()">
        <input type="text" id="cmd-input" placeholder="Search modules or commands (e.g. 'Terminal')..." autocomplete="off">
        <div id="cmd-results"></div>
    </div>
</div>

<script>
    // --- Toast System ---
    function showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        let icon = 'info';
        if(type==='success') icon = 'check-circle';
        if(type==='error') icon = 'alert-triangle';
        
        // Use DOMPurify if available
        let safeMsg = typeof DOMPurify !== 'undefined' ? DOMPurify.sanitize(message) : message;
        
        toast.innerHTML = `<i data-lucide="${icon}" style="width:14px;height:14px;"></i> <span>${safeMsg}</span>`;
        container.appendChild(toast);
        lucide.createIcons({ root: toast });
        
        setTimeout(() => toast.classList.add('show'), 10);
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    // --- Command Palette System ---
    const cmdModules = [
        { name: 'Root Shell', id: 'terminal', icon: 'square-terminal' },
        { name: 'Process Monitor', id: 'monitor', icon: 'list-tree' },
        { name: 'Vision Node (Browser)', id: 'browser', icon: 'globe' },
        { name: 'Kanban Tasks', id: 'kanban', icon: 'kanban' },
        { name: 'File Explorer', id: 'files', icon: 'folder' },
        { name: 'Swarm Control Panel', id: 'swarm', icon: 'bot' },
        { name: 'Voice Terminal', id: 'audio', icon: 'mic' },
        { name: 'Network Scanner', id: 'netscan', icon: 'wifi' },
        { name: 'Threat Sentinel', id: 'threat', icon: 'shield-alert' },
        { name: 'Code Editor', id: 'editor', icon: 'file-code' },
        { name: 'Services Manager', id: 'services', icon: 'server' },
        { name: 'Forensics Suite', id: 'forensics', icon: 'shield-check' },
        { name: 'Workflow Engine', id: 'workflow', icon: 'workflow' },
        { name: 'Obsidian Graph', id: 'obsgraph', icon: 'git-fork' }
    ];

    let cmdSelectedIndex = 0;

    function renderCmdResults(query = '') {
        const resultsEl = document.getElementById('cmd-results');
        const filtered = cmdModules.filter(m => m.name.toLowerCase().includes(query.toLowerCase()));
        
        if (filtered.length === 0) {
            resultsEl.innerHTML = `<div style="padding: 16px; text-align: center; color: rgba(255,255,255,0.4); font-size: 12px;">No modules found</div>`;
            return;
        }

        resultsEl.innerHTML = filtered.map((m, idx) => `
            <div class="cmd-item ${idx === cmdSelectedIndex ? 'selected' : ''}" onclick="openModuleFromCmd('${m.id}')" data-idx="${idx}">
                <i data-lucide="${m.icon}" style="width:14px;height:14px;"></i>
                <span>Open ${m.name}</span>
                ${idx === 0 && query === '' ? '<span class="cmd-shortcut">↵</span>' : ''}
            </div>
        `).join('');
        lucide.createIcons({ root: resultsEl });
    }

    function openModuleFromCmd(moduleId) {
        closeCmdPalette();
        const mockBtn = document.querySelector(`.dock-item[onclick*="'${moduleId}'"]`);
        if(mockBtn) openModule(moduleId, mockBtn);
        else console.log('Module btn not found', moduleId);
        showToast(`Opened ${moduleId}`, 'success');
    }

    function closeCmdPalette(e) {
        document.getElementById('cmd-palette-overlay').classList.remove('active');
        document.getElementById('cmd-input').blur();
    }

    document.addEventListener('keydown', (e) => {
        // Toggle Command Palette (Cmd+K / Ctrl+K)
        if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
            e.preventDefault();
            const overlay = document.getElementById('cmd-palette-overlay');
            if (overlay.classList.contains('active')) {
                closeCmdPalette();
            } else {
                overlay.classList.add('active');
                document.getElementById('cmd-input').value = '';
                cmdSelectedIndex = 0;
                renderCmdResults('');
                setTimeout(() => document.getElementById('cmd-input').focus(), 100);
            }
        }

        // Navigate Command Palette
        const overlay = document.getElementById('cmd-palette-overlay');
        if (overlay.classList.contains('active')) {
            const results = document.querySelectorAll('.cmd-item');
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                cmdSelectedIndex = (cmdSelectedIndex + 1) % results.length;
                renderCmdResults(document.getElementById('cmd-input').value);
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                cmdSelectedIndex = (cmdSelectedIndex - 1 + results.length) % results.length;
                renderCmdResults(document.getElementById('cmd-input').value);
            } else if (e.key === 'Enter') {
                e.preventDefault();
                const selected = document.querySelector('.cmd-item.selected');
                if (selected) selected.click();
            } else if (e.key === 'Escape') {
                closeCmdPalette();
            }
        }
    });

    // Override fetch errors to use toasts
    const originalFetch = window.fetch;
    window.fetch = async function(...args) {
        try {
            const res = await originalFetch(...args);
            if(!res.ok) {
                // Ignore chatty polling errors for toast
                if(args[0] && typeof args[0] === 'string' && !args[0].includes('/api/system/metrics')) {
                    showToast(`API Error: ${res.status}`, 'error');
                }
            }
            return res;
        } catch(err) {
            if(args[0] && typeof args[0] === 'string' && !args[0].includes('/api/system/metrics')) {
                showToast(`Network Error: ${err.message}`, 'error');
            }
            throw err;
        }
    };
    
    // Announce startup
    setTimeout(() => {
        showToast('Sovereign Node Ready (Press Cmd+K for Command Palette)', 'success');
    }, 1500);

</script>
<!-- ==========================================
     END: UX IMPROVEMENT PATCH
     ========================================== -->
</body>
"""

new_content = content.replace('</body>', injection)

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("UX patch applied successfully to index.html.")
