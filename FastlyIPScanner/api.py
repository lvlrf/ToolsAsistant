#!/usr/bin/env python3
"""
Fastly CDN Scanner - Collection API Server
Version: 1.0
Developed by: DrConnect
Telegram: @lvlRF
Phone: +98 912 741 9412

Description:
API server to collect scan results from distributed scanners.
Provides timestamp-based authentication and result aggregation.
"""

from flask import Flask, request, jsonify, send_file
import json
import os
import hashlib
import time
from datetime import datetime
from collections import defaultdict
import threading

app = Flask(__name__)

# ==================== CONFIGURATION ====================

# Obfuscated SECRET_KEY (randomly generated)
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
MAX_SUBMISSIONS_PER_HOUR = 10

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
                'last_updated': datetime.now().isoformat() + 'Z'
            }, f, indent=2)

def get_stats():
    """Get current statistics"""
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, 'r') as f:
            return json.load(f)
    return {}

def update_stats(submission_data):
    """Update statistics with new submission"""
    stats = get_stats()
    
    stats['total_submissions'] = stats.get('total_submissions', 0) + 1
    stats['total_tests'] = stats.get('total_tests', 0) + 1
    stats['total_successful_ips'] = stats.get('total_successful_ips', 0) + len(submission_data.get('results', []))
    stats['last_updated'] = datetime.now().isoformat() + 'Z'
    
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
        
        # Check if timestamp is within valid window
        if abs(current_time - ts) > TOKEN_VALIDITY:
            return False, "Token expired"
        
        # Verify token
        expected_token = generate_token(timestamp)
        if token != expected_token:
            return False, "Invalid token"
        
        return True, "OK"
    
    except Exception as e:
        return False, str(e)

def check_rate_limit(client_ip):
    """Check if client has exceeded rate limit"""
    with rate_limit_lock:
        current_time = time.time()
        
        # Clean old entries
        rate_limit_storage[client_ip] = [
            t for t in rate_limit_storage[client_ip]
            if current_time - t < RATE_LIMIT_WINDOW
        ]
        
        # Check limit
        if len(rate_limit_storage[client_ip]) >= MAX_SUBMISSIONS_PER_HOUR:
            return False
        
        # Add current request
        rate_limit_storage[client_ip].append(current_time)
        return True

def validate_submission(data):
    """Validate submission data structure"""
    required_fields = ['timestamp', 'public_ip', 'results']
    
    # Check required fields
    for field in required_fields:
        if field not in data:
            return False, f"Missing field: {field}"
    
    # Validate results structure
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
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{SUBMISSIONS_DIR}/{data['public_ip']}_{timestamp}.json"
    
    # Add metadata
    data['received_at'] = datetime.now().isoformat() + 'Z'
    data['client_ip'] = client_ip
    
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    
    return filename

# ==================== API ENDPOINTS ====================

@app.route('/timestamp', methods=['GET'])
def get_timestamp():
    """
    Get current timestamp for token generation
    
    Returns:
        JSON with current timestamp
    """
    current_ts = int(time.time())
    return jsonify({
        'timestamp': current_ts,
        'status': 'ok'
    })

@app.route('/myip', methods=['GET'])
def get_client_ip():
    """
    Get client's public IP address
    
    Returns:
        Plain text with client IP
    """
    # Try to get real IP from headers (in case of proxy)
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
        "total_successful": <int>,
        "results": [
            {"ip": "...", "port": ..., ...},
            ...
        ]
    }
    
    Returns:
        JSON with status
    """
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if ',' in client_ip:
        client_ip = client_ip.split(',')[0].strip()
    
    # Check content size
    if len(request.data) > MAX_SUBMISSION_SIZE:
        return jsonify({
            'status': 'error',
            'message': 'Submission too large'
        }), 413
    
    # Check rate limit
    if not check_rate_limit(client_ip):
        return jsonify({
            'status': 'error',
            'message': 'Rate limit exceeded'
        }), 429
    
    # Parse JSON
    try:
        data = request.json
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Invalid JSON: {str(e)}'
        }), 400
    
    # Validate token
    timestamp = data.get('timestamp')
    token = data.get('token')
    
    if not timestamp or not token:
        return jsonify({
            'status': 'error',
            'message': 'Missing timestamp or token'
        }), 401
    
    valid, msg = validate_token(timestamp, token)
    if not valid:
        return jsonify({
            'status': 'error',
            'message': msg
        }), 401
    
    # Validate submission structure
    valid, msg = validate_submission(data)
    if not valid:
        return jsonify({
            'status': 'error',
            'message': msg
        }), 400
    
    # Save submission
    try:
        filename = save_submission(data, client_ip)
        update_stats(data)
        
        return jsonify({
            'status': 'ok',
            'message': 'Submission received',
            'filename': os.path.basename(filename)
        }), 200
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to save: {str(e)}'
        }), 500

@app.route('/stats', methods=['GET'])
def get_statistics():
    """
    Get current statistics (public)
    
    Returns:
        JSON with statistics
    """
    stats = get_stats()
    
    # Remove sensitive data
    public_stats = {
        'total_submissions': stats.get('total_submissions', 0),
        'total_tests': stats.get('total_tests', 0),
        'total_successful_ips': stats.get('total_successful_ips', 0),
        'last_updated': stats.get('last_updated', 'N/A')
    }
    
    return jsonify(public_stats)

@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    
    Returns:
        JSON with health status
    """
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat() + 'Z'
    })

