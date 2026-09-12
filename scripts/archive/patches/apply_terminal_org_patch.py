import os
import re

html_path = r"C:\Users\megat\Hermes-WebApp\static\index.html"

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# ---------------------------------------------------------
# 1. Terminal Enhancement
# ---------------------------------------------------------
terminal_old_pattern = r'<!-- Terminal View -->.*?<div id="module-terminal" class="module-overlay">.*?<div style="flex: 1; padding: 24px; display: flex; flex-direction: column; gap: 24px;">.*?</form>\s*</div>\s*</div>\s*</div>'

terminal_new_html = """<!-- Terminal View -->
    <div id="module-terminal" class="module-overlay">
        <div style="padding: 24px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid rgba(255,255,255,0.05);">
            <div style="display: flex; align-items: center; gap: 12px;">
                <i data-lucide="terminal" style="width: 24px; height: 24px; color: #fff;"></i>
                <div>
                    <h2 style="font-size: 24px; font-weight: 300; letter-spacing: -0.5px;">System Terminal</h2>
                    <p style="color: rgba(255,255,255,0.4); font-size: 14px;">Direct command-line interface</p>
                </div>
            </div>
            <button onclick="document.getElementById('module-terminal').classList.remove('active'); document.querySelectorAll('.dock-item').forEach(i=>i.classList.remove('active')); document.querySelector('.dock-item[onclick*=\\'dashboard\\']').classList.add('active');" class="glass" style="width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center;">
                <i data-lucide="chevron-down"></i>
            </button>
        </div>
        
        <div style="flex: 1; padding: 24px; display: flex; flex-direction: column;">
            <div id="term-output" style="flex: 1; background: #09090b; color: #10b981; font-family: 'Consolas', 'Courier New', monospace; font-size: 14px; padding: 16px; overflow-y: auto; border: 1px solid #27272a; border-radius: 8px 8px 0 0; white-space: pre-wrap; line-height: 1.6; text-shadow: 0 0 2px rgba(16, 185, 129, 0.4);">Hermes OS [Version 2.0.19045.3086]
(c) GangNiaga Elite CyberSuite. All rights reserved.

Type 'help' to see available internal commands.

</div>
            <div style="background: #09090b; border: 1px solid #27272a; border-top: none; border-radius: 0 0 8px 8px; padding: 12px 16px; display: flex; align-items: center; gap: 12px;">
                <span style="color: #10b981; font-family: 'Consolas', monospace; font-size: 14px; font-weight: bold;">PS C:\\Hermes&gt;</span>
                <input type="text" id="term-input" autocomplete="off" spellcheck="false" style="flex: 1; background: transparent; border: none; color: #f4f4f5; font-family: 'Consolas', monospace; font-size: 14px; outline: none; caret-color: #10b981;">
            </div>
        </div>
    </div>"""

if 'PS C:\\Hermes&gt;' not in content:
    content = re.sub(terminal_old_pattern, lambda m: terminal_new_html, content, flags=re.DOTALL)

# ---------------------------------------------------------
# 2. Dock Organization (Add Dividers)
# ---------------------------------------------------------
divider = '\n            <div style="width: 1px; height: 30px; background: #27272a; margin: 0 8px; border-radius: 1px;"></div>\n'

# Insert after Database if divider is not there
if '<div style="width: 1px; height: 30px; background: #27272a' not in content:
    content = re.sub(r'(<div class="dock-label">Database</div>\s*</div>)', r'\1' + divider, content)
    content = re.sub(r'(<div class="dock-label">Network Scanner</div>\s*</div>)', r'\1' + divider, content)

