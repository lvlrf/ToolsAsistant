#!/usr/bin/env python3
"""
@lvlRF Tunnel Management Dashboard
Web-based dashboard for managing tunnel services
"""

# ============================================================================
# CONFIGURATION - تنظیمات اصلی
# ============================================================================

DASHBOARD_PORT = 8000
DASHBOARD_PASSWORD = "your-secure-password-here"  # ⚠️ حتماً تغییر بده!
AUTO_REFRESH_SECONDS = 3
BINARY_PATH = "/root/backhaul-core"
STATE_FILE = f"{BINARY_PATH}/state.json"
CONFIG_FILE = f"{BINARY_PATH}/config.json"

# ============================================================================

from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
import subprocess
import json
import os
from functools import wraps
from datetime import datetime, timedelta
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
app.permanent_session_lifetime = timedelta(hours=24)

# ============================================================================
# Authentication
# ============================================================================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('password') == DASHBOARD_PASSWORD:
            session['logged_in'] = True
            session.permanent = True
            return redirect(url_for('index'))
        return render_template_string(LOGIN_TEMPLATE, error="رمز عبور اشتباه است")
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ============================================================================
# Main Dashboard
# ============================================================================

@app.route('/')
@login_required
def index():
    return render_template_string(DASHBOARD_TEMPLATE, 
                                 refresh_interval=AUTO_REFRESH_SECONDS)

# ============================================================================
# API Endpoints
# ============================================================================

@app.route('/api/configs')
@login_required
def get_configs():
    """Get all configs with live status"""
    try:
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
        
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        
        # Build server IP map
        server_ips = {}
        for server in config.get('iran_servers', []):
            server_ips[server['name']] = {'ip': server['ip'], 'type': 'iran'}
        for server in config.get('kharej_servers', []):
            server_ips[server['name']] = {'ip': server['ip'], 'type': 'kharej'}
        
        configs = []
        for cfg in state.get('generated_configs', []):
            service_name = generate_service_name(cfg)
            status = get_service_status(service_name)
            
            iran_ip = server_ips.get(cfg['iran'], {}).get('ip', 'N/A')
            kharej_ip = server_ips.get(cfg['kharej'], {}).get('ip', 'N/A')
            
            configs.append({
                'service_name': service_name,
                'iran': cfg['iran'],
                'kharej': cfg['kharej'],
                'iran_ip': iran_ip,
                'kharej_ip': kharej_ip,
                'transport': cfg['transport'],
                'profile': cfg['profile'],
                'mux_version': cfg.get('mux_version'),
                'tunnel_port': cfg['tunnel_port'],
                'web_port': cfg['web_port'],
                'iperf_port': cfg['iperf_port'],
                'subnet': cfg.get('subnet'),
                'token': cfg.get('token', ''),
                'status': status
            })
        
        return jsonify({'success': True, 'configs': configs})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/service/<action>/<service_name>')
