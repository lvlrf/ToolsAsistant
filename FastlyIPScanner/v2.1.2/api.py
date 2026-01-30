#!/usr/bin/env python3
"""
Dr.CDN-Scanner - Collection API Server
Version: 2.2
Developed by: DrConnect
Telegram: @lvlRF | Channel: @drconnect

Description:
API server to collect scan results from distributed scanners.
Supports multiple test types: port, tls, real, download, udp, dns, dnstt

Changes in v2.2:
- Added DNSTT test type support
- Added /download route (alias for /dl)

Changes in v2.1:
- Fixed /dl page to show txt/html in browser
- Fixed Aggregate button functionality
- Added protocol field (tcp/udp)
"""

from flask import Flask, request, jsonify, send_file, Response
import json
import os
import hashlib
import time
from datetime import datetime
from collections import defaultdict
import threading
import mimetypes

app = Flask(__name__)

# ==================== CONFIGURATION ====================

VERSION = "2.2"

# Obfuscated SECRET_KEY
_k = [68, 114, 67, 111, 110, 110, 101, 99, 116, 95, 70, 97, 115, 116, 108, 121, 95, 50, 48, 50, 53, 95, 83, 101, 99, 117, 114, 101, 95, 75, 101, 121, 95, 88, 55, 57, 51]
SECRET_KEY = ''.join(chr(c) for c in _k)

# Directories
SUBMISSIONS_DIR = 'submissions'
AGGREGATED_DIR = 'aggregated'
DOWNLOADS_DIR = '/opt/fastly-collector/dl'
STATS_FILE = 'stats.json'

# Settings
MAX_SUBMISSION_SIZE = 5 * 1024 * 1024  # 5MB
TOKEN_VALIDITY = 86400  # 24 hours
RATE_LIMIT_WINDOW = 3600  # 1 hour
MAX_SUBMISSIONS_PER_HOUR = 30

# Valid test types
VALID_TEST_TYPES = ['port', 'tls', 'real', 'download', 'udp', 'dns', 'dnstt', 1, 2, 3, 4, 5, 6, 7]

# Rate limiting storage
rate_limit_storage = defaultdict(list)
rate_limit_lock = threading.Lock()

# ==================== UTILITY FUNCTIONS ====================

def init_directories():
    """Initialize required directories"""
    os.makedirs(SUBMISSIONS_DIR, exist_ok=True)
    os.makedirs(AGGREGATED_DIR, exist_ok=True)
    os.makedirs(DOWNLOADS_DIR, exist_ok=True)
    
    if not os.path.exists(STATS_FILE):
        with open(STATS_FILE, 'w') as f:
            json.dump({
                'total_submissions': 0,
                'total_tests': 0,
                'total_successful_ips': 0,
                'by_test_type': {},
                'by_cdn': {},
                'by_protocol': {'tcp': 0, 'udp': 0},
                'scanner_versions': {},
                'last_updated': datetime.now().isoformat() + 'Z'
            }, f, indent=2)

def get_stats():
    """Get current statistics"""
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {}

def normalize_test_type(test_type):
    """Normalize test_type to string format"""
    type_map = {1: 'port', 2: 'tls', 3: 'real', 4: 'download', 5: 'udp', 6: 'dns', 7: 'dnstt'}
    if isinstance(test_type, int):
        return type_map.get(test_type, 'port')
    return str(test_type) if test_type else 'port'

def update_stats(submission_data):
    """Update statistics with new submission"""
    stats = get_stats()
    
    # Basic counts
    stats['total_submissions'] = stats.get('total_submissions', 0) + 1
    stats['total_tests'] = stats.get('total_tests', 0) + 1
    stats['total_successful_ips'] = stats.get('total_successful_ips', 0) + len(submission_data.get('results', []))
    stats['last_updated'] = datetime.now().isoformat() + 'Z'
    
    # Initialize nested dicts if missing
    if 'by_test_type' not in stats:
        stats['by_test_type'] = {}
    if 'by_cdn' not in stats:
        stats['by_cdn'] = {}
    if 'by_protocol' not in stats:
        stats['by_protocol'] = {'tcp': 0, 'udp': 0}
    if 'scanner_versions' not in stats:
        stats['scanner_versions'] = {}
    
    # Track by test type, CDN, and protocol
    for result in submission_data.get('results', []):
        # Test type
        test_type = normalize_test_type(result.get('test_type', 'port'))
        if test_type not in stats['by_test_type']:
            stats['by_test_type'][test_type] = 0
        stats['by_test_type'][test_type] += 1
        
        # CDN type
        cdn = result.get('cdn', 'unknown')
        if cdn not in stats['by_cdn']:
            stats['by_cdn'][cdn] = 0
        stats['by_cdn'][cdn] += 1
        
        # Protocol
        protocol = result.get('protocol', 'tcp')
        if protocol not in stats['by_protocol']:
            stats['by_protocol'][protocol] = 0
        stats['by_protocol'][protocol] += 1
    
    # Scanner version
    version = submission_data.get('scanner_version', '1.0')
    if version not in stats['scanner_versions']:
        stats['scanner_versions'][version] = 0
    stats['scanner_versions'][version] += 1
    
    with open(STATS_FILE, 'w') as f:
        json.dump(stats, f, indent=2)