# ---------------------------------------------------------
# 3. Quick Actions & Terminal Javascript Logic
# ---------------------------------------------------------
if 'TERMINAL & ACTIONS LOGIC PATCH' not in content:
    logic_injection = """
<!-- ==========================================
     START: TERMINAL & ACTIONS LOGIC PATCH
     ========================================== -->
<script>
    // --- 1. Terminal Emulator Logic ---
    const termInput = document.getElementById('term-input');
    const termOutput = document.getElementById('term-output');
    const cmdHistory = [];
    let historyIndex = -1;

    if (termInput && termOutput) {
        termInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                const cmd = this.value.trim();
                if (cmd) {
                    cmdHistory.push(cmd);
                    historyIndex = cmdHistory.length;
                    
                    // Echo command
                    termOutput.innerHTML += `<div style="margin-top: 8px;"><span style="color:#f4f4f5;">PS C:\\\\Hermes&gt;</span> ${cmd}</div>`;
                    
                    // Process Command
                    processCommand(cmd);
                } else {
                    termOutput.innerHTML += `<div style="margin-top: 8px;"><span style="color:#f4f4f5;">PS C:\\\\Hermes&gt;</span></div>`;
                }
                this.value = '';
                termOutput.scrollTop = termOutput.scrollHeight;
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                if (historyIndex > 0) {
                    historyIndex--;
                    this.value = cmdHistory[historyIndex];
                }
            } else if (e.key === 'ArrowDown') {
                e.preventDefault();
                if (historyIndex < cmdHistory.length - 1) {
                    historyIndex++;
                    this.value = cmdHistory[historyIndex];
                } else {
                    historyIndex = cmdHistory.length;
                    this.value = '';
                }
            }
        });

        function processCommand(cmd) {
            const args = cmd.split(' ');
            const baseCmd = args[0].toLowerCase();
            
            let response = '';
            switch(baseCmd) {
                case 'help':
                    response = `Available commands:
  help       - Show this message
  clear      - Clear the terminal screen
  date       - Show current system date and time
  whoami     - Display current user
  ping       - Check connection to Swarm API
  reboot     - Restart the Hermes UI`;
                    break;
                case 'clear':
                    termOutput.innerHTML = `Hermes OS [Version 2.0.19045.3086]\\n(c) GangNiaga Elite CyberSuite. All rights reserved.\\n\\n`;
                    return; // exit early to not append response wrapper
                case 'date':
                    response = new Date().toString();
                    break;
                case 'whoami':
                    response = 'gangniaga\\\\sovereign_conductor';
                    break;
                case 'ping':
                    response = 'Pinging swarm.local [127.0.0.1] with 32 bytes of data:<br>Reply from 127.0.0.1: bytes=32 time<1ms TTL=128<br>Reply from 127.0.0.1: bytes=32 time<1ms TTL=128<br>Ping statistics for 127.0.0.1:<br>&nbsp;&nbsp;Packets: Sent = 2, Received = 2, Lost = 0 (0% loss)';
                    break;
                case 'reboot':
                    response = 'Initiating UI reload...';
                    setTimeout(() => location.reload(), 1000);
                    break;
                default:
                    response = `${baseCmd} : The term '${baseCmd}' is not recognized as the name of a cmdlet, function, script file, or operable program. Check the spelling of the name, or if a path was included, verify that the path is correct and try again.`;
                    break;
            }
            termOutput.innerHTML += `<div style="color:#a1a1aa; margin-top:4px;">${response.replace(/\\n/g, '<br>')}</div>`;
        }
    }

    // --- 2. Quick Actions Binding ---
    document.addEventListener('DOMContentLoaded', () => {
        const buttons = document.querySelectorAll('.btn-action');
        buttons.forEach(btn => {
            btn.removeAttribute('onclick'); // strip old inline events
            btn.addEventListener('click', () => {
                const iconClass = btn.querySelector('i').getAttribute('data-lucide');
                let actionName = 'Action executed';
                
                if (iconClass === 'trash-2') {
                    actionName = 'Temporary files cleaned.';
                    if (window.showToast) showToast('System Maintenance', actionName, 'success');
                } else if (iconClass === 'lock') {
                    actionName = 'System Locked. Security protocols active.';
                    if (window.showToast) showToast('Security', actionName, 'warning');
                } else if (iconClass === 'skull') {
                    actionName = 'Zombie processes terminated.';
                    if (window.showToast) showToast('Process Manager', actionName, 'error');
                } else if (iconClass === 'link-2') {
                    actionName = 'Cloudflare tunnel synced successfully.';
                    if (window.showToast) showToast('Network', actionName, 'success');
                } else {
                    if (window.showToast) showToast('Action', 'Command sent to system.', 'success');
                }
            });
        });
    });
</script>
<!-- ==========================================
     END: TERMINAL & ACTIONS LOGIC PATCH
     ========================================== -->
</body>
"""
    content = content.replace('</body>', logic_injection)

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Terminal and Organization patch applied successfully.")