@login_required
def service_action(action, service_name):
    """Perform action on service"""
    try:
        if action == 'start':
            cmd = ['systemctl', 'start', f'{service_name}.service']
        elif action == 'stop':
            cmd = ['systemctl', 'stop', f'{service_name}.service']
        elif action == 'restart':
            cmd = ['systemctl', 'restart', f'{service_name}.service']
        elif action == 'status':
            return jsonify(get_service_status_detail(service_name))
        else:
            return jsonify({'success': False, 'error': 'Invalid action'})
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        return jsonify({
            'success': result.returncode == 0,
            'message': f'Service {action}ed successfully' if result.returncode == 0 else result.stderr
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/logs/<service_name>')
@login_required
def get_logs(service_name):
    """Get service logs"""
    try:
        cmd = ['journalctl', '-u', f'{service_name}.service', '-n', '100', '--no-pager']
        result = subprocess.run(cmd, capture_output=True, text=True)
        return jsonify({
            'success': True,
            'logs': result.stdout
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/edit-port', methods=['POST'])
@login_required
def edit_port():
    """Edit ports in config file and restart service"""
    try:
        data = request.json
        service_name = data['service_name']
        new_tunnel_port = data['tunnel_port']
        new_web_port = data['web_port']
        new_iperf_port = data['iperf_port']
        
        # Find config file
        config_file = find_config_file(service_name)
        if not config_file:
            return jsonify({'success': False, 'error': 'Config file not found'})
        
        # Read and modify config
        with open(config_file, 'r') as f:
            content = f.read()
        
        # Replace ports (simple regex replacement)
        import re
        content = re.sub(r'bind_addr = "0\.0\.0\.0:\d+"', 
                        f'bind_addr = "0.0.0.0:{new_tunnel_port}"', content)
        content = re.sub(r'remote_addr = "[^:]+:\d+"',
                        lambda m: m.group(0).rsplit(':', 1)[0] + f':{new_tunnel_port}"', content)
        content = re.sub(r'web_port = \d+', f'web_port = {new_web_port}', content)
        
        # Update iperf port in ports array
        content = re.sub(r'"\d+=127\.0\.0\.1:\d+"',
                        f'"{new_iperf_port}=127.0.0.1:5201"', content)
        
        # Write back
        with open(config_file, 'w') as f:
            f.write(content)
        
        # Restart service
        subprocess.run(['systemctl', 'restart', f'{service_name}.service'])
        
        # Update state.json
        update_state_file(service_name, new_tunnel_port, new_web_port, new_iperf_port)
        
        return jsonify({'success': True, 'message': 'Ports updated and service restarted'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/dashboard/control/<action>')
@login_required
def dashboard_control(action):
    """Enable or disable dashboard service"""
    try:
        if action == 'enable':
            subprocess.run(['systemctl', 'enable', 'lvlrf-dashboard.service'])
            subprocess.run(['systemctl', 'start', 'lvlrf-dashboard.service'])
            message = 'Dashboard service enabled'
        elif action == 'disable':
            subprocess.run(['systemctl', 'disable', 'lvlrf-dashboard.service'])
            subprocess.run(['systemctl', 'stop', 'lvlrf-dashboard.service'])
            message = 'Dashboard service disabled'
        elif action == 'status':
            result = subprocess.run(['systemctl', 'is-active', 'lvlrf-dashboard.service'],
                                  capture_output=True, text=True)
            enabled = subprocess.run(['systemctl', 'is-enabled', 'lvlrf-dashboard.service'],
                                   capture_output=True, text=True)
            return jsonify({
                'success': True,
                'active': result.stdout.strip() == 'active',
                'enabled': enabled.stdout.strip() == 'enabled'
            })
        else:
            return jsonify({'success': False, 'error': 'Invalid action'})
        
        return jsonify({'success': True, 'message': message})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/bulk/<action>')
@login_required
def bulk_action(action):
    """Perform bulk action on all services"""
    try:
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
        
        results = []
        for cfg in state.get('generated_configs', []):
            service_name = generate_service_name(cfg)
            
            if action == 'start':
                cmd = ['systemctl', 'start', f'{service_name}.service']
            elif action == 'stop':
                cmd = ['systemctl', 'stop', f'{service_name}.service']
            elif action == 'restart':
                cmd = ['systemctl', 'restart', f'{service_name}.service']
            else:
                continue
            
            result = subprocess.run(cmd, capture_output=True)
            results.append({
                'service': service_name,
                'success': result.returncode == 0
            })
        
        return jsonify({
            'success': True,
            'results': results,
            'message': f'Bulk {action} completed'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# ============================================================================
# Helper Functions
# ============================================================================

def generate_service_name(cfg):
    """Generate service name from config"""
    port = cfg['tunnel_port']
    transport = cfg['transport']
    mux_version = cfg.get('mux_version')
    profile = cfg['profile']
    
    name = f"@lvlRF-Tunnel-{port}-{transport}"
    if mux_version:
        name += f"-v{mux_version}"
    name += f"-{profile}"
    
    return name

def get_service_status(service_name):
    """Get service status (active, inactive, failed)"""
    try:
        result = subprocess.run(
            ['systemctl', 'is-active', f'{service_name}.service'],
            capture_output=True,
            text=True
        )
        status = result.stdout.strip()
        return status if status in ['active', 'inactive', 'failed'] else 'unknown'
    except:
        return 'unknown'

def get_service_status_detail(service_name):
    """Get detailed service status"""
    try:
        result = subprocess.run(
            ['systemctl', 'status', f'{service_name}.service'],
            capture_output=True,
            text=True
        )
        return {
            'success': True,
            'status': result.stdout,
            'returncode': result.returncode
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}

def find_config_file(service_name):
    """Find config file for service"""
    # Extract info from service name: @lvlRF-Tunnel-100-tcp-speed
    parts = service_name.replace('@lvlRF-Tunnel-', '').split('-')
    port = parts[0]
    
    # Try iran config
    for prefix in ['iran', 'kharej']:
        config_path = f"{BINARY_PATH}/{prefix}{port}-{'-'.join(parts[1:])}.toml"
        if os.path.exists(config_path):
            return config_path
    
    return None

def update_state_file(service_name, tunnel_port, web_port, iperf_port):
    """Update state.json with new ports"""
    try:
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
        
        for cfg in state['generated_configs']:
            if generate_service_name(cfg) == service_name:
                cfg['tunnel_port'] = int(tunnel_port)
                cfg['web_port'] = int(web_port)
                cfg['iperf_port'] = int(iperf_port)
                break
        
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)
    except:
        pass

# ============================================================================
# HTML Templates
# ============================================================================

LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ورود به داشبورد</title>
    <link href="https://cdn.jsdelivr.net/gh/rastikerdar/vazir-font@v30.1.0/dist/font-face.css" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Vazir', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .login-container {
            background: white;
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            width: 400px;
            text-align: center;
        }
        h1 { color: #667eea; margin-bottom: 30px; }
        input {
            width: 100%;
            padding: 15px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 16px;
            font-family: 'Vazir', sans-serif;
            margin-bottom: 20px;
        }
        input:focus { outline: none; border-color: #667eea; }
        button {
            width: 100%;
            padding: 15px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            font-family: 'Vazir', sans-serif;
        }
        button:hover { background: #5568d3; }
        .error {
            background: #f56565;
            color: white;
            padding: 10px;
            border-radius: 6px;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <h1>🚀 داشبورد تانل</h1>
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        <form method="POST">
            <input type="password" name="password" placeholder="رمز عبور" required autofocus>
            <button type="submit">ورود</button>
        </form>
    </div>
</body>
</html>
'''

DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>@lvlRF Tunnel Dashboard</title>
    <link href="https://cdn.jsdelivr.net/gh/rastikerdar/vazir-font@v30.1.0/dist/font-face.css" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        :root {
            --bg-primary: #f7fafc;
            --bg-secondary: #ffffff;
            --text-primary: #2d3748;
            --text-secondary: #718096;
            --accent: #667eea;
            --accent-hover: #5568d3;
            --success: #48bb78;
            --warning: #ed8936;
            --danger: #f56565;
            --info: #4299e1;
            --border: #e2e8f0;
        }
        
        body.dark-mode {
            --bg-primary: #1a202c;
            --bg-secondary: #2d3748;
            --text-primary: #f7fafc;
            --text-secondary: #cbd5e0;
            --border: #4a5568;
        }
        
        body {
            font-family: 'Vazir', sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            transition: all 0.3s;
        }
        
        .header {
            background: var(--bg-secondary);
            padding: 20px 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: sticky;
            top: 0;
            z-index: 100;
        }
        
        .header h1 {
            color: var(--accent);
            font-size: 1.5rem;
        }
        
        .header-actions {
            display: flex;
            gap: 10px;
            align-items: center;
        }
        
        .container {
            max-width: 1600px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .section {
            background: var(--bg-secondary);
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            margin-bottom: 20px;
        }
        
        .section-title {
            font-size: 1.2rem;
            margin-bottom: 15px;
            color: var(--text-primary);
        }
        
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.9rem;
            font-weight: 600;
            transition: all 0.3s;
            font-family: 'Vazir', sans-serif;
        }
        
        .btn:hover { transform: scale(1.05); }
        .btn-primary { background: var(--accent); color: white; }
        .btn-primary:hover { background: var(--accent-hover); }
        .btn-success { background: var(--success); color: white; }
        .btn-warning { background: var(--warning); color: white; }
        .btn-danger { background: var(--danger); color: white; }
        .btn-info { background: var(--info); color: white; }
        .btn-secondary { background: var(--text-secondary); color: white; }
        .btn-small { padding: 6px 12px; font-size: 0.85rem; }
        
        .action-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
        }
        
        .filters {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .filters input, .filters select {
            padding: 10px;
            border: 2px solid var(--border);
            border-radius: 6px;
            font-family: 'Vazir', sans-serif;
            background: var(--bg-secondary);
            color: var(--text-primary);
        }
        
        .configs-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(500px, 1fr));
            gap: 20px;
        }
        
        .config-card {
            background: var(--bg-secondary);
            border: 2px solid var(--border);
            border-radius: 10px;
            overflow: hidden;
            transition: transform 0.3s;
        }
        
        .config-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        }
        
        .config-header {
            padding: 15px;
            border-bottom: 2px solid var(--border);
        }
        
        .config-header h3 {
            font-size: 1rem;
            margin-bottom: 8px;
        }
        
        .config-info {
            font-size: 0.85rem;
            color: var(--text-secondary);
        }
        
        .status-badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
            margin-right: 8px;
        }
        
        .status-active {
            background: #c6f6d5;
            color: #22543d;
        }
        
        .status-inactive {
            background: #fed7d7;
            color: #742a2a;
        }
        
        .status-unknown {
            background: #e2e8f0;
            color: #2d3748;
        }
        
        body.dark-mode .status-active {
            background: #22543d;
            color: #c6f6d5;
        }
        
        body.dark-mode .status-inactive {
            background: #742a2a;
            color: #fed7d7;
        }
        
        .config-body {
            padding: 15px;
        }
        
        .config-section {
            margin-bottom: 12px;
        }
        
        .config-section-title {
            font-size: 0.8rem;
            color: var(--text-secondary);
            margin-bottom: 6px;
            font-weight: 600;
        }
        
        .button-row {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 6px;
            margin-bottom: 10px;
        }
        
        .button-row:last-child {
            margin-bottom: 0;
        }
        
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.7);
        }
        
        .modal.show {
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .modal-content {
            background: var(--bg-secondary);
            padding: 30px;
            border-radius: 10px;
            max-width: 800px;
            max-height: 80vh;
            overflow-y: auto;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            width: 90%;
        }
        
        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .modal-header h2 {
            color: var(--accent);
        }
        
        .close-btn {
            background: var(--danger);
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
        }
        
        pre {
            background: #1a202c;
            color: #f7fafc;
            padding: 15px;
            border-radius: 6px;
            overflow-x: auto;
            font-size: 0.85rem;
            direction: ltr;
            text-align: left;
        }
        
        .form-group {
            margin-bottom: 15px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: 600;
        }
        
        .form-group input {
            width: 100%;
            padding: 10px;
            border: 2px solid var(--border);
            border-radius: 6px;
            font-family: 'Vazir', sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
        }
        
        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            background: white;
            padding: 15px 25px;
            border-radius: 8px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            z-index: 2000;
            display: none;
            animation: slideIn 0.3s ease;
        }
        
        .notification.show { display: block; }
        .notification.success { border-right: 5px solid var(--success); }
        .notification.error { border-right: 5px solid var(--danger); }
        
        @keyframes slideIn {
            from { transform: translateX(400px); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        
        .loading {
            text-align: center;
            padding: 60px;
            font-size: 1.5rem;
        }
        
        @media (max-width: 768px) {
            .configs-grid { grid-template-columns: 1fr; }
            .action-grid { grid-template-columns: 1fr; }
            .button-row { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 @lvlRF Tunnel Dashboard</h1>
        <div class="header-actions">
            <span id="refresh-status">Auto-refresh: {{ refresh_interval }}s</span>
            <button class="btn btn-small btn-secondary" onclick="toggleDarkMode()">🌙</button>
            <button class="btn btn-small btn-info" onclick="showDashboardControl()">⚙️ Dashboard</button>
            <button class="btn btn-small btn-danger" onclick="logout()">خروج</button>
        </div>
    </div>
    
    <div class="container">
        <div class="section">
            <h2 class="section-title">عملیات سریع</h2>
            <div class="action-grid">
                <button class="btn btn-info" onclick="bulkAction('start')">▶️ استارت همه</button>
                <button class="btn btn-warning" onclick="bulkAction('stop')">⏸️ استاپ همه</button>
                <button class="btn btn-success" onclick="bulkAction('restart')">🔄 ری‌استارت همه</button>
            </div>
        </div>
        
        <div class="section">
            <h2 class="section-title">فیلتر</h2>
            <div class="filters">
                <input type="text" id="searchInput" placeholder="جستجو..." onkeyup="filterConfigs()">
                <select id="serverFilter" onchange="filterConfigs()">
                    <option value="">همه سرورها</option>
                </select>
                <select id="transportFilter" onchange="filterConfigs()">
                    <option value="">همه Transport ها</option>
                </select>
                <select id="statusFilter" onchange="filterConfigs()">
                    <option value="">همه وضعیت‌ها</option>
                    <option value="active">فعال</option>
                    <option value="inactive">غیرفعال</option>
                </select>
            </div>
        </div>
        
        <div id="loading" class="loading">در حال بارگذاری...</div>
        <div id="configs-container" class="configs-grid" style="display: none;"></div>
    </div>
    
    <div id="notification" class="notification"></div>
    
    <!-- Logs Modal -->
    <div id="logsModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2>لاگ‌ها</h2>
                <button class="close-btn" onclick="closeModal('logsModal')">✕</button>
            </div>
            <pre id="logsContent"></pre>
        </div>
    </div>
    
    <!-- Edit Modal -->
    <div id="editModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2>ویرایش پورت‌ها</h2>
                <button class="close-btn" onclick="closeModal('editModal')">✕</button>
            </div>
            <form id="editForm" onsubmit="saveEdit(event)">
                <input type="hidden" id="edit-service">
                <div class="form-group">
                    <label>پورت تانل:</label>
                    <input type="number" id="edit-tunnel-port" required>
                </div>
                <div class="form-group">
                    <label>پورت وب:</label>
                    <input type="number" id="edit-web-port" required>
                </div>
                <div class="form-group">
                    <label>پورت iperf:</label>
                    <input type="number" id="edit-iperf-port" required>
                </div>
                <button type="submit" class="btn btn-success">ذخیره و ری‌استارت</button>
            </form>
        </div>
    </div>
    
    <!-- Test Speed Modal -->
    <div id="testModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2>تست سرعت</h2>
                <button class="close-btn" onclick="closeModal('testModal')">✕</button>
            </div>
            <div id="testContent"></div>
        </div>
    </div>
    
    <!-- Dashboard Control Modal -->
    <div id="dashboardModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2>مدیریت Dashboard Service</h2>
                <button class="close-btn" onclick="closeModal('dashboardModal')">✕</button>
            </div>
            <div id="dashboardStatus" style="margin-bottom: 20px;"></div>
            <div class="button-row">
                <button class="btn btn-success" onclick="dashboardControl('enable')">فعال‌سازی</button>
                <button class="btn btn-danger" onclick="dashboardControl('disable')">غیرفعال‌سازی</button>
            </div>
            <hr style="margin: 20px 0;">
            <h3 style="margin-bottom: 10px;">دستورات دستی:</h3>
            <pre>systemctl enable lvlrf-dashboard.service
systemctl start lvlrf-dashboard.service

systemctl disable lvlrf-dashboard.service
systemctl stop lvlrf-dashboard.service

systemctl status lvlrf-dashboard.service</pre>
        </div>
    </div>
    
    <script>
        let allConfigs = [];
        let refreshInterval = {{ refresh_interval }} * 1000;
        let refreshTimer;
        
        function loadConfigs() {
            fetch('/api/configs')
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        allConfigs = data.configs;
                        populateFilters();
                        renderConfigs(allConfigs);
                        document.getElementById('loading').style.display = 'none';
                        document.getElementById('configs-container').style.display = 'grid';
                    }
                });
        }
        
        function populateFilters() {
            const servers = new Set();
            const transports = new Set();
            
            allConfigs.forEach(c => {
                servers.add(c.iran);
                servers.add(c.kharej);
                transports.add(c.transport);
            });
            
            const serverFilter = document.getElementById('serverFilter');
            serverFilter.innerHTML = '<option value="">همه سرورها</option>';
            Array.from(servers).sort().forEach(s => {
                serverFilter.innerHTML += `<option value="${s}">${s}</option>`;
            });
            
            const transportFilter = document.getElementById('transportFilter');
            transportFilter.innerHTML = '<option value="">همه Transport ها</option>';
            Array.from(transports).sort().forEach(t => {
                transportFilter.innerHTML += `<option value="${t}">${t.toUpperCase()}</option>`;
            });
        }
        
        function renderConfigs(configs) {
            const container = document.getElementById('configs-container');
            
            if (configs.length === 0) {
                container.innerHTML = '<div style="text-align:center;padding:40px;">هیچ نتیجه‌ای یافت نشد</div>';
                return;
            }
            
            container.innerHTML = configs.map(cfg => {
                const statusClass = cfg.status === 'active' ? 'status-active' : 
                                   cfg.status === 'inactive' ? 'status-inactive' : 'status-unknown';
                const statusText = cfg.status === 'active' ? '● فعال' : 
                                  cfg.status === 'inactive' ? '○ غیرفعال' : '⚠ نامعلوم';
                
                const transportDisplay = cfg.mux_version ? 
                    `${cfg.transport.toUpperCase()}-V${cfg.mux_version}` : 
                    cfg.transport.toUpperCase();
                
                return `
                    <div class="config-card">
                        <div class="config-header">
                            <h3>${cfg.service_name}</h3>
                            <div class="config-info">
                                <span class="status-badge ${statusClass}">${statusText}</span>
                                ${cfg.iran} (${cfg.iran_ip}) ↔ ${cfg.kharej} (${cfg.kharej_ip})
                            </div>
                            <div class="config-info" style="margin-top: 5px;">
                                ${transportDisplay} | ${cfg.profile.toUpperCase()} | 
                                Port: ${cfg.tunnel_port} | Web: ${cfg.web_port} | iperf: ${cfg.iperf_port}
                            </div>
                        </div>
                        <div class="config-body">
                            <div class="config-section">
                                <div class="config-section-title">وب پنل:</div>
                                <div class="button-row">
                                    <button class="btn btn-primary btn-small" onclick="openWeb('${cfg.iran_ip}', ${cfg.web_port})">
                                        🌐 ${cfg.iran}
                                    </button>
                                    <button class="btn btn-primary btn-small" onclick="openWeb('${cfg.kharej_ip}', ${cfg.web_port})">
                                        🌐 ${cfg.kharej}
                                    </button>
                                </div>
                            </div>
                            
                            <div class="config-section">
                                <div class="config-section-title">مدیریت سرویس:</div>
                                <div class="button-row">
                                    <button class="btn btn-success btn-small" onclick="serviceAction('start', '${cfg.service_name}')">
                                        ▶️ استارت
                                    </button>
                                    <button class="btn btn-warning btn-small" onclick="serviceAction('stop', '${cfg.service_name}')">
                                        ⏸️ استاپ
                                    </button>
                                </div>
                                <div class="button-row">
                                    <button class="btn btn-success btn-small" onclick="serviceAction('restart', '${cfg.service_name}')">
                                        🔄 ری‌استارت
                                    </button>
                                    <button class="btn btn-info btn-small" onclick="serviceAction('status', '${cfg.service_name}')">
                                        📊 وضعیت
                                    </button>
                                </div>
                            </div>
                            
                            <div class="config-section">
                                <div class="config-section-title">عملیات:</div>
                                <div class="button-row">
                                    <button class="btn btn-secondary btn-small" onclick="showLogs('${cfg.service_name}')">
                                        📜 لاگ
                                    </button>
                                    <button class="btn btn-info btn-small" onclick="showEdit('${cfg.service_name}', ${cfg.tunnel_port}, ${cfg.web_port}, ${cfg.iperf_port})">
                                        ✏️ ویرایش
                                    </button>
                                </div>
                                <div class="button-row">
                                    <button class="btn btn-primary btn-small" onclick="showTestSpeed(${cfg.iperf_port}, '${cfg.iran}', '${cfg.kharej}')">
                                        ⚡ تست سرعت
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            }).join('');
        }
        
        function filterConfigs() {
            const search = document.getElementById('searchInput').value.toLowerCase();
            const server = document.getElementById('serverFilter').value;
            const transport = document.getElementById('transportFilter').value;
            const status = document.getElementById('statusFilter').value;
            
            const filtered = allConfigs.filter(cfg => {
                const matchSearch = cfg.service_name.toLowerCase().includes(search) ||
                                  cfg.iran.toLowerCase().includes(search) ||
                                  cfg.kharej.toLowerCase().includes(search);
                const matchServer = !server || cfg.iran === server || cfg.kharej === server;
                const matchTransport = !transport || cfg.transport === transport;
                const matchStatus = !status || cfg.status === status;
                
                return matchSearch && matchServer && matchTransport && matchStatus;
            });
            
            renderConfigs(filtered);
        }
        
        function openWeb(ip, port) {
            window.open(`http://${ip}:${port}`, '_blank');
        }
        
        function serviceAction(action, service) {
            fetch(`/api/service/${action}/${service}`)
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        showNotification(`✅ ${action} انجام شد`, 'success');
                        if (action !== 'status') {
                            setTimeout(loadConfigs, 1000);
                        }
                    } else {
                        showNotification(`❌ خطا: ${data.error || data.message}`, 'error');
                    }
                    
                    if (action === 'status' && data.status) {
                        alert(data.status);
                    }
                });
        }
        
        function bulkAction(action) {
            if (!confirm(`آیا مطمئن هستید؟`)) return;
            
            fetch(`/api/bulk/${action}`)
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        showNotification(`✅ ${data.message}`, 'success');
                        setTimeout(loadConfigs, 2000);
                    } else {
                        showNotification(`❌ خطا: ${data.error}`, 'error');
                    }
                });
        }
        
        function showLogs(service) {
            fetch(`/api/logs/${service}`)
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        document.getElementById('logsContent').textContent = data.logs;
                        showModal('logsModal');
                    } else {
                        showNotification(`❌ خطا: ${data.error}`, 'error');
                    }
                });
        }
        
        function showEdit(service, tunnel, web, iperf) {
            document.getElementById('edit-service').value = service;
            document.getElementById('edit-tunnel-port').value = tunnel;
            document.getElementById('edit-web-port').value = web;
            document.getElementById('edit-iperf-port').value = iperf;
            showModal('editModal');
        }
        
        function saveEdit(e) {
            e.preventDefault();
            
            const data = {
                service_name: document.getElementById('edit-service').value,
                tunnel_port: document.getElementById('edit-tunnel-port').value,
                web_port: document.getElementById('edit-web-port').value,
                iperf_port: document.getElementById('edit-iperf-port').value
            };
            
            fetch('/api/edit-port', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            })
            .then(r => r.json())
            .then(resp => {
                if (resp.success) {
                    showNotification('✅ پورت‌ها بروزرسانی شد', 'success');
                    closeModal('editModal');
                    setTimeout(loadConfigs, 2000);
                } else {
                    showNotification(`❌ خطا: ${resp.error}`, 'error');
                }
            });
        }
        
        function showTestSpeed(port, iran, kharej) {
            const content = `
                <h3 style="margin-bottom: 15px;">🔴 سرور ${iran}:</h3>
                <div style="margin-bottom: 20px;">
                    <p><strong>مرحله 1: راه‌اندازی سرور iperf3</strong></p>
                    <pre style="cursor: pointer;" onclick="copyText(this)">iperf3 -s -B 127.0.0.1 -p ${port}</pre>
                    
                    <p style="margin-top: 15px;"><strong>مرحله 2: تست سرعت دانلود (از Kharej)</strong></p>
                    <pre style="cursor: pointer;" onclick="copyText(this)">iperf3 -c 127.0.0.1 -p ${port} -t 30</pre>
                    
                    <p style="margin-top: 15px;"><strong>مرحله 3: تست سرعت آپلود (به Kharej)</strong></p>
                    <pre style="cursor: pointer;" onclick="copyText(this)">iperf3 -c 127.0.0.1 -p ${port} -t 30 -R</pre>
                </div>
                
                <h3 style="margin-bottom: 15px;">🟢 سرور ${kharej}:</h3>
                <div>
                    <p><strong>راه‌اندازی سرور iperf3</strong></p>
                    <pre style="cursor: pointer;" onclick="copyText(this)">iperf3 -s -B 127.0.0.1 -p 5201</pre>
                </div>
                
                <p style="margin-top: 20px; padding: 10px; background: var(--warning); color: white; border-radius: 6px;">
                    💡 نکته: روی هر دستور کلیک کنید تا کپی شود
                </p>
            `;
            
            document.getElementById('testContent').innerHTML = content;
            showModal('testModal');
        }
        
        function showDashboardControl() {
            fetch('/api/dashboard/control/status')
                .then(r => r.json())
                .then(data => {
                    const statusHtml = `
                        <div style="padding: 15px; background: var(--bg-primary); border-radius: 6px;">
                            <p><strong>وضعیت:</strong> ${data.active ? '✅ فعال' : '❌ غیرفعال'}</p>
                            <p><strong>Enabled:</strong> ${data.enabled ? 'Yes' : 'No'}</p>
                        </div>
                    `;
                    document.getElementById('dashboardStatus').innerHTML = statusHtml;
                    showModal('dashboardModal');
                });
        }
        
        function dashboardControl(action) {
            fetch(`/api/dashboard/control/${action}`)
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        showNotification(`✅ ${data.message}`, 'success');
                        showDashboardControl();
                    } else {
                        showNotification(`❌ خطا: ${data.error}`, 'error');
                    }
                });
        }
        
        function copyText(element) {
            const text = element.textContent;
            navigator.clipboard.writeText(text).then(() => {
                showNotification('✅ کپی شد', 'success');
            });
        }
        
        function showModal(id) {
            document.getElementById(id).classList.add('show');
        }
        
        function closeModal(id) {
            document.getElementById(id).classList.remove('show');
        }
        
        function showNotification(message, type) {
            const notif = document.getElementById('notification');
            notif.textContent = message;
            notif.className = `notification ${type} show`;
            setTimeout(() => notif.classList.remove('show'), 3000);
        }
        
        function toggleDarkMode() {
            document.body.classList.toggle('dark-mode');
            localStorage.setItem('darkMode', document.body.classList.contains('dark-mode'));
        }
        
        function logout() {
            window.location.href = '/logout';
        }
        
        function startAutoRefresh() {
            refreshTimer = setInterval(loadConfigs, refreshInterval);
        }
        
        function stopAutoRefresh() {
            clearInterval(refreshTimer);
        }
        
        // Initialize
        window.addEventListener('DOMContentLoaded', () => {
            if (localStorage.getItem('darkMode') === 'true') {
                document.body.classList.add('dark-mode');
            }
            
            loadConfigs();
            startAutoRefresh();
        });
    </script>
</body>
</html>
'''

# ============================================================================
# Main
# ============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("@lvlRF Tunnel Management Dashboard")
    print("=" * 60)
    print(f"Port: {DASHBOARD_PORT}")
    print(f"Auto-refresh: {AUTO_REFRESH_SECONDS}s")
    print(f"Binary path: {BINARY_PATH}")
    print(f"⚠️  Change PASSWORD in the code before deploying!")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=DASHBOARD_PORT, debug=False)