def generate_token(timestamp):
    """Generate authentication token"""
    data = f"{timestamp}{SECRET_KEY}"
    return hashlib.sha256(data.encode()).hexdigest()

def validate_token(timestamp, token):
    """Validate authentication token"""
    try:
        ts = int(timestamp)
        current_time = int(time.time())
        
        if abs(current_time - ts) > TOKEN_VALIDITY:
            return False, "Token expired"
        
        expected_token = generate_token(timestamp)
        if token != expected_token:
            return False, "Invalid token"
        
        return True, "OK"
    except Exception as e:
        return False, str(e)

def check_rate_limit(client_ip):
    """Check rate limit"""
    with rate_limit_lock:
        current_time = time.time()
        
        rate_limit_storage[client_ip] = [
            t for t in rate_limit_storage[client_ip]
            if current_time - t < RATE_LIMIT_WINDOW
        ]
        
        if len(rate_limit_storage[client_ip]) >= MAX_SUBMISSIONS_PER_HOUR:
            return False
        
        rate_limit_storage[client_ip].append(current_time)
        return True

def validate_submission(data):
    """Validate submission data structure"""
    required_fields = ['timestamp', 'public_ip', 'results']
    
    for field in required_fields:
        if field not in data:
            return False, f"Missing field: {field}"
    
    if not isinstance(data['results'], list):
        return False, "Results must be a list"
    
    # Allow empty results for scan statistics
    if len(data['results']) == 0:
        return True, "OK"
    
    # Validate result items
    for result in data['results']:
        if not isinstance(result, dict):
            return False, "Each result must be a dictionary"
        if 'ip' not in result or 'port' not in result:
            return False, "Each result must have 'ip' and 'port'"
    
    return True, "OK"

def save_submission(data, client_ip):
    """Save submission to file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    public_ip = data['public_ip'].replace('.', '_').replace(':', '_')
    filename = f"{SUBMISSIONS_DIR}/{public_ip}_{timestamp}.json"
    
    # Add metadata
    data['received_at'] = datetime.now().isoformat() + 'Z'
    data['client_ip'] = client_ip
    data['api_version'] = VERSION
    
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    
    return filename

# ==================== API ENDPOINTS ====================

@app.route('/timestamp', methods=['GET'])
def get_timestamp():
    """Get current timestamp for token generation"""
    return jsonify({
        'timestamp': int(time.time()),
        'status': 'ok',
        'api_version': VERSION
    })

@app.route('/myip', methods=['GET'])
def get_client_ip():
    """Get client's public IP address"""
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if ',' in client_ip:
        client_ip = client_ip.split(',')[0].strip()
    return client_ip

@app.route('/submit', methods=['POST'])
def submit_results():
    """
    Submit scan results
    
    Expected JSON:
    {
        "timestamp": <int>,
        "token": "<hash>",
        "public_ip": "<ip>",
        "scan_duration": <float>,
        "scanner_version": "2.1",
        "total_successful": <int>,
        "results": [
            {
                "ip": "...",
                "port": ...,
                "protocol": "tcp",  // tcp or udp
                "test_type": "real",  // port, tls, real, download, udp, dns
                "delay_ms": 234,
                "download_speed": 1250,
                "cdn": "fastly",
                "is_official": true
            }
        ]
    }
    """
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if ',' in client_ip:
        client_ip = client_ip.split(',')[0].strip()
    
    # Check content size
    if len(request.data) > MAX_SUBMISSION_SIZE:
        return jsonify({'status': 'error', 'message': 'Submission too large'}), 413
    
    # Check rate limit
    if not check_rate_limit(client_ip):
        return jsonify({'status': 'error', 'message': 'Rate limit exceeded'}), 429
    
    # Parse JSON
    try:
        data = request.json
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Invalid JSON: {str(e)}'}), 400
    
    # Validate token
    timestamp = data.get('timestamp')
    token = data.get('token')
    
    if not timestamp or not token:
        return jsonify({'status': 'error', 'message': 'Missing timestamp or token'}), 401
    
    valid, msg = validate_token(timestamp, token)
    if not valid:
        return jsonify({'status': 'error', 'message': msg}), 401
    
    # Validate submission structure
    valid, msg = validate_submission(data)
    if not valid:
        return jsonify({'status': 'error', 'message': msg}), 400
    
    # Save submission
    try:
        filename = save_submission(data, client_ip)
        update_stats(data)
        
        return jsonify({
            'status': 'ok',
            'message': 'Submission received',
            'filename': os.path.basename(filename),
            'count': len(data.get('results', []))
        }), 200
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to save: {str(e)}'}), 500

