/**
 * Hermes OS — Remote Operations Mission Control
 * Single-writer AGY orchestration, durable cursor sync, and streaming updates.
 */
(function (window) {
    'use strict';

    // Safe UUID generation
    function generateUUID() {
        if (typeof crypto !== 'undefined' && crypto.randomUUID) {
            return crypto.randomUUID();
        }
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
            var r = (Math.random() * 16) | 0,
                v = c === 'x' ? r : (r & 0x3) | 0x8;
            return v.toString(16);
        });
    }

    // CSRF token retrieval
    function getCsrfToken() {
        var meta = document.querySelector('meta[name="csrf-token"]');
        if (meta && meta.content) return meta.content;
        return window.__HERMES_CSRF_TOKEN__ || sessionStorage.getItem('hermes.csrf_token') || '';
    }

    function safeUrl(url) {
        if (!url || typeof url !== 'string') return '#';
        var trimmed = url.trim();
        if (/^https?:\/\//i.test(trimmed) || /^blob:/i.test(trimmed) || /^\/api\//i.test(trimmed) || /^\/static\//i.test(trimmed)) {
            return trimmed;
        }
        return '#';
    }

    var HermesMissionControl = {
        state: {
            activeMissionId: null,
            activeMission: null,
            missions: [],
            events: [],
            cursor: 0,
            ws: null,
            wsConnected: false,
            reconnectTimer: null,
            reconnectAttempt: 0,
            selectedProject: 'doh-nut',
            selectedAgent: 'dohnut-social-autopilot',
            selectedExecutor: 'agy',
            capabilities: [],
            turnInProgress: false,
        },

        rootEl: null,

        mount: function (root) {
            if (!root) return;
            this.rootEl = root;
            this.rootEl.innerHTML = '';
            this.rootEl.setAttribute('data-mission-control', 'true');
            this.renderLayout();
            this.initSessionAndCapabilities();
            this.loadMissions();
        },

        initSessionAndCapabilities: function () {
            var self = this;
            // Fetch session/csrf if not present
            if (!getCsrfToken()) {
                fetch('/api/auth/session')
                    .then(function (res) { return res.ok ? res.json() : null; })
                    .then(function (data) {
                        if (data && data.csrf_token) {
                            sessionStorage.setItem('hermes.csrf_token', data.csrf_token);
                            window.__HERMES_CSRF_TOKEN__ = data.csrf_token;
                        }
                    })
                    .catch(function () {});
            }

            fetch('/api/capabilities')
                .then(function (res) { return res.ok ? res.json() : []; })
                .then(function (caps) {
                    self.state.capabilities = caps;
                    self.updateCapabilitiesView();
                })
                .catch(function () {});
        },

        renderLayout: function () {
            var self = this;
            var container = document.createElement('div');
            container.className = 'mission-control-root';

            // 1. Header Bar
            var header = document.createElement('div');
            header.className = 'mc-header-bar';
            header.innerHTML = [
                '<div class="mc-header-title">',
                '  <i data-lucide="crosshair" style="width: 16px; height: 16px; color: #a855f7; display: inline-block; vertical-align: middle;"></i>',
                '  <span>Doh-Nut Sovereign Mission Control</span>',
                '  <span id="mc-active-badge" class="mc-badge mc-badge-agy">AGY Isolated</span>',
                '</div>',
                '<div style="display: flex; align-items: center; gap: 8px;">',
                '  <span id="mc-status-region" aria-live="polite">Ready</span>',
                '  <button id="mc-btn-refresh" class="mc-btn mc-btn-secondary" style="min-height: 32px; padding: 4px 10px; font-size: 10px;">Refresh</button>',
                '</div>'
            ].join('');
            container.appendChild(header);

            // 2. Recovery Banner (Hidden by default)
            var recoveryBanner = document.createElement('div');
            recoveryBanner.id = 'mc-recovery-banner';
            recoveryBanner.className = 'mc-recovery-banner';
            recoveryBanner.style.display = 'none';
            recoveryBanner.innerHTML = [
                '<div class="mc-recovery-text">',
                '  <strong><i data-lucide="alert-triangle" style="width: 14px; height: 14px; color: #f59e0b; display: inline-block; vertical-align: middle; margin-right: 4px;"></i> Run Interrupted Across Restart:</strong> A previous execution was interrupted cleanly. State is preserved in WAL ledger.',
                '</div>',
                '<button id="mc-btn-resume" class="mc-btn mc-btn-primary" style="min-height: 36px; font-size: 11px;">Resume Turn</button>'
            ].join('');
            container.appendChild(recoveryBanner);

            // 3. Controls Card (Create Mission)
            var controlsCard = document.createElement('div');
            controlsCard.className = 'mc-controls-card';
            controlsCard.innerHTML = [
                '<div class="mc-form-row">',
                '  <label class="mc-label" for="mc-project-select">Project Profile',
                '    <select id="mc-project-select" class="mc-select" aria-label="Project Profile">',
                '      <option value="doh-nut" selected>Doh-Nut (G:\\Doh-Nut)</option>',
                '    </select>',
                '  </label>',
                '  <label class="mc-label" for="mc-agent-select">Assigned Agent',
                '    <select id="mc-agent-select" class="mc-select" aria-label="Assigned Agent">',
                '      <option value="dohnut-social-autopilot">dohnut-social-autopilot (6-Platform Viral)</option>',
                '      <option value="dohnut-baking-master">dohnut-baking-master (Baking & Kitchen)</option>',
                '      <option value="dohnut-ops-commander">dohnut-ops-commander (Supply & Logistics)</option>',
                '      <option value="dohnut-crm-retention">dohnut-crm-retention (Customer & Kiosk)</option>',
                '      <option value="dohnut-visual-director">dohnut-visual-director (Design & Assets)</option>',
                '      <option value="dohnut-security-guard">dohnut-security-guard (POS & Web Bridge)</option>',
                '      <option value="dohnut-finance-ledger">dohnut-finance-ledger (Revenue & Margin)</option>',
                '      <option value="dohnut-growth-hacker">dohnut-growth-hacker (Traffic & Campaign)</option>',
                '    </select>',
                '  </label>',
                '</div>',
                '<div class="mc-form-row">',
                '  <label class="mc-label" for="mc-mission-title">Mission Title',
                '    <input id="mc-mission-title" class="mc-input" type="text" aria-label="Mission Title" placeholder="e.g. Sedia Campaign Donut Panas Jumaat" value="Campaign Launch & Prep" />',
                '  </label>',
                '  <label class="mc-label" for="mc-mission-objective">Mission Objective',
                '    <input id="mc-mission-objective" class="mc-input" type="text" aria-label="Mission Objective" placeholder="Tugasan objektif spesifik..." value="Jana pelan kempen 6-platform tanpa publish automatik." />',
                '  </label>',
                '</div>',
                '<div style="display: flex; justify-content: flex-end; gap: 8px;">',
                '  <button id="mc-btn-create" data-action="create-mission" class="mc-btn mc-btn-primary">',
                '    <span>🚀</span> Launch AGY Mission',
                '  </button>',
                '</div>'
            ].join('');
            container.appendChild(controlsCard);

            // 4. Mission Selector & Stream Grid
            var streamCard = document.createElement('div');
            streamCard.className = 'mc-stream-container';

            var streamHeader = document.createElement('div');
            streamHeader.className = 'mc-stream-header';
            streamHeader.innerHTML = [
                '<div style="display: flex; align-items: center; gap: 8px;">',
                '  <span style="color: #c084fc;">●</span>',
                '  <span id="mc-stream-title">No Active Mission</span>',
                '</div>',
                '<div style="display: flex; align-items: center; gap: 8px;">',
                '  <span id="mc-ws-indicator" style="font-size: 9px; color: rgba(255,255,255,0.4);">WS Disconnected</span>',
                '  <button id="mc-btn-cancel" data-action="cancel-mission" class="mc-btn mc-btn-danger" style="min-height: 28px; padding: 2px 8px; font-size: 10px; display: none;">Cancel</button>',
                '</div>'
            ].join('');
            streamCard.appendChild(streamHeader);

            var streamLog = document.createElement('div');
            streamLog.id = 'mc-stream-log';
            streamLog.className = 'mc-stream-log';
            streamLog.setAttribute('role', 'log');
            streamLog.setAttribute('aria-live', 'polite');
            streamCard.appendChild(streamLog);

            // Turn Input Bar
            var turnBar = document.createElement('div');
            turnBar.className = 'mc-turn-bar';
            turnBar.innerHTML = [
                '<input id="mc-turn-input" class="mc-input" type="text" aria-label="Turn prompt message" placeholder="Hantar arahan giliran seterusnya (e.g. Sila audit kos dan semak bahan)..." style="flex: 1;" />',
                '<button id="mc-btn-send" data-action="send-turn" class="mc-btn mc-btn-primary">',
                '  <span>Send</span>',
                '</button>'
            ].join('');
            streamCard.appendChild(turnBar);

            container.appendChild(streamCard);

            // 5. Verification, Artifacts & Approval Drawer
            var sideGrid = document.createElement('div');
            sideGrid.className = 'mc-side-grid';

            // Artifacts Card
            var artifactsCard = document.createElement('div');
            artifactsCard.className = 'mc-drawer-card';
            artifactsCard.innerHTML = [
                '<div class="mc-drawer-title">',
                '  <span>📦 Durable Artifacts</span>',
                '  <span id="mc-artifacts-count" style="font-size: 9px; color: rgba(255,255,255,0.4);">0 files</span>',
                '</div>',
                '<div id="mc-artifacts-list" class="mc-artifacts-list">',
                '  <div style="font-size: 10px; color: rgba(255,255,255,0.4); text-align: center; padding: 10px;">Tiada fail dihasilkan lagi.</div>',
                '</div>'
            ].join('');
            sideGrid.appendChild(artifactsCard);

            // Approvals Drawer Card
            var approvalCard = document.createElement('div');
            approvalCard.className = 'mc-drawer-card';
            approvalCard.innerHTML = [
                '<div class="mc-drawer-title">',
                '  <span>🛡️ Human Gate Approval</span>',
                '  <span id="mc-approval-status" class="mc-badge mc-badge-status-waiting">None Required</span>',
                '</div>',
                '<div id="mc-approval-body" style="font-size: 10px; color: rgba(255,255,255,0.6); display: flex; flex-direction: column; gap: 6px;">',
                '  <div>Tiada tindakan berisiko tinggi yang menunggu pengesahan.</div>',
                '</div>',
                '<div id="mc-approval-actions" style="display: none; gap: 8px; margin-top: 6px;">',
                '  <button id="mc-btn-approve" data-action="approve-attempt" class="mc-btn mc-btn-primary" style="flex: 1; min-height: 38px;">Sah & Luluskan</button>',
                '  <button id="mc-btn-reject" data-action="reject-attempt" class="mc-btn mc-btn-danger" style="flex: 1; min-height: 38px;">Tolak</button>',
                '</div>'
            ].join('');
            sideGrid.appendChild(approvalCard);

            // Capabilities Card
            var capCard = document.createElement('div');
            capCard.className = 'mc-drawer-card';
            capCard.innerHTML = [
                '<div class="mc-drawer-title">',
                '  <span>⚡ Capability Probes</span>',
                '  <span id="mc-caps-count" style="font-size: 9px; color: #4ade80;">Active</span>',
                '</div>',
                '<div id="mc-caps-list" style="display: flex; flex-wrap: wrap; gap: 4px; font-size: 9px;">',
                '  <span class="mc-badge mc-badge-agy">AGY CLI</span>',
                '  <span class="mc-badge mc-badge-status-succeeded">SQLite WAL</span>',
                '  <span class="mc-badge mc-badge-status-succeeded">WebBridge 10087</span>',
                '  <span class="mc-badge mc-badge-status-waiting">Hermes Adapter</span>',
                '</div>'
            ].join('');
            sideGrid.appendChild(capCard);

            container.appendChild(sideGrid);
            this.rootEl.appendChild(container);

            this.bindEvents();
        },

        bindEvents: function () {
            var self = this;

            var createBtn = document.getElementById('mc-btn-create');
            if (createBtn) {
                createBtn.addEventListener('click', function () {
                    self.createMission();
                });
            }

            var sendBtn = document.getElementById('mc-btn-send');
            if (sendBtn) {
                sendBtn.addEventListener('click', function () {
                    self.sendTurn();
                });
            }

            var turnInput = document.getElementById('mc-turn-input');
            if (turnInput) {
                turnInput.addEventListener('keydown', function (e) {
                    if (e.key === 'Enter') {
                        e.preventDefault();
                        self.sendTurn();
                    }
                });
            }

            var cancelBtn = document.getElementById('mc-btn-cancel');
            if (cancelBtn) {
                cancelBtn.addEventListener('click', function () {
                    if (confirm('Adakah anda pasti mahu membatalkan misi ini?')) {
                        self.cancelMission();
                    }
                });
            }

            var refreshBtn = document.getElementById('mc-btn-refresh');
            if (refreshBtn) {
                refreshBtn.addEventListener('click', function () {
                    self.loadMissions();
                });
            }
        },

        setStatus: function (msg) {
            var el = document.getElementById('mc-status-region');
            if (el) el.textContent = msg;
        },

        createMission: function () {
            var self = this;
            var proj = document.getElementById('mc-project-select').value;
            var agent = document.getElementById('mc-agent-select').value;
            var title = document.getElementById('mc-mission-title').value.trim();
            var obj = document.getElementById('mc-mission-objective').value.trim();
            var csrf = getCsrfToken();

            if (!title) {
                alert('Sila masukkan tajuk misi.');
                return;
            }

            self.setStatus('Launching mission...');
            var btn = document.getElementById('mc-btn-create');
            if (btn) btn.disabled = true;

            var payload = {
                project_slug: proj,
                agent_profile: agent,
                title: title,
                objective: obj || title,
                primary_executor: 'agy',
                idempotency_key: generateUUID()
            };

            fetch('/api/missions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'x-csrf-token': csrf
                },
                body: JSON.stringify(payload)
            })
            .then(function (res) {
                if (!res.ok) {
                    return res.json().then(function (err) { throw new Error(err.detail || 'Failed'); });
                }
                return res.json();
            })
            .then(function (data) {
                self.setStatus('Mission created!');
                self.loadMissions(data.mission_id || data.id);
            })
            .catch(function (err) {
                self.setStatus('Error: ' + err.message);
                alert('Ralat mencipta misi: ' + err.message);
            })
            .finally(function () {
                if (btn) btn.disabled = false;
            });
        },

        loadMissions: function (selectId) {
            var self = this;
            self.setStatus('Loading missions...');
            fetch('/api/missions')
                .then(function (res) { return res.ok ? res.json() : []; })
                .then(function (missions) {
                    self.state.missions = missions;
                    if (missions.length > 0) {
                        var targetId = selectId || self.state.activeMissionId || missions[0].id || missions[0].mission_id;
                        self.selectMission(targetId);
                    } else {
                        self.setStatus('No active missions');
                    }
                })
                .catch(function (err) {
                    self.setStatus('Load failed');
                });
        },

        selectMission: function (missionId) {
            var self = this;
            self.state.activeMissionId = missionId;
            self.state.cursor = parseInt(sessionStorage.getItem('hermes.mission.' + missionId + '.sequence') || '0', 10);

            var titleEl = document.getElementById('mc-stream-title');
            var cancelBtn = document.getElementById('mc-btn-cancel');
            if (titleEl) titleEl.textContent = 'Mission ' + String(missionId).substring(0, 8);
            if (cancelBtn) cancelBtn.style.display = 'inline-flex';

            // Catch-up via REST cursor first
            self.setStatus('Syncing event ledger...');
            fetch('/api/missions/' + missionId + '/events?after_sequence=' + self.state.cursor)
                .then(function (res) { return res.ok ? res.json() : []; })
                .then(function (events) {
                    self.state.events = [];
                    var streamLog = document.getElementById('mc-stream-log');
                    if (streamLog) streamLog.innerHTML = '';

                    events.forEach(function (ev) {
                        self.appendEvent(ev);
                    });
                    self.setStatus('Ledger synced');
                    self.connectWebSocket(missionId);
                })
                .catch(function (err) {
                    self.setStatus('Sync failed, trying WS...');
                    self.connectWebSocket(missionId);
                });
        },

        connectWebSocket: function (missionId) {
            var self = this;
            if (self.state.ws) {
                try { self.state.ws.close(); } catch (e) {}
                self.state.ws = null;
            }

            var csrf = getCsrfToken();
            var wsIndicator = document.getElementById('mc-ws-indicator');
            if (wsIndicator) wsIndicator.textContent = 'WS Connecting...';

            // Request 1-time ticket
            fetch('/api/auth/websocket-ticket', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'x-csrf-token': csrf
                }
            })
            .then(function (res) { return res.ok ? res.json() : null; })
            .then(function (ticketData) {
                if (!ticketData || !ticketData.ticket) {
                    throw new Error('Ticket denied');
                }

                var proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                var wsUrl = proto + '//' + window.location.host + '/ws/missions/' + missionId;
                var ws = new WebSocket(wsUrl);

                ws.onopen = function () {
                    self.state.reconnectAttempt = 0;
                    if (wsIndicator) {
                        wsIndicator.textContent = 'WS Live ●';
                        wsIndicator.style.color = '#4ade80';
                    }
                    // Send handshake payload
                    ws.send(JSON.stringify({
                        ticket: ticketData.ticket,
                        after_sequence: self.state.cursor
                    }));
                };

                ws.onmessage = function (event) {
                    try {
                        var ev = JSON.parse(event.data);
                        self.appendEvent(ev);
                    } catch (e) {}
                };

                ws.onclose = function () {
                    if (wsIndicator) {
                        wsIndicator.textContent = 'WS Disconnected';
                        wsIndicator.style.color = 'rgba(255,255,255,0.4)';
                    }
                    self.scheduleReconnect(missionId);
                };

                ws.onerror = function () {
                    try { ws.close(); } catch (e) {}
                };

                self.state.ws = ws;
            })
            .catch(function (err) {
                if (wsIndicator) wsIndicator.textContent = 'WS Ticket Failed';
                self.scheduleReconnect(missionId);
            });
        },

        scheduleReconnect: function (missionId) {
            var self = this;
            if (self.state.reconnectTimer) clearTimeout(self.state.reconnectTimer);

            self.state.reconnectAttempt++;
            // Exponential backoff capped at 30 seconds
            var delay = Math.min(30000, 1000 * Math.pow(1.5, self.state.reconnectAttempt));
            self.state.reconnectTimer = setTimeout(function () {
                if (self.state.activeMissionId === missionId) {
                    self.connectWebSocket(missionId);
                }
            }, delay);
        },

        appendEvent: function (ev) {
            var self = this;
            var seq = ev.sequence || 0;
            if (seq > self.state.cursor) {
                self.state.cursor = seq;
                if (self.state.activeMissionId) {
                    sessionStorage.setItem('hermes.mission.' + self.state.activeMissionId + '.sequence', String(seq));
                }
            }

            var streamLog = document.getElementById('mc-stream-log');
            if (!streamLog) return;

            var item = document.createElement('div');
            item.className = 'mc-event-item';

            var evType = ev.event_type || 'event';
            var payload = ev.payload || {};

            if (evType.indexOf('turn.') === 0 || evType === 'turn.enqueued') {
                item.className += ' mc-event-user';
            } else if (evType.indexOf('agy.') === 0 || evType === 'run.completed') {
                item.className += ' mc-event-agent';
            } else {
                item.className += ' mc-event-system';
            }

            var meta = document.createElement('div');
            meta.className = 'mc-event-meta';
            meta.textContent = '#' + seq + ' · ' + evType + ' · ' + (ev.created_at ? new Date(ev.created_at).toLocaleTimeString() : '');
            item.appendChild(meta);

            var text = document.createElement('div');
            text.className = 'mc-event-text';

            // Safe text extraction
            var displayContent = '';
            if (typeof payload === 'string') {
                displayContent = payload;
            } else if (payload.message) {
                displayContent = payload.message;
            } else if (payload.text) {
                displayContent = payload.text;
            } else if (payload.delta) {
                displayContent = payload.delta;
            } else if (payload.result) {
                displayContent = typeof payload.result === 'string' ? payload.result : JSON.stringify(payload.result);
            } else {
                displayContent = JSON.stringify(payload);
            }

            text.textContent = displayContent;
            item.appendChild(text);

            streamLog.appendChild(item);
            streamLog.scrollTop = streamLog.scrollHeight;

            // Handle artifacts or recovery
            if (evType === 'artifact.created' && payload.url) {
                self.addArtifact(payload);
            }
            if (evType === 'run.interrupted') {
                var rec = document.getElementById('mc-recovery-banner');
                if (rec) rec.style.display = 'flex';
            }
        },

        sendTurn: function () {
            var self = this;
            if (!self.state.activeMissionId) {
                alert('Sila pilih atau cipta misi dahulu.');
                return;
            }

            var input = document.getElementById('mc-turn-input');
            var btn = document.getElementById('mc-btn-send');
            var msg = input ? input.value.trim() : '';
            if (!msg) return;

            var csrf = getCsrfToken();
            self.setStatus('Sending turn...');
            if (btn) btn.disabled = true;

            fetch('/api/missions/' + self.state.activeMissionId + '/turns', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'x-csrf-token': csrf
                },
                body: JSON.stringify({ message: msg, idempotency_key: generateUUID() })
            })
            .then(function (res) {
                if (!res.ok) throw new Error('Turn rejected');
                return res.json();
            })
            .then(function () {
                if (input) input.value = '';
                self.setStatus('Turn queued');
            })
            .catch(function (err) {
                self.setStatus('Turn failed: ' + err.message);
                alert('Gagal menghantar turn: ' + err.message);
            })
            .finally(function () {
                if (btn) btn.disabled = false;
            });
        },

        cancelMission: function () {
            var self = this;
            if (!self.state.activeMissionId) return;
            var csrf = getCsrfToken();

            fetch('/api/missions/' + self.state.activeMissionId + '/cancel', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'x-csrf-token': csrf
                }
            })
            .then(function () {
                self.setStatus('Mission cancelled');
            })
            .catch(function (err) {
                alert('Gagal membatalkan misi: ' + err.message);
            });
        },

        addArtifact: function (art) {
            var list = document.getElementById('mc-artifacts-list');
            if (!list) return;

            var item = document.createElement('div');
            item.className = 'mc-artifact-item';

            var link = document.createElement('a');
            link.className = 'mc-artifact-link';
            link.href = safeUrl(art.url);
            link.target = '_blank';
            link.rel = 'noopener noreferrer';
            link.textContent = art.title || art.filename || 'Artifact';

            var size = document.createElement('span');
            size.style.color = 'rgba(255,255,255,0.4)';
            size.textContent = art.type || 'file';

            item.appendChild(link);
            item.appendChild(size);
            list.appendChild(item);
        },

        updateCapabilitiesView: function () {
            var caps = this.state.capabilities || [];
            var list = document.getElementById('mc-caps-list');
            if (!list || caps.length === 0) return;

            list.innerHTML = '';
            caps.forEach(function (c) {
                var badge = document.createElement('span');
                badge.className = 'mc-badge mc-badge-status-succeeded';
                badge.textContent = c.name || c.id || 'Cap';
                list.appendChild(badge);
            });
        }
    };

    window.HermesMissionControl = HermesMissionControl;

})(window);
