"""Flask + SocketIO web dashboard for real-time monitoring and config toggling."""

from __future__ import annotations

import asyncio
import json
import threading
from pathlib import Path

from flask import Flask, jsonify, render_template_string, request
from flask_socketio import SocketIO

from core.config_manager import ConfigManager

TEMPLATE = """
<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Loctor Builder Dashboard</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.5/socket.io.min.js"></script>
    <style>
        :root {
            --bg-primary: #0f172a;
            --bg-secondary: #1e293b;
            --bg-card: #1e293b;
            --text-primary: #f1f5f9;
            --text-secondary: #94a3b8;
            --accent: #38bdf8;
            --accent-hover: #7dd3fc;
            --success: #4ade80;
            --warning: #fbbf24;
            --danger: #f87171;
            --border: #334155;
            --radius: 12px;
            --shadow: 0 4px 6px -1px rgba(0,0,0,0.3);
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
        }

        .header {
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border);
            padding: 1rem 2rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .header h1 {
            font-size: 1.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, var(--accent), #818cf8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .header .status-badge {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.4rem 1rem;
            background: rgba(56,189,248,0.1);
            border: 1px solid var(--accent);
            border-radius: 20px;
            font-size: 0.85rem;
        }

        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--success);
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.4; }
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1.5rem;
        }

        .card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 1.5rem;
            box-shadow: var(--shadow);
        }

        .card-title {
            font-size: 1rem;
            font-weight: 600;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 1rem;
            padding-bottom: 0.75rem;
            border-bottom: 1px solid var(--border);
        }

        .provider-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 0.75rem;
        }

        .provider-btn {
            padding: 1rem;
            border-radius: 8px;
            border: 2px solid var(--border);
            background: transparent;
            color: var(--text-primary);
            cursor: pointer;
            transition: all 0.2s ease;
            text-align: center;
            font-size: 0.9rem;
            font-weight: 500;
        }

        .provider-btn:hover {
            border-color: var(--accent);
            background: rgba(56,189,248,0.05);
        }

        .provider-btn.active {
            border-color: var(--accent);
            background: rgba(56,189,248,0.15);
            box-shadow: 0 0 20px rgba(56,189,248,0.1);
        }

        .provider-btn .model-name {
            font-size: 0.75rem;
            color: var(--text-secondary);
            margin-top: 0.25rem;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1rem;
        }

        .stat-item {
            text-align: center;
            padding: 1rem;
            border-radius: 8px;
            background: rgba(255,255,255,0.03);
        }

        .stat-value {
            font-size: 2rem;
            font-weight: 700;
            line-height: 1;
        }

        .stat-label {
            font-size: 0.75rem;
            color: var(--text-secondary);
            margin-top: 0.5rem;
            text-transform: uppercase;
        }

        .stat-value.passed { color: var(--success); }
        .stat-value.healed { color: var(--warning); }
        .stat-value.failed { color: var(--danger); }
        .stat-value.total  { color: var(--accent); }

        .log-feed {
            max-height: 400px;
            overflow-y: auto;
            font-family: 'Cascadia Code', 'Fira Code', monospace;
            font-size: 0.8rem;
            line-height: 1.7;
        }

        .log-feed::-webkit-scrollbar { width: 6px; }
        .log-feed::-webkit-scrollbar-track { background: transparent; }
        .log-feed::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }

        .log-entry {
            padding: 0.25rem 0;
            border-bottom: 1px solid rgba(255,255,255,0.03);
        }

        .log-time { color: var(--text-secondary); }
        .log-pass { color: var(--success); }
        .log-heal { color: var(--warning); }
        .log-fail { color: var(--danger); }
        .log-info { color: var(--accent); }

        .full-width { grid-column: 1 / -1; }

        .settings-form { display: grid; gap: 0.75rem; }

        .form-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0.5rem 0;
        }

        .form-label {
            font-size: 0.9rem;
            color: var(--text-secondary);
        }

        .toggle {
            position: relative;
            width: 44px;
            height: 24px;
        }

        .toggle input { opacity: 0; width: 0; height: 0; }

        .toggle-slider {
            position: absolute;
            cursor: pointer;
            top: 0; left: 0; right: 0; bottom: 0;
            background: var(--border);
            border-radius: 12px;
            transition: 0.3s;
        }

        .toggle-slider::before {
            content: '';
            position: absolute;
            width: 18px;
            height: 18px;
            left: 3px;
            bottom: 3px;
            background: var(--text-primary);
            border-radius: 50%;
            transition: 0.3s;
        }

        .toggle input:checked + .toggle-slider { background: var(--accent); }
        .toggle input:checked + .toggle-slider::before { transform: translateX(20px); }

        .input-sm {
            background: var(--bg-primary);
            border: 1px solid var(--border);
            border-radius: 6px;
            color: var(--text-primary);
            padding: 0.4rem 0.75rem;
            font-size: 0.85rem;
            width: 80px;
            text-align: right;
        }

        .input-sm:focus {
            outline: none;
            border-color: var(--accent);
        }

        .btn {
            padding: 0.6rem 1.5rem;
            border-radius: 8px;
            border: none;
            font-size: 0.9rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
        }

        .btn-primary {
            background: var(--accent);
            color: var(--bg-primary);
        }

        .btn-primary:hover { background: var(--accent-hover); }

        @media (max-width: 900px) {
            .container { grid-template-columns: 1fr; }
            .stats-grid { grid-template-columns: repeat(2, 1fr); }
            .provider-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Loctor Builder</h1>
        <div class="status-badge">
            <div class="status-dot" id="statusDot"></div>
            <span id="statusText">Connected</span>
        </div>
    </div>

    <div class="container">
        <div class="card">
            <div class="card-title">AI Provider</div>
            <div class="provider-grid">
                <button class="provider-btn" id="btn-gemini" onclick="switchProvider('gemini')">
                    Gemini
                    <div class="model-name" id="model-gemini"></div>
                </button>
                <button class="provider-btn" id="btn-openai" onclick="switchProvider('openai')">
                    OpenAI
                    <div class="model-name" id="model-openai"></div>
                </button>
                <button class="provider-btn" id="btn-claude" onclick="switchProvider('claude')">
                    Claude
                    <div class="model-name" id="model-claude"></div>
                </button>
            </div>
        </div>

        <div class="card">
            <div class="card-title">Audit Statistics</div>
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-value total" id="stat-total">0</div>
                    <div class="stat-label">Total</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value passed" id="stat-passed">0</div>
                    <div class="stat-label">Passed</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value healed" id="stat-healed">0</div>
                    <div class="stat-label">Healed</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value failed" id="stat-failed">0</div>
                    <div class="stat-label">Failed</div>
                </div>
            </div>
        </div>

        <div class="card">
            <div class="card-title">Settings</div>
            <div class="settings-form">
                <div class="form-row">
                    <span class="form-label">Auto-Commit</span>
                    <label class="toggle">
                        <input type="checkbox" id="set-autocommit" onchange="updateSetting('auto_commit', this.checked)">
                        <span class="toggle-slider"></span>
                    </label>
                </div>
                <div class="form-row">
                    <span class="form-label">Headless Browser</span>
                    <label class="toggle">
                        <input type="checkbox" id="set-headless" onchange="updateSetting('headless', this.checked)">
                        <span class="toggle-slider"></span>
                    </label>
                </div>
                <div class="form-row">
                    <span class="form-label">Retry Limit</span>
                    <input type="number" class="input-sm" id="set-retry" min="1" max="10" value="3"
                           onchange="updateSetting('retry_limit', parseInt(this.value))">
                </div>
                <div class="form-row">
                    <span class="form-label">Timeout (ms)</span>
                    <input type="number" class="input-sm" id="set-timeout" min="1000" max="30000" step="1000" value="5000"
                           onchange="updateSetting('validation_timeout', parseInt(this.value))">
                </div>
            </div>
        </div>

        <div class="card">
            <div class="card-title">Configuration</div>
            <pre id="configView" style="font-size:0.8rem; color:var(--text-secondary); white-space:pre-wrap; max-height:300px; overflow-y:auto;"></pre>
        </div>

        <div class="card full-width">
            <div class="card-title">Live Activity Feed</div>
            <div class="log-feed" id="logFeed">
                <div class="log-entry">
                    <span class="log-info">System ready. Waiting for audit...</span>
                </div>
            </div>
        </div>
    </div>

    <script>
        const socket = io();

        socket.on('connect', () => {
            document.getElementById('statusDot').style.background = '#4ade80';
            document.getElementById('statusText').textContent = 'Connected';
            loadConfig();
        });

        socket.on('disconnect', () => {
            document.getElementById('statusDot').style.background = '#f87171';
            document.getElementById('statusText').textContent = 'Disconnected';
        });

        socket.on('config_updated', (data) => {
            loadConfig();
            addLog('info', `Config updated: ${JSON.stringify(data)}`);
        });

        socket.on('element_audited', (data) => {
            const cls = data.status === 'passed' ? 'pass' : data.status === 'healed' ? 'heal' : 'fail';
            addLog(cls, `${data.status.toUpperCase()} - ${data.element_name} (${data.page_name})`);
            updateStats(data);
        });

        socket.on('page_started', (data) => {
            addLog('info', `Navigating to: ${data.page_name} (${data.url})`);
        });

        function switchProvider(name) {
            fetch('/api/provider', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ provider: name })
            }).then(r => r.json()).then(data => {
                if (data.success) loadConfig();
            });
        }

        function updateSetting(key, value) {
            fetch('/api/settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ key, value })
            }).then(r => r.json()).then(data => {
                if (data.success) loadConfig();
            });
        }

        function loadConfig() {
            fetch('/api/config').then(r => r.json()).then(data => {
                document.getElementById('configView').textContent = JSON.stringify(data, null, 2);

                document.querySelectorAll('.provider-btn').forEach(b => b.classList.remove('active'));
                const activeBtn = document.getElementById('btn-' + data.active_provider);
                if (activeBtn) activeBtn.classList.add('active');

                for (const [name, cfg] of Object.entries(data.providers || {})) {
                    const el = document.getElementById('model-' + name);
                    if (el) el.textContent = cfg.model;
                }

                const settings = data.settings || {};
                const ac = document.getElementById('set-autocommit');
                if (ac) ac.checked = settings.auto_commit !== false;
                const hl = document.getElementById('set-headless');
                if (hl) hl.checked = settings.headless !== false;
                const rt = document.getElementById('set-retry');
                if (rt) rt.value = settings.retry_limit || 3;
                const to = document.getElementById('set-timeout');
                if (to) to.value = settings.validation_timeout || 5000;
            });
        }

        let stats = { total: 0, passed: 0, healed: 0, failed: 0 };

        function updateStats(data) {
            stats.total++;
            if (data.status === 'passed') stats.passed++;
            else if (data.status === 'healed') stats.healed++;
            else stats.failed++;

            document.getElementById('stat-total').textContent = stats.total;
            document.getElementById('stat-passed').textContent = stats.passed;
            document.getElementById('stat-healed').textContent = stats.healed;
            document.getElementById('stat-failed').textContent = stats.failed;
        }

        function addLog(cls, message) {
            const feed = document.getElementById('logFeed');
            const time = new Date().toLocaleTimeString();
            const entry = document.createElement('div');
            entry.className = 'log-entry';
            entry.innerHTML = `<span class="log-time">${time}</span> <span class="log-${cls}">${message}</span>`;
            feed.appendChild(entry);
            feed.scrollTop = feed.scrollHeight;
        }

        loadConfig();
    </script>
</body>
</html>
"""