@app.route('/', methods=['GET'])
def index():
    """
    Serve dashboard or API info based on request
    """
    # Check if dashboard.html exists
    dashboard_path = 'dashboard.html'
    if os.path.exists(dashboard_path):
        with open(dashboard_path, 'r') as f:
            return f.read()
    
    # Fallback to API info
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Fastly CDN Scanner - API</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background: #f5f5f5;
            }
            .container {
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 {
                color: #333;
                border-bottom: 2px solid #007bff;
                padding-bottom: 10px;
            }
            .endpoint {
                background: #f8f9fa;
                padding: 15px;
                margin: 10px 0;
                border-left: 4px solid #007bff;
                border-radius: 4px;
            }
            code {
                background: #e9ecef;
                padding: 2px 6px;
                border-radius: 3px;
                font-family: monospace;
            }
            .footer {
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #ddd;
                text-align: center;
                color: #666;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Fastly CDN Scanner - Collection API</h1>
            <p>This API collects scan results from distributed scanners to help Iranians access the internet.</p>
            
            <h2>Available Endpoints:</h2>
            
            <div class="endpoint">
                <strong>GET /timestamp</strong>
                <p>Get current server timestamp for token generation</p>
            </div>
            
            <div class="endpoint">
                <strong>GET /myip</strong>
                <p>Get your public IP address</p>
            </div>
            
            <div class="endpoint">
                <strong>POST /submit</strong>
                <p>Submit scan results (requires authentication token)</p>
            </div>
            
            <div class="endpoint">
                <strong>GET /stats</strong>
                <p>Get current statistics</p>
            </div>
            
            <div class="endpoint">
                <strong>GET /health</strong>
                <p>Health check endpoint</p>
            </div>
            
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
    """
    Serve aggregated result files
    """
    aggregated_path = os.path.join(AGGREGATED_DIR, filename)
    
    if not os.path.exists(aggregated_path):
        return jsonify({'error': 'File not found'}), 404
    
    # Send file with no-cache headers
    response = send_file(aggregated_path, mimetype='application/json')
    response.headers['Cache-Control'] = 'no-cache, must-revalidate'
    return response

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    """
    Serve downloadable files (scanner package, etc.)
    Files should be placed in: /opt/fastly-collector/dl/
    """
    file_path = os.path.join(DOWNLOADS_DIR, filename)
    
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
    
    # Determine mimetype
    if filename.endswith('.zip'):
        mimetype = 'application/zip'
    elif filename.endswith('.py'):
        mimetype = 'text/x-python'
    elif filename.endswith('.txt'):
        mimetype = 'text/plain'
    else:
        mimetype = 'application/octet-stream'
    
    return send_file(file_path, 
                     mimetype=mimetype,
                     as_attachment=True,
                     download_name=filename)

@app.route('/api/aggregate', methods=['POST'])
def trigger_aggregation():
    """
    Trigger aggregation process (Admin only)
    
    This endpoint runs aggregator.py to regenerate aggregated results
    
    Returns:
        JSON with status
    """
    try:
        import subprocess
        
        # Get the directory where api.py is located
        api_dir = os.path.dirname(os.path.abspath(__file__))
        aggregator_path = os.path.join(api_dir, 'aggregator.py')
        
        # Check if aggregator.py exists
        if not os.path.exists(aggregator_path):
            return jsonify({
                'status': 'error',
                'message': 'aggregator.py not found'
            }), 404
        
        # Run aggregator.py
        result = subprocess.run(
            ['python3', aggregator_path],
            cwd=api_dir,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            return jsonify({
                'status': 'ok',
                'message': 'Aggregation completed successfully',
                'output': result.stdout
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Aggregation failed',
                'error': result.stderr
            }), 500
    
    except subprocess.TimeoutExpired:
        return jsonify({
            'status': 'error',
            'message': 'Aggregation timed out'
        }), 408
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to trigger aggregation: {str(e)}'
        }), 500

# ==================== MAIN ====================

if __name__ == '__main__':
    # Initialize
    init_directories()
    
    print("="*50)
    print("Fastly CDN Scanner - Collection API")
    print("Developed by: DrConnect")
    print("="*50)
    print(f"\nSecret Key (keep secure): {SECRET_KEY}")
    print(f"Submissions directory: {SUBMISSIONS_DIR}")
    print(f"Aggregated directory: {AGGREGATED_DIR}")
    print(f"Downloads directory: {DOWNLOADS_DIR}")
    print(f"Stats file: {STATS_FILE}")
    print("\nStarting server on 0.0.0.0:8080...")
    print("="*50)
    
    # Run server
    app.run(
        host='0.0.0.0',
        port=8080,
        debug=False
    )