@app.route('/stats', methods=['GET'])
def get_statistics():
    """Get current statistics (public)"""
    stats = get_stats()
    
    return jsonify({
        'total_submissions': stats.get('total_submissions', 0),
        'total_tests': stats.get('total_tests', 0),
        'total_successful_ips': stats.get('total_successful_ips', 0),
        'by_test_type': stats.get('by_test_type', {}),
        'by_cdn': stats.get('by_cdn', {}),
        'by_protocol': stats.get('by_protocol', {}),
        'last_updated': stats.get('last_updated', 'N/A'),
        'api_version': VERSION
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat() + 'Z',
        'api_version': VERSION
    })

@app.route('/', methods=['GET'])
def index():
    """Serve dashboard or API info"""
    dashboard_path = 'dashboard.html'
    if os.path.exists(dashboard_path):
        with open(dashboard_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dr.CDN-Scanner - API</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }}
            .container {{
                background: white;
                padding: 30px;
                border-radius: 15px;
                box-shadow: 0 10px 50px rgba(0,0,0,0.2);
            }}
            h1 {{ color: #333; border-bottom: 3px solid #667eea; padding-bottom: 15px; }}
            .endpoint {{
                background: #f8f9fa;
                padding: 15px;
                margin: 10px 0;
                border-left: 4px solid #667eea;
                border-radius: 4px;
            }}
            .badge {{
                background: #667eea;
                color: white;
                padding: 3px 8px;
                border-radius: 10px;
                font-size: 0.8em;
            }}
            .footer {{
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #ddd;
                text-align: center;
                color: #666;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Dr.CDN-Scanner - API <span class="badge">v{VERSION}</span></h1>
            <p>API server for collecting CDN scan results.</p>
            
            <h2>Endpoints:</h2>
            <div class="endpoint"><strong>GET /timestamp</strong> - Get server timestamp</div>
            <div class="endpoint"><strong>GET /myip</strong> - Get your public IP</div>
            <div class="endpoint"><strong>POST /submit</strong> - Submit scan results</div>
            <div class="endpoint"><strong>GET /stats</strong> - Get statistics</div>
            <div class="endpoint"><strong>GET /health</strong> - Health check</div>
            <div class="endpoint"><strong>GET /dl/</strong> - Downloads page</div>
            <div class="endpoint"><strong>GET /aggregated/results.json</strong> - Get results</div>
            
            <div class="footer">
                <p>Developed by: <strong>DrConnect</strong></p>
                <p>Channel: <a href="https://t.me/drconnect">@drconnect</a></p>
            </div>
        </div>
    </body>
    </html>
    """

@app.route('/aggregated/<path:filename>', methods=['GET'])
def serve_aggregated(filename):
    """Serve aggregated result files"""
    aggregated_path = os.path.join(AGGREGATED_DIR, filename)
    
    if not os.path.exists(aggregated_path):
        return jsonify({'error': 'File not found'}), 404
    
    response = send_file(aggregated_path, mimetype='application/json')
    response.headers['Cache-Control'] = 'no-cache, must-revalidate'
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

@app.route('/dl/', methods=['GET'])
@app.route('/dl', methods=['GET'])
@app.route('/download/', methods=['GET'])
@app.route('/download', methods=['GET'])
def downloads_index():
    """Show downloads directory listing"""
    if not os.path.exists(DOWNLOADS_DIR):
        os.makedirs(DOWNLOADS_DIR, exist_ok=True)
    
    files = []
    for f in os.listdir(DOWNLOADS_DIR):
        filepath = os.path.join(DOWNLOADS_DIR, f)
        if os.path.isfile(filepath):
            stat = os.stat(filepath)
            files.append({
                'name': f,
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M')
            })
    
    files.sort(key=lambda x: x['name'])
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Downloads - Dr.CDN-Scanner</title>
        <meta charset="UTF-8">
        <style>
            body { font-family: Arial, sans-serif; max-width: 900px; margin: 40px auto; padding: 20px; background: #f5f5f5; }
            .container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #333; border-bottom: 2px solid #667eea; padding-bottom: 10px; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th { background: #667eea; color: white; padding: 12px; text-align: left; }
            td { padding: 10px; border-bottom: 1px solid #eee; }
            tr:hover { background: #f8f9fa; }
            a { color: #667eea; text-decoration: none; }
            a:hover { text-decoration: underline; }
            .size { color: #666; font-size: 0.9em; }
            .date { color: #999; font-size: 0.85em; }
            .icon { margin-right: 8px; }
            .empty { text-align: center; color: #999; padding: 40px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📁 Downloads</h1>
    """
    
    if files:
        html += """
            <table>
                <tr><th>File</th><th>Size</th><th>Modified</th></tr>
        """
        
        for f in files:
            ext = f['name'].split('.')[-1].lower() if '.' in f['name'] else ''
            icon = '📄'
            if ext in ['zip', 'rar', '7z', 'tar', 'gz']:
                icon = '📦'
            elif ext in ['py']:
                icon = '🐍'
            elif ext in ['txt', 'md']:
                icon = '📝'
            elif ext in ['html', 'htm']:
                icon = '🌐'
            elif ext in ['json']:
                icon = '📋'
            elif ext in ['exe']:
                icon = '⚙️'
            
            # Format size
            size = f['size']
            if size >= 1024 * 1024:
                size_str = f"{size / (1024*1024):.1f} MB"
            elif size >= 1024:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size} B"
            
            html += f"""
                <tr>
                    <td><span class="icon">{icon}</span><a href="/dl/{f['name']}">{f['name']}</a></td>
                    <td class="size">{size_str}</td>
                    <td class="date">{f['modified']}</td>
                </tr>
            """
        
        html += "</table>"
    else:
        html += '<div class="empty">No files available</div>'
    
    html += """
        </div>
    </body>
    </html>
    """
    
    return html

@app.route('/dl/<path:filename>', methods=['GET'])
@app.route('/download/<path:filename>', methods=['GET'])
def download_file(filename):
    """Serve files - show txt/html in browser, download others"""
    file_path = os.path.join(DOWNLOADS_DIR, filename)
    
    # Security: prevent directory traversal
    if '..' in filename or filename.startswith('/'):
        return jsonify({'error': 'Invalid filename'}), 400
    
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
    
    # Get file extension
    ext = filename.split('.')[-1].lower() if '.' in filename else ''
    
    # Files to display in browser (not download)
    display_extensions = ['txt', 'html', 'htm', 'md', 'json', 'xml', 'css', 'js', 'log']
    
    if ext in display_extensions:
        # Read and display in browser
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if ext == 'html' or ext == 'htm':
                return content
            elif ext == 'json':
                return Response(content, mimetype='application/json')
            elif ext == 'md':
                # Simple markdown display
                html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>{filename}</title>
                    <style>
                        body {{ font-family: monospace; max-width: 900px; margin: 40px auto; padding: 20px; background: #f5f5f5; }}
                        pre {{ background: white; padding: 20px; border-radius: 5px; overflow-x: auto; white-space: pre-wrap; }}
                    </style>
                </head>
                <body>
                    <h2>{filename}</h2>
                    <pre>{content}</pre>
                </body>
                </html>
                """
                return html
            else:
                # Plain text
                return Response(content, mimetype='text/plain; charset=utf-8')
        except UnicodeDecodeError:
            # Binary file, force download
            pass
    
    # Download other files
    mimetype = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
    return send_file(file_path, mimetype=mimetype, as_attachment=True, download_name=filename)

@app.route('/api/aggregate', methods=['POST', 'GET'])
def trigger_aggregation():
    """Trigger aggregation process"""
    try:
        import subprocess
        
        api_dir = os.path.dirname(os.path.abspath(__file__))
        aggregator_path = os.path.join(api_dir, 'aggregator.py')
        
        if not os.path.exists(aggregator_path):
            return jsonify({
                'status': 'error',
                'message': f'aggregator.py not found at {aggregator_path}'
            }), 404
        
        # Run aggregator.py
        result = subprocess.run(
            ['python3', aggregator_path],
            cwd=api_dir,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            return jsonify({
                'status': 'ok',
                'message': 'Aggregation completed successfully',
                'output': result.stdout[-500:] if len(result.stdout) > 500 else result.stdout
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Aggregation failed',
                'error': result.stderr[-500:] if len(result.stderr) > 500 else result.stderr,
                'returncode': result.returncode
            }), 500
    
    except subprocess.TimeoutExpired:
        return jsonify({'status': 'error', 'message': 'Aggregation timed out (60s)'}), 408
    except FileNotFoundError:
        return jsonify({'status': 'error', 'message': 'python3 not found'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ==================== MAIN ====================

if __name__ == '__main__':
    init_directories()
    
    print("="*50)
    print(f"Dr.CDN-Scanner - Collection API v{VERSION}")
    print("Developed by: DrConnect")
    print("="*50)
    print(f"\nSubmissions: {SUBMISSIONS_DIR}")
    print(f"Aggregated: {AGGREGATED_DIR}")
    print(f"Downloads: {DOWNLOADS_DIR}")
    print("\nStarting server on 0.0.0.0:8080...")
    print("="*50)
    
    app.run(host='0.0.0.0', port=8080, debug=False)