def create_app(config: ConfigManager):
    """Create and configure the Flask + SocketIO application."""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "loctor-builder-dashboard"
    socketio = SocketIO(app, cors_allowed_origins="*")

    @app.route("/")
    def index():
        return render_template_string(TEMPLATE)

    @app.route("/api/config")
    def get_config():
        return jsonify(config.to_dict())

    @app.route("/api/provider", methods=["POST"])
    def set_provider():
        data = request.get_json()
        provider = data.get("provider")
        try:
            config.active_provider = provider
            socketio.emit("config_updated", {"provider": provider})
            return jsonify({"success": True, "provider": provider})
        except ValueError as e:
            return jsonify({"success": False, "error": str(e)}), 400

    @app.route("/api/settings", methods=["POST"])
    def update_settings():
        data = request.get_json()
        key = data.get("key")
        value = data.get("value")
        if not key:
            return jsonify({"success": False, "error": "No key provided"}), 400
        config.set_setting(key, value)
        socketio.emit("config_updated", {key: value})
        return jsonify({"success": True, "key": key, "value": value})

    @app.route("/api/stats")
    def get_stats():
        return jsonify({"status": "ready"})

    def emit_element_result(result):
        socketio.emit(
            "element_audited",
            {
                "element_name": result.element_name,
                "page_name": result.page_name,
                "status": result.status.value,
            },
        )

    def emit_page_started(page_name, url):
        socketio.emit("page_started", {"page_name": page_name, "url": url})

    app.emit_element_result = emit_element_result
    app.emit_page_started = emit_page_started

    return app, socketio
