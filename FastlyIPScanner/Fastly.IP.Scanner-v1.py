#!/usr/bin/env python3
"""
Fastly CDN IP Scanner v1.3
Developed by: DrConnect
Telegram: @lvlRF
Phone: +98 912 741 9412

Description:
Scans Fastly CDN IP ranges to find working IPs accessible from your location.
Features:
- Two-stage verification: TCP connect + HTTP verification
- Custom IP List: Load IPs from ip_list.txt file
- Ctrl+C Safe Exit: Press once 
"""

import sys
import os
import socket
import json
import ipaddress
import time
import subprocess
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed, wait, FIRST_COMPLETED
from threading import Lock, Thread
import threading
import signal

# Check and auto-install required packages
def check_and_install_packages():
    """Check if packages are installed, auto-install from wheels if missing"""
    from pathlib import Path
    import platform
    
    # Check requests
    try:
        import requests
        has_requests = True
    except ImportError:
        has_requests = False
    
    if not has_requests:
        print("\n" + "="*60)
        print("[INFO] Package 'requests' is not installed")
        print("="*60)
        
        # Detect OS
        os_name = platform.system()
        is_windows = os_name == "Windows"
        
        # Determine pip command for messages
        pip_cmd = 'pip' if is_windows else 'pip3'
        python_cmd = 'python' if is_windows else 'python3'
        
        # Find wheel files
        script_dir = Path(__file__).parent
        wheels_dir = script_dir / 'wheels'
        
        # Check multiple locations for wheel files
        install_dir = None
        if wheels_dir.exists() and list(wheels_dir.glob('*.whl')):
            install_dir = wheels_dir
            location = "wheels/ folder"
        elif list(script_dir.glob('*.whl')):
            install_dir = script_dir
            location = "current directory"
        
        if install_dir:
            print(f"\n[INFO] Found .whl files in {location}")
            print(f"[INFO] Detected OS: {os_name}")
            print(f"[INFO] Attempting automatic installation...")
            print()
            
            try:
                import subprocess
                
                # Method 1: Try direct installation with all wheel files
                print("[INFO] Method 1: Installing all wheel files...")
                whl_files = list(str(f) for f in install_dir.glob('*.whl'))
                cmd = [sys.executable, '-m', 'pip', 'install', '--user'] + whl_files
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    print("[OK] Packages installed successfully!")
                    print(f"\n[INFO] Please run the scanner again:")
                    print(f"       {python_cmd} scanner.py")
                    print("="*60 + "\n")
                    sys.exit(0)
                
                # Method 2: Try with find-links
                print("[INFO] Method 2: Installing with --find-links...")
                cmd = [
                    sys.executable, '-m', 'pip', 'install',
                    '--user',
                    '--no-index',
                    '--find-links', str(install_dir),
                    'requests', 'tqdm'
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    print("[OK] Packages installed successfully!")
                    print(f"\n[INFO] Please run the scanner again:")
                    print(f"       {python_cmd} scanner.py")
                    print("="*60 + "\n")
                    sys.exit(0)
                
                # Method 3: Try without --user
                print("[INFO] Method 3: Installing without --user flag...")
                cmd = [
                    sys.executable, '-m', 'pip', 'install',
                    '--no-index',
                    '--find-links', str(install_dir),
                    'requests', 'tqdm'
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    print("[OK] Packages installed successfully!")
                    print(f"\n[INFO] Please run the scanner again:")
                    print(f"       {python_cmd} scanner.py")
                    print("="*60 + "\n")
                    sys.exit(0)
                else:
                    print("[WARNING] All automatic installation methods failed")
                    
            except Exception as e:
                print(f"[WARNING] Installation error: {e}")
        
        # If auto-install failed, show OS-specific manual instructions
        print("\n[INFO] Please install manually:\n")
        
        if is_windows:
            print("  Windows - Method 1 (Recommended):")
            print("    pip install --user --no-index --find-links . requests tqdm")
            print("\n  Windows - Method 2 (Use install script):")
            print("    Double-click: install.bat")
            print("\n  Windows - Method 3 (One by one):")
            print("    pip install --user certifi-2023.11.17-py3-none-any.whl")
            print("    pip install --user charset_normalizer-3.3.2-py3-none-any.whl")
            print("    pip install --user idna-3.6-py3-none-any.whl")
            print("    pip install --user urllib3-2.0.7-py3-none-any.whl")
            print("    pip install --user requests-2.31.0-py3-none-any.whl")
            print("    pip install --user tqdm-4.66.1-py3-none-any.whl")
        else:
            print("  Linux/Mac - Method 1 (Recommended):")
            print("    pip3 install --user --no-index --find-links . requests tqdm")
            print("\n  Linux/Mac - Method 2 (Use install script):")
            print("    chmod +x install.sh")
            print("    ./install.sh")
            print("\n  Linux/Mac - Method 3 (One by one):")
            print("    pip3 install --user certifi-2023.11.17-py3-none-any.whl")
            print("    pip3 install --user charset_normalizer-3.3.2-py3-none-any.whl")
            print("    pip3 install --user idna-3.6-py3-none-any.whl")
            print("    pip3 install --user urllib3-2.0.7-py3-none-any.whl")
            print("    pip3 install --user requests-2.31.0-py3-none-any.whl")
            print("    pip3 install --user tqdm-4.66.1-py3-none-any.whl")
        
        print("\n" + "="*60 + "\n")
        sys.exit(1)

check_and_install_packages()

import requests

# tqdm is OPTIONAL (for progress bar)
try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False
    print("[INFO] tqdm not installed. Using simple progress display.")
    print("[INFO] For better progress bar: pip install tqdm\n")

# Disable SSL warnings
requests.packages.urllib3.disable_warnings()

# ==================== CONFIGURATION ====================

# Telemetry Server
TELEMETRY_SERVER = "http://194.36.174.102:8080"
DEVELOPER_CHANNEL = "https://t.me/drconnect"

# Obfuscated SECRET_KEY (must match server)
_k = [68, 114, 67, 111, 110, 110, 101, 99, 116, 95, 70, 97, 115, 116, 108, 121, 95, 50, 48, 50, 53, 95, 83, 101, 99, 117, 114, 101, 95, 75, 101, 121, 95, 88, 55, 57, 51]
SECRET_KEY = ''.join(chr(c) for c in _k)

# Embedded Fastly IP ranges
FASTLY_IP_RANGES = [
    "23.235.32.0/20",
    "43.249.72.0/22",
    "103.244.50.0/24",
    "103.245.222.0/23",
    "103.245.224.0/24",
    "104.156.80.0/20",
    "140.248.64.0/18",
    "140.248.128.0/17",
    "146.75.0.0/17",
    "151.101.0.0/16",
    "157.52.64.0/18",
    "167.82.0.0/17",
    "167.82.128.0/20",
    "167.82.160.0/20",
    "167.82.224.0/20",
    "172.111.64.0/18",
    "185.31.16.0/22",
    "199.27.72.0/21",
    "199.232.0.0/16"
]

# CDN Ports (Compatible with Fastly & Cloudflare)
PORTS = {
    'https': [443, 8443, 2053, 2083, 2087, 2096],
    'http': [80, 8080, 8880, 2052, 2082, 2086, 2095],
    'all': [443, 8443, 2053, 2083, 2087, 2096, 80, 8080, 8880, 2052, 2082, 2086, 2095]
}

# Default settings
DEFAULT_SETTINGS = {
    'threads': 30,
    'timeout': 5,
    'port_mode': 'https',
    'smart_scan': True,
    'logging_level': 'normal',
    'export_format': 'both'
}

# Global variables
settings = DEFAULT_SETTINGS.copy()
scan_interrupted = False
force_exit = False  # Flag for immediate exit after Ctrl+C
ctrl_c_count = 0  # Track Ctrl+C presses
results_lock = Lock()
successful_ips = []
failed_ips = []
tested_count = 0
state_file = '.scan_state.json'

# Auto-submit configuration
pending_results = []  # Buffer for results waiting to be sent
last_submission_time = 0
submission_lock = Lock()
auto_submit_enabled = True
auto_submit_thread = None
AUTO_SUBMIT_BATCH = 10  # Send after every 10 successful IPs
AUTO_SUBMIT_INTERVAL = 60  # Send every 60 seconds if there are results
MIN_RESULTS_TO_SUBMIT = 1  # Minimum results to trigger submission

# ==================== UTILITY FUNCTIONS ====================

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully - submit pending results before exit"""
    global scan_interrupted, auto_submit_enabled, ctrl_c_count, force_exit
    
    ctrl_c_count += 1
    
    # If pressed twice quickly, force exit immediately
    if ctrl_c_count >= 2:
        print("\n\n[!] Force exit ")
        os._exit(1)  # Force exit immediately
    
    scan_interrupted = True
    auto_submit_enabled = False  # Stop auto-submit thread
    force_exit = True  # Signal to main menu to exit
    
    print("\n\n[!] Scan interrupted by user")
    print("[INFO] Press Ctrl+C again to force exit without submitting")
    
    # Submit results (even if empty for scan statistics)
    try:
        public_ip = get_public_ip()
        
        with submission_lock:
            if pending_results:
                print(f"[INFO] Submitting {len(pending_results)} pending results...")
                try:
                    success = submit_telemetry(pending_results.copy(), public_ip, 1)
                    if success:
                        pending_results.clear()
                        print("[OK] ")
                    else:
                        print(f"[WARNING] ")
                except Exception as e:
                    print(f"[WARNING] ")
            else:
                # No successful IPs, but still send scan statistics
                print("[INFO] ")
                try:
                    success = submit_telemetry([], public_ip, 1)
                    if success:
                        print("[OK] ")
                    else:
                        print("[WARNING] ")
                except Exception as e:
                    print(f"[WARNING] ")
    except:
        pass  # Ignore errors during exit
    
    print("\n[INFO] Exiting...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def get_local_ip():
    """Get local IP address of the system"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0)
        s.connect(('8.8.8.8', 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "127.0.0.1"

def get_public_ip():
    """Get public IP from telemetry server"""
    try:
        response = requests.get(f'{TELEMETRY_SERVER}/myip', timeout=2)
        if response.status_code == 200:
            return response.text.strip()
    except:
        pass
    
    # Fallback to local IP
    return get_local_ip()

def clear_screen():
    """Clear terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    """Print application header"""
    print("╔════════════════════════════════════════════════════╗")
    print("║        Fastly CDN IP Scanner v1.0                  ║")
    print("║        Developed by: DrConnect                     ║")
    print("║        Channel: https://t.me/drconnect            ║")
    print("╚════════════════════════════════════════════════════╝\n")
    print("[INFO] This tool helps Iranians access the internet")
    print("[INFO] Working Your IPs list also : file name in root : ip_list.txt \n")

def expand_ip_ranges(ranges):
    """Expand CIDR ranges to individual IPs"""
    all_ips = []
    for cidr in ranges:
        network = ipaddress.ip_network(cidr, strict=False)
        all_ips.extend([str(ip) for ip in network.hosts()])
    return all_ips

def load_ip_list_from_file(filename='ip_list.txt'):
    """
    Load IP list from external file
    
    Supported formats:
    - CIDR: 23.235.32.0/24
    - Single IP: 151.101.1.1
    - Range: 23.235.32.0-23.235.32.255
    - Comments: # This is a comment
    
    Returns list of CIDR ranges or None if file not found
    """
    if not os.path.exists(filename):
        return None
    
    ranges = []
    
    try:
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Format 1: CIDR (23.235.32.0/24)
                if '/' in line:
                    try:
                        # Validate CIDR
                        ipaddress.ip_network(line, strict=False)
                        ranges.append(line)
                    except:
                        print(f"[WARNING] Invalid CIDR: {line}")
                
                # Format 2: Range (23.235.32.0-23.235.32.255)
                elif '-' in line:
                    try:
                        start_ip, end_ip = line.split('-')
                        start_ip = start_ip.strip()
                        end_ip = end_ip.strip()
                        
                        # Convert range to CIDR (approximation)
                        start = ipaddress.ip_address(start_ip)
                        end = ipaddress.ip_address(end_ip)
                        
                        # Add all IPs in range as /32
                        for ip_int in range(int(start), int(end) + 1):
                            ip = str(ipaddress.ip_address(ip_int))
                            ranges.append(f"{ip}/32")
                    except Exception as e:
                        print(f"[WARNING] Invalid range: {line} ({e})")
                
                # Format 3: Single IP (151.101.1.1)
                else:
                    try:
                        # Validate IP
                        ipaddress.ip_address(line)
                        ranges.append(f"{line}/32")
                    except:
                        print(f"[WARNING] Invalid IP: {line}")
        
        return ranges if ranges else None
    
    except Exception as e:
        print(f"[ERROR] Failed to read {filename}: {e}")
        return None

def get_ip_ranges():
    """
    Get IP ranges from external file or use default Fastly ranges
    
    Priority:
    1. ip_list.txt (if exists)
    2. FASTLY_IP_RANGES (default)
    """
    # Try to load from external file
    custom_ranges = load_ip_list_from_file('ip_list.txt')
    
    if custom_ranges:
        print("[INFO] Using custom IP list from: ip_list.txt")
        print(f"[INFO] Loaded {len(custom_ranges)} IP ranges from file")
        return custom_ranges
    else:
        print("[INFO] Using default Fastly CDN IP ranges")
        return FASTLY_IP_RANGES

def get_nearby_ips(successful_ip, all_ips):
    """Get IPs from the same /24 subnet as successful IP"""
    try:
        ip_obj = ipaddress.ip_address(successful_ip)
        subnet = ipaddress.ip_network(f"{successful_ip}/24", strict=False)
        nearby = [ip for ip in all_ips if ipaddress.ip_address(ip) in subnet]
        return nearby
    except:
        return []

def save_state(ips_to_scan, scanned_ips):
    """Save current scan state for resume"""
    state = {
        'timestamp': datetime.now().isoformat(),
        'settings': settings,
        'ips_to_scan': ips_to_scan,
        'scanned_ips': scanned_ips,
        'successful_ips': successful_ips,
        'failed_ips': failed_ips
    }
    with open(state_file, 'w') as f:
        json.dump(state, f, indent=2)

def load_state():
    """Load previous scan state"""
    if os.path.exists(state_file):
        with open(state_file, 'r') as f:
            return json.load(f)
    return None

def delete_state():
    """Delete scan state file"""
    if os.path.exists(state_file):
        os.remove(state_file)

# ==================== SCANNING FUNCTIONS ====================

def generate_token(timestamp):
    """Generate authentication token"""
    import hashlib
    data = f"{timestamp}{SECRET_KEY}"
    return hashlib.sha256(data.encode()).hexdigest()

def get_server_timestamp():
    """Get timestamp from telemetry server"""
    try:
        response = requests.get(f'{TELEMETRY_SERVER}/timestamp', timeout=3)
        if response.status_code == 200:
            data = response.json()
            return data.get('timestamp')
    except:
        pass
    return None

def submit_telemetry(successful_ips, public_ip, duration):
    """Submit scan results to telemetry server"""
    try:
        # Get timestamp from server
        timestamp = get_server_timestamp()
        if not timestamp:
            return False
        
        # Generate token
        token = generate_token(timestamp)
        
        # Prepare payload
        payload = {
            'timestamp': timestamp,
            'token': token,
            'public_ip': public_ip,
            'scan_duration': duration,
            'total_successful': len(successful_ips),
            'results': successful_ips
        }
        
        # Submit
        response = requests.post(
            f'{TELEMETRY_SERVER}/submit',
            json=payload,
            timeout=5
        )
        
        return response.status_code == 200
    
    except:
        return False

def auto_submit_worker(public_ip):
    """Background worker for automatic submission - batch + timer based"""
    global pending_results, last_submission_time, scan_interrupted, auto_submit_enabled
    
    last_submission_time = time.time()
    
    while auto_submit_enabled and not scan_interrupted:
        try:
            time.sleep(5)  # Check every 5 seconds
            
            current_time = time.time()
            should_submit = False
            
            with submission_lock:
                num_pending = len(pending_results)
                time_since_last = current_time - last_submission_time
                
                # Submit if:
                # 1. Reached batch size (10 IPs)
                # 2. OR has results AND 60 seconds passed
                if num_pending >= AUTO_SUBMIT_BATCH:
                    should_submit = True
                elif num_pending >= MIN_RESULTS_TO_SUBMIT and time_since_last >= AUTO_SUBMIT_INTERVAL:
                    should_submit = True
            
            if should_submit:
                with submission_lock:
                    results_to_send = pending_results.copy()
                    pending_results.clear()
                    last_submission_time = current_time
                
                # Send in background (don't block scanning)
                if results_to_send:
                    duration = int(current_time - (last_submission_time - AUTO_SUBMIT_INTERVAL))
                    success = submit_telemetry(results_to_send, public_ip, duration)
                    
                    if success:
                        print(f"\n[OK] )
                    else:
                        # If failed, put back to pending (keep for next try)
                        with submission_lock:
                            pending_results.extend(results_to_send)
        
        except Exception as e:
            pass  # Silent fail, don't interrupt scanning

def test_tcp_connection(ip, port, timeout):
    """Stage 1: Test TCP connection to IP:port"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        sock.close()
        return result == 0
    except:
        return False

def test_http_verification(ip, port, timeout):
    """Stage 2: Verify HTTP/HTTPS response and check for Fastly"""
    protocol = 'https' if port in PORTS['https'] else 'http'
    url = f"{protocol}://{ip}:{port}"
    
    try:
        response = requests.get(
            url,
            timeout=timeout,
            verify=False,
            headers={'User-Agent': 'FastlyScannerBot/1.0'}
        )
        
        # Check if it's actually Fastly
        server_header = response.headers.get('Server', '').lower()
        via_header = response.headers.get('Via', '').lower()
        
        is_fastly = 'fastly' in server_header or 'fastly' in via_header
        
        return {
            'success': response.status_code < 500,
            'is_fastly': is_fastly,
            'status_code': response.status_code,
            'server': response.headers.get('Server', 'Unknown'),
            'latency': response.elapsed.total_seconds() * 1000
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def scan_ip_port(ip, port, scan_mode='quick'):
    """Scan single IP:port combination"""
    global tested_count, scan_interrupted
    
    if scan_interrupted:
        return None
    
    # Stage 1: TCP Connect
    tcp_success = test_tcp_connection(ip, port, settings['timeout'])
    
    result = {
        'ip': ip,
        'port': port,
        'tcp_success': tcp_success,
        'timestamp': datetime.now().isoformat()
    }
    
    # Stage 2: HTTP Verification (only if Stage 1 passed and mode is full)
    if tcp_success and scan_mode == 'full':
        http_result = test_http_verification(ip, port, settings['timeout'])
        result.update(http_result)
        
        if http_result['success']:
            with results_lock:
                successful_ips.append(result)
            # Add to pending results for real-time submission
            with submission_lock:
                pending_results.append(result)
    elif tcp_success and scan_mode == 'quick':
        result['success'] = True
        with results_lock:
            successful_ips.append(result)
        # Add to pending results for real-time submission
        with submission_lock:
            pending_results.append(result)
    else:
        with results_lock:
            failed_ips.append(result)
    
    with results_lock:
        tested_count += 1
    
    return result

def perform_scan(ip_list, ports, scan_mode='quick'):
    """Perform the actual scanning with threading"""
    global tested_count, scan_interrupted, successful_ips, failed_ips, last_submission_time, pending_results
    
    tested_count = 0
    scan_interrupted = False
    last_submission_time = time.time()
    
    # Clear pending results from previous scan
    with submission_lock:
        pending_results.clear()
    
    # Start auto-submit thread
    public_ip = get_public_ip()
    auto_submit_thread = threading.Thread(target=auto_submit_worker, args=(public_ip,), daemon=True)
    auto_submit_thread.start()
    print(f"[INFO] ")
    
    # Generate all IP:port combinations
    targets = [(ip, port) for ip in ip_list for port in ports]
    total_targets = len(targets)
    
    print(f"\n[INFO] Total targets to scan: {total_targets:,}")
    print(f"[INFO] Threads: {settings['threads']} | Timeout: {settings['timeout']}s")
    print(f"[INFO] Mode: {scan_mode.upper()} | Smart Scan: {settings['smart_scan']}")
    print(f"\n[INFO] Press [0] + Enter at any time to stop and save results\n")
    
    scanned_targets = []
    priority_queue = targets.copy()
    
    with ThreadPoolExecutor(max_workers=settings['threads']) as executor:
        if HAS_TQDM:
            # Use tqdm progress bar
            with tqdm(total=total_targets, desc="Scanning", unit="target") as pbar:
                futures = {}
                
                # Submit initial batch
                batch_size = settings['threads'] * 3
                for target in priority_queue[:batch_size]:
                    ip, port = target
                    future = executor.submit(scan_ip_port, ip, port, scan_mode)
                    futures[future] = target
                
                remaining_targets = priority_queue[batch_size:]
                
                while futures and not scan_interrupted:
                    try:
                        # Wait for any future to complete (longer timeout for better performance)
                        done, pending = wait(futures.keys(), timeout=5.0, return_when=FIRST_COMPLETED)
                        
                        # If no futures completed, continue waiting
                        if not done:
                            continue
                        
                        for future in done:
                            target = futures.pop(future)
                            scanned_targets.append(target)
                            
                            try:
                                result = future.result()
                                
                                # Smart Scan: prioritize nearby IPs if successful
                                if result and result.get('success') and settings['smart_scan']:
                                    nearby = get_nearby_ips(result['ip'], [t[0] for t in remaining_targets])
                                    remaining_targets = [t for t in remaining_targets if t[0] in nearby] + \
                                                      [t for t in remaining_targets if t[0] not in nearby]
                                
                                # Update progress bar
                                pbar.update(1)
                                pbar.set_postfix({
                                    'Success': len(successful_ips),
                                    'Failed': len(failed_ips),
                                    'Speed': f"{tested_count/(time.time() - start_time):.1f} t/s"
                                })
                                
                            except Exception as e:
                                if settings['logging_level'] == 'verbose':
                                    print(f"\n[ERROR] {target}: {e}")
                            
                            # Submit next target
                            if remaining_targets and not scan_interrupted:
                                next_target = remaining_targets.pop(0)
                                ip, port = next_target
                                future = executor.submit(scan_ip_port, ip, port, scan_mode)
                                futures[future] = next_target
                    
                    except KeyboardInterrupt:
                        scan_interrupted = True
                        print("\n\n[!] Scan interrupted by user...")
                        break
                        
        else:
            # Simple progress without tqdm
            futures = {}
            
            # Submit initial batch
            batch_size = settings['threads'] * 3
            for target in priority_queue[:batch_size]:
                ip, port = target
                future = executor.submit(scan_ip_port, ip, port, scan_mode)
                futures[future] = target
            
            remaining_targets = priority_queue[batch_size:]
            last_update = time.time()
            
            while futures and not scan_interrupted:
                try:
                    # Wait for any future to complete (longer timeout for better performance)
                    done, pending = wait(futures.keys(), timeout=5.0, return_when=FIRST_COMPLETED)
                    
                    # If no futures completed, continue waiting
                    if not done:
                        continue
                    
                    for future in done:
                        target = futures.pop(future)
                        scanned_targets.append(target)
                        
                        try:
                            result = future.result()
                            
                            # Smart Scan: prioritize nearby IPs if successful
                            if result and result.get('success') and settings['smart_scan']:
                                nearby = get_nearby_ips(result['ip'], [t[0] for t in remaining_targets])
                                remaining_targets = [t for t in remaining_targets if t[0] in nearby] + \
                                                  [t for t in remaining_targets if t[0] not in nearby]
                            
                            # Update progress every 2 seconds
                            if time.time() - last_update > 2:
                                progress = (tested_count / total_targets * 100) if total_targets > 0 else 0
                                speed = tested_count / (time.time() - start_time) if (time.time() - start_time) > 0 else 0
                                print(f"Progress: {tested_count:,}/{total_targets:,} ({progress:.1f}%) | "
                                      f"Success: {len(successful_ips)} | Failed: {len(failed_ips)} | "
                                      f"Speed: {speed:.1f} t/s")
                                last_update = time.time()
                            
                        except Exception as e:
                            if settings['logging_level'] == 'verbose':
                                print(f"\n[ERROR] {target}: {e}")
                        
                        # Submit next target
                        if remaining_targets and not scan_interrupted:
                            next_target = remaining_targets.pop(0)
                            ip, port = next_target
                            future = executor.submit(scan_ip_port, ip, port, scan_mode)
                            futures[future] = next_target
                
                except KeyboardInterrupt:
                    scan_interrupted = True
                    print("\n\n[!] Scan interrupted by user...")
                    break
    
    # Save state if interrupted
    if scan_interrupted:
        remaining = [t for t in targets if t not in scanned_targets]
        save_state(remaining, scanned_targets)
        print(f"\n[INFO] Progress saved. {len(remaining):,} targets remaining.")
    else:
        delete_state()
    
    # Final submission - send any remaining pending results or scan statistics
    global auto_submit_enabled
    auto_submit_enabled = False  # Stop auto-submit thread
    time.sleep(1)  # Give thread time to finish
    
    with submission_lock:
        if pending_results:
            print(f"\n[INFO] wating...")
            try:
                duration = int(time.time() - last_submission_time) if last_submission_time > 0 else 1
                success = submit_telemetry(pending_results.copy(), public_ip, duration)
                if success:
                    print("[OK] wating")
                    pending_results.clear()
                else:
                    print("[WARNING] wating")
            except Exception as e:
                print(f"[WARNING] wating")
        else:
            # No successful IPs, but still send scan statistics
            if not scan_interrupted:  # Only if scan completed normally
                print(f"\n[INFO] No successful IPs found. ")
                try:
                    scan_time = time.time() - start_time if 'start_time' in locals() else 1
                    success = submit_telemetry([], public_ip, int(scan_time))
                    if success:
                        print("[OK] wating...")
                    else:
                        print("[WARNING] wating...")
                except Exception as e:
                    print(f"[WARNING] wating...")
    
    return successful_ips

def save_results(successful_ips, scan_duration=0):
    """Save scan results to files"""
    if not successful_ips:
        print("\n[!] No successful IPs found. Nothing to save.")
        return
    
    # Create results directory
    os.makedirs('results', exist_ok=True)
    
    # Generate filename
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    public_ip = get_public_ip()
    local_ip = get_local_ip()
    base_filename = f"results/fastly_{timestamp}_{public_ip}_{local_ip}"
    
    # Save TXT format
    if settings['export_format'] in ['text', 'both']:
        txt_file = f"{base_filename}.txt"
        with open(txt_file, 'w') as f:
            f.write(f"# Fastly CDN Working IPs\n")
            f.write(f"# Generated: {timestamp}\n")
            f.write(f"# Public IP: {public_ip}\n")
            f.write(f"# Local IP: {local_ip}\n")
            f.write(f"# Total: {len(successful_ips)}\n")
            f.write(f"# Contact: DrConnect | Channel: https://t.me/drconnect\n\n")
            
            for result in successful_ips:
                f.write(f"{result['ip']}:{result['port']}\n")
        
        print(f"[OK] TXT saved: {txt_file}")
    
    # Save JSON format
    if settings['export_format'] in ['json', 'both']:
        json_file = f"{base_filename}.json"
        output_data = {
            'metadata': {
                'generated': timestamp,
                'public_ip': public_ip,
                'local_ip': local_ip,
                'total_successful': len(successful_ips),
                'scan_settings': settings,
                'contact': {
                    'developer': 'DrConnect',
                    'channel': 'https://t.me/drconnect'
                }
            },
            'results': successful_ips
        }
        
        with open(json_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"[OK] JSON saved: {json_file}")
    
    # Save log
    log_file = f"results/scan_{timestamp}.log"
    with open(log_file, 'w') as f:
        f.write(f"Scan Log - {timestamp}\n")
        f.write(f"Public IP: {public_ip}\n")
        f.write(f"Local IP: {local_ip}\n")
        f.write(f"Settings: {json.dumps(settings, indent=2)}\n\n")
        f.write(f"Total Tested: {tested_count}\n")
        f.write(f"Successful: {len(successful_ips)}\n")
        f.write(f"Failed: {len(failed_ips)}\n")
        f.write(f"Duration: {scan_duration:.1f}s\n")
    
    print(f"[OK] Log saved: {log_file}")
    
    # Send any remaining pending results
    with submission_lock:
        if pending_results:
            print(f"[INFO] wating......")
            submit_telemetry(pending_results, public_ip, scan_duration)
            pending_results.clear()
    
    # Submit to telemetry server (final submission with all results)
    print("[INFO] wating...")
    if submit_telemetry(successful_ips, public_ip, scan_duration):
        print("[OK] wating...")
    else:
        print("[!] wating...")

# ==================== MENU FUNCTIONS ====================

def menu_settings():
    """Settings menu"""
    while True:
        clear_screen()
        print_header()
        print("═══════════ SETTINGS ═══════════\n")
        print(f"[1] Select Ports (Current: {settings['port_mode']})")
        print(f"[2] Thread Count (Current: {settings['threads']})")
        print(f"[3] Timeout (Current: {settings['timeout']}s)")
        print(f"[4] Smart Scan (Current: {'Enabled' if settings['smart_scan'] else 'Disabled'})")
        print(f"[5] Logging Level (Current: {settings['logging_level']})")
        print(f"[6] Export Format (Current: {settings['export_format']})")
        print("[7] Reset to Defaults")
        print("[0] Back to Main Menu\n")
        
        choice = input("Your choice: ").strip()
        
        if choice == '1':
            menu_port_selection()
        elif choice == '2':
            try:
                threads = int(input("\nEnter thread count (1-100): "))
                if 1 <= threads <= 100:
                    settings['threads'] = threads
                    print("[OK] Thread count updated")
                else:
                    print("[!] Invalid range")
                time.sleep(1)
            except:
                print("[!] Invalid input")
                time.sleep(1)
        elif choice == '3':
            try:
                timeout = int(input("\nEnter timeout in seconds (1-30): "))
                if 1 <= timeout <= 30:
                    settings['timeout'] = timeout
                    print("[OK] Timeout updated")
                else:
                    print("[!] Invalid range")
                time.sleep(1)
            except:
                print("[!] Invalid input")
                time.sleep(1)
        elif choice == '4':
            settings['smart_scan'] = not settings['smart_scan']
            print(f"[OK] Smart Scan {'Enabled' if settings['smart_scan'] else 'Disabled'}")
            time.sleep(1)
        elif choice == '5':
            menu_logging_level()
        elif choice == '6':
            menu_export_format()
        elif choice == '7':
            settings.update(DEFAULT_SETTINGS)
            print("[OK] Settings reset to defaults")
            time.sleep(1)
        elif choice == '0':
            break

def menu_port_selection():
    """Port selection submenu"""
    while True:
        clear_screen()
        print_header()
        print("═══════════ SELECT PORTS ═══════════\n")
        print("[1] HTTPS Only (443, 8443, 2053, 2083, 2087, 2096)")
        print("[2] HTTP Only (80, 8080, 8880, 2052, 2082, 2086, 2095)")
        print("[3] All Ports (Recommended)")
        print("[4] Custom (Enter manually)")
        print("[0] Back\n")
        
        choice = input("Your choice: ").strip()
        
        if choice == '1':
            settings['port_mode'] = 'https'
            print("[OK] HTTPS ports selected")
            time.sleep(1)
            break
        elif choice == '2':
            settings['port_mode'] = 'http'
            print("[OK] HTTP ports selected")
            time.sleep(1)
            break
        elif choice == '3':
            settings['port_mode'] = 'all'
            print("[OK] All ports selected")
            time.sleep(1)
            break
        elif choice == '4':
            try:
                custom = input("\nEnter ports (comma-separated): ").strip()
                custom_ports = [int(p.strip()) for p in custom.split(',')]
                PORTS['custom'] = custom_ports
                settings['port_mode'] = 'custom'
                print(f"[OK] Custom ports set: {custom_ports}")
                time.sleep(1)
                break
            except:
                print("[!] Invalid port format")
                time.sleep(1)
        elif choice == '0':
            break

def menu_logging_level():
    """Logging level submenu"""
    clear_screen()
    print_header()
    print("═══════════ LOGGING LEVEL ═══════════\n")
    print("[1] Minimal (Only results)")
    print("[2] Normal (Progress + results)")
    print("[3] Verbose (Everything)")
    print("[0] Back\n")
    
    choice = input("Your choice: ").strip()
    
    if choice == '1':
        settings['logging_level'] = 'minimal'
    elif choice == '2':
        settings['logging_level'] = 'normal'
    elif choice == '3':
        settings['logging_level'] = 'verbose'
    
    if choice in ['1', '2', '3']:
        print(f"[OK] Logging level set to: {settings['logging_level']}")
        time.sleep(1)

def menu_export_format():
    """Export format submenu"""
    clear_screen()
    print_header()
    print("═══════════ EXPORT FORMAT ═══════════\n")
    print("[1] Text only (.txt)")
    print("[2] JSON only (.json)")
    print("[3] Both (Recommended)")
    print("[0] Back\n")
    
    choice = input("Your choice: ").strip()
    
    if choice == '1':
        settings['export_format'] = 'text'
    elif choice == '2':
        settings['export_format'] = 'json'
    elif choice == '3':
        settings['export_format'] = 'both'
    
    if choice in ['1', '2', '3']:
        print(f"[OK] Export format set to: {settings['export_format']}")
        time.sleep(1)

def main_menu():
    """Main menu"""
    global start_time, force_exit
    
    while True:
        # Check if we need to exit (after Ctrl+C)
        if force_exit:
            print("[INFO] Exiting after interrupt...")
            sys.exit(0)
        
        clear_screen()
        print_header()
        print("[1] Quick Scan (TCP Connect Only)")
        print("[2] Full Scan (TCP + HTTP Verification)")
        print("[3] Resume Previous Scan")
        print("[4] Settings")
        print("[0] Exit\n")
        
        choice = input("Your choice: ").strip()
        
        if choice == '1':
            print("\n[INFO] Loading IP ranges...")
            ip_ranges = get_ip_ranges()
            print("[INFO] Expanding IP ranges...")
            ip_list = expand_ip_ranges(ip_ranges)
            print(f"[INFO] Total IPs: {len(ip_list):,}")
            
            ports = PORTS[settings['port_mode']]
            start_time = time.time()
            
            results = perform_scan(ip_list, ports, scan_mode='quick')
            
            # Check if interrupted
            if force_exit:
                sys.exit(0)
            
            scan_duration = time.time() - start_time
            
            print(f"\n{'='*50}")
            print(f"[OK] Scan completed!")
            print(f"[OK] Successful IPs: {len(successful_ips)}")
            print(f"[OK] Failed: {len(failed_ips)}")
            print(f"[OK] Duration: {scan_duration:.1f}s")
            print(f"{'='*50}\n")
            
            save_results(successful_ips, scan_duration)
            
            input("\nPress Enter to continue...")
            
        elif choice == '2':
            print("\n[INFO] Loading IP ranges...")
            ip_ranges = get_ip_ranges()
            print("[INFO] Expanding IP ranges...")
            ip_list = expand_ip_ranges(ip_ranges)
            print(f"[INFO] Total IPs: {len(ip_list):,}")
            
            ports = PORTS[settings['port_mode']]
            start_time = time.time()
            
            results = perform_scan(ip_list, ports, scan_mode='full')
            
            # Check if interrupted
            if force_exit:
                sys.exit(0)
            
            scan_duration = time.time() - start_time
            
            print(f"\n{'='*50}")
            print(f"[OK] Scan completed!")
            print(f"[OK] Successful IPs: {len(successful_ips)}")
            print(f"[OK] Failed: {len(failed_ips)}")
            print(f"[OK] Duration: {scan_duration:.1f}s")
            print(f"{'='*50}\n")
            
            save_results(successful_ips, scan_duration)
            
            input("\nPress Enter to continue...")
            
        elif choice == '3':
            state = load_state()
            if state:
                print(f"\n[INFO] Found previous scan state")
                print(f"[INFO] Remaining targets: {len(state['ips_to_scan']):,}")
                print(f"[INFO] Already found: {len(state['successful_ips'])} successful IPs")
                
                resume = input("\nResume scan? (y/n): ").strip().lower()
                if resume == 'y':
                    # Restore state
                    settings.update(state['settings'])
                    successful_ips.extend(state['successful_ips'])
                    
                    ports = PORTS[settings['port_mode']]
                    remaining_ips = list(set([t[0] for t in state['ips_to_scan']]))
                    
                    start_time = time.time()
                    results = perform_scan(remaining_ips, ports, scan_mode='full')
                    
                    # Check if interrupted
                    if force_exit:
                        sys.exit(0)
                    
                    scan_duration = time.time() - start_time
                    
                    print(f"\n{'='*50}")
                    print(f"[OK] Scan completed!")
                    print(f"[OK] Successful IPs: {len(successful_ips)}")
                    print(f"[OK] Duration: {scan_duration:.1f}s")
                    print(f"{'='*50}\n")
                    
                    save_results(successful_ips, scan_duration)
                    delete_state()
                    
                    input("\nPress Enter to continue...")
            else:
                print("\n[!] No previous scan state found")
                time.sleep(2)
                
        elif choice == '4':
            menu_settings()
            
        elif choice == '0':
            print("\n[INFO] Exiting... Goodbye!")
            sys.exit(0)

# ==================== MAIN ====================

if __name__ == "__main__":
    start_time = time.time()
    try:
        main_menu()
    except KeyboardInterrupt:
        # signal_handler already took care of everything
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        sys.exit(1)
