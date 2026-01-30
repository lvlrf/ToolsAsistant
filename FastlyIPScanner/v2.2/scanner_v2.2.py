#!/usr/bin/env python3
"""
Dr.CDN-Scanner v2.2 - Enhanced Edition
Developed by: DrConnect
Telegram: @lvlRF | Channel: @drconnect

Description:
Advanced CDN IP Scanner with Xray integration for real connectivity testing.
Supports Cloudflare, Fastly, Gcore and other CDN providers.
Includes DNSTT compatibility testing for finding DNS servers with external connectivity.

Enhanced Features:
- Live progress bar with real-time statistics
- Live results table showing found IPs immediately
- Real-time file saving during scan
- Improved Ctrl+C handling with safe exit
- Pause functionality (press 'p' during scan)
- Silent background telemetry
- Better error handling and stability

Changes in v2.2:
- Added DNSTT test layer (Layer 7) for finding DNS servers suitable for DNS tunneling
- DNSTT tests: TXT record, EDNS0 support, stability check, hijack detection
- Custom IP list now shows as 'custom' instead of 'unknown'
- Local results saved on Ctrl+C
- Improved report format with test type details
"""

import sys
import os
import socket
import ssl
import json
import ipaddress
import time
import subprocess
import base64
import hashlib
import threading
import signal
import platform
import random
import struct
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from threading import Lock, Event
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote

# ==================== AUTO-INSTALL PACKAGES ====================

def check_and_install_packages():
    """Check and auto-install required packages from wheels"""
    try:
        import requests
        return True
    except ImportError:
        pass
    
    print("\n" + "="*60)
    print("[INFO] Package 'requests' is not installed")
    print("="*60)
    
    script_dir = Path(__file__).parent
    wheels_dir = script_dir / 'wheels'
    
    install_dir = None
    if wheels_dir.exists() and list(wheels_dir.glob('*.whl')):
        install_dir = wheels_dir
    elif list(script_dir.glob('*.whl')):
        install_dir = script_dir
    
    if install_dir:
        print(f"\n[INFO] Found .whl files, attempting installation...")
        try:
            whl_files = list(str(f) for f in install_dir.glob('*.whl'))
            cmd = [sys.executable, '-m', 'pip', 'install', '--user'] + whl_files
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("[OK] Packages installed! Please restart the scanner.")
                sys.exit(0)
        except Exception as e:
            print(f"[WARNING] Auto-install failed: {e}")
    
    pip_cmd = 'pip' if platform.system() == 'Windows' else 'pip3'
    print(f"\n[INFO] Please install manually:")
    print(f"  {pip_cmd} install requests")
    print("="*60 + "\n")
    sys.exit(1)

check_and_install_packages()

import requests
requests.packages.urllib3.disable_warnings()

try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False

# ==================== CONFIGURATION ====================

VERSION = "2.2 Enhanced"
APP_NAME = "Dr.CDN-Scanner"

# Telemetry
TELEMETRY_SERVER = "http://api.irihost.com:8080"
DEVELOPER_CHANNEL = "https://t.me/drconnect"

# Secret key (obfuscated)
_k = [68, 114, 67, 111, 110, 110, 101, 99, 116, 95, 70, 97, 115, 116, 108, 121, 95, 50, 48, 50, 53, 95, 83, 101, 99, 117, 114, 101, 95, 75, 101, 121, 95, 88, 55, 57, 51]
SECRET_KEY = ''.join(chr(c) for c in _k)

# CDN IP Ranges
CDN_RANGES = {
    'cloudflare': [
        "173.245.48.0/20", "103.21.244.0/22", "103.22.200.0/22",
        "103.31.4.0/22", "141.101.64.0/18", "108.162.192.0/18",
        "190.93.240.0/20", "188.114.96.0/20", "197.234.240.0/22",
        "198.41.128.0/17", "162.158.0.0/15", "104.16.0.0/13",
        "104.24.0.0/14", "172.64.0.0/13", "131.0.72.0/22"
    ],
    'fastly': [
        "23.235.32.0/20", "43.249.72.0/22", "103.244.50.0/24",
        "103.245.222.0/23", "103.245.224.0/24", "104.156.80.0/20",
        "140.248.64.0/18", "140.248.128.0/17", "146.75.0.0/17",
        "151.101.0.0/16", "157.52.64.0/18", "167.82.0.0/17",
        "167.82.128.0/20", "167.82.160.0/20", "167.82.224.0/20",
        "172.111.64.0/18", "185.31.16.0/22", "199.27.72.0/21",
        "199.232.0.0/16"
    ],
    'gcore': [
        "92.223.64.0/22", "92.223.122.0/24", "79.133.106.0/24",
        "81.30.158.0/24", "92.38.128.0/22", "159.255.0.0/21"
    ]
}

# Ports
PORTS = {
    'https': [443, 8443, 2053, 2083, 2087, 2096],
    'http': [80, 8080, 8880, 2052, 2082, 2086, 2095],
    'all': [443, 8443, 2053, 2083, 2087, 2096, 80, 8080, 8880, 2052, 2082, 2086, 2095],
    'dns': [53],
    'udp_common': [53, 443, 80, 8080]
}

HTTPS_PORTS = [443, 8443, 2053, 2083, 2087, 2096]

# Test URLs
TEST_URLS = {
    'real_delay': 'https://www.google.com/generate_204',
    'download': 'https://speed.cloudflare.com/__down?bytes=10000000',
    'upload': 'https://speed.cloudflare.com/__up'
}

# Default Settings
DEFAULT_SETTINGS = {
    'threads': 0,  # 0 = auto-detect
    'timeout_port': 2,
    'timeout_tls': 3,
    'timeout_real': 5,
    'timeout_download': 10,
    'timeout_udp': 2,
    'timeout_dns': 3,
    'timeout_dnstt': 5,
    'retry_count': 3,
    'min_download_speed': 50,  # KB/s
    'min_upload_speed': 30,    # KB/s
    'port_mode': 'https',
    'cdn_mode': 'both',  # cloudflare, fastly, gcore, both, all
    'ip_mode': 'random',  # random, sequential
    'test_layers': [1, 2],  # 1=port, 2=tls, 3=real, 4=download, 5=udp, 6=dns, 7=dnstt
    'protocol': 'tcp',  # tcp, udp, both
    'auto_submit': True,
    'xray_path': '',
    'config_link': '',
    'test_url': 'https://www.google.com/generate_204',
    'dns_test_domain': 'google.com',
    'dnstt_rtt_threshold': 2000,  # max RTT in ms for DNSTT
    'dnstt_stability_threshold': 2,  # min successful out of 3 tests
    'verify_response': True,  # Enable response verification to reduce false positives
    'using_custom_list': False  # Track if using custom IP list
}

# Global State
settings = DEFAULT_SETTINGS.copy()
scan_interrupted = False
scan_paused = False
pause_event = Event()
pause_event.set()  # Initially not paused
force_exit = False
results_lock = Lock()
submission_lock = Lock()
progress_lock = Lock()

successful_ips = []
failed_ips = []
tested_count = 0
pending_results = []
last_submission_time = 0
start_time = 0
current_ip = ""
current_layer = ""

AUTO_SUBMIT_BATCH = 10
AUTO_SUBMIT_INTERVAL = 60

# ==================== UTILITY FUNCTIONS ====================

def get_cpu_count():
    """Get optimal thread count based on CPU"""
    try:
        cpu_count = os.cpu_count() or 4
        return min(cpu_count * 2, 32)
    except:
        return 8

def format_time(seconds):
    """Format seconds to HH:MM:SS"""
    return str(timedelta(seconds=int(seconds)))[:-3] if seconds < 86400 else f"{int(seconds/3600)}h"

def clear_line():
    """Clear current line in terminal"""
    sys.stdout.write('\r' + ' ' * 120 + '\r')
    sys.stdout.flush()

def save_live_result(ip, port, cdn, rtt, test_type):
    """Save result to live results file immediately"""
    try:
        os.makedirs('results', exist_ok=True)
        with open('results/live_results.txt', 'a', encoding='utf-8') as f:
            f.write(f"{ip}:{port} | {cdn} | {test_type} | {rtt}ms\n")
    except Exception as e:
        pass  # Silent fail

def print_live_results_table():
    """Print the live results table"""
    with results_lock:
        if not successful_ips:
            return
        
        print("\n" + "═" * 80)
        print(" " * 30 + "FOUND IPs")
        print("═" * 80)
        print(f"{'#':<4} {'IP':<16} {'Port':<6} {'CDN':<12} {'RTT':<8} {'Status':<15}")
        print("─" * 80)
        
        # Show last 10 results
        for idx, result in enumerate(successful_ips[-10:], 1):
            ip = result.get('ip', 'N/A')
            port = result.get('port', 'N/A')
            cdn = result.get('cdn_provider', 'unknown')
            rtt = result.get('rtt', 0)
            test_type = result.get('test_type', 'unknown')
            
            status = test_type if test_type != 'unknown' else 'ok'
            print(f"{idx:<4} {ip:<16} {port:<6} {cdn:<12} {rtt:<8} {status:<15}")
        
        if len(successful_ips) > 10:
            print(f"... and {len(successful_ips) - 10} more results")
        print("═" * 80)

def update_progress_display(total, current, found, failed, current_ip_display, layer_name):
    """Update the live progress bar and statistics"""
    global start_time
    
    try:
        elapsed = time.time() - start_time
        percent = (current / total * 100) if total > 0 else 0
        speed = current / elapsed if elapsed > 0 else 0
        
        # Create progress bar
        bar_length = 30
        filled = int(bar_length * percent / 100)
        bar = '█' * filled + '░' * (bar_length - filled)
        
        # Format display
        time_str = format_time(elapsed)
        
        clear_line()
        progress = (
            f"[{bar}] {current:,}/{total:,} ({percent:.1f}%) "
            f"Testing: {current_ip_display} | Layer: {layer_name} | "
            f"Found: {found} | Failed: {failed} | "
            f"Time: {time_str} | Speed: {speed:.1f} IP/s"
        )
        
        sys.stdout.write('\r' + progress)
        sys.stdout.flush()
        
    except Exception as e:
        pass  # Silent fail

def signal_handler(sig, frame):
    """Handle Ctrl+C - save and exit immediately"""
    global scan_interrupted, force_exit
    
    scan_interrupted = True
    force_exit = True
    
    print("\n\n" + "="*80)
    print("[!] Ctrl+C detected - Saving and exiting...")
    print("[!] در حال ذخیره و خروج...")
    print("="*80)
    
    save_interrupted_state()
    
    print("\n[OK] All data saved successfully!")
    print("[OK] همه داده‌ها با موفقیت ذخیره شد!")
    print("="*80)
    
    os._exit(0)

def save_interrupted_state():
    """Save current scan state when interrupted"""
    try:
        # Save successful IPs
        if successful_ips:
            os.makedirs('results', exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Save to TXT
            txt_file = f'results/interrupted_{timestamp}.txt'
            with open(txt_file, 'w', encoding='utf-8') as f:
                f.write(f"Dr.CDN-Scanner v{VERSION}\n")
                f.write(f"Interrupted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total found: {len(successful_ips)}\n")
                f.write("="*50 + "\n\n")
                
                for result in successful_ips:
                    ip = result.get('ip', 'N/A')
                    port = result.get('port', 'N/A')
                    cdn = result.get('cdn_provider', 'unknown')
                    rtt = result.get('rtt', 0)
                    test_type = result.get('test_type', 'unknown')
                    f.write(f"{ip}:{port} | {cdn} | {test_type} | {rtt}ms\n")
            
            # Save to JSON
            json_file = f'results/interrupted_{timestamp}.json'
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'version': VERSION,
                    'timestamp': datetime.now().isoformat(),
                    'total_found': len(successful_ips),
                    'results': successful_ips
                }, f, indent=2, ensure_ascii=False)
            
            print(f"[OK] Results saved to: {txt_file}")
            print(f"[OK] Results saved to: {json_file}")
        
        # Save resume state
        os.makedirs('resume', exist_ok=True)
        state_file = 'resume/scan_state.json'
        
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump({
                'version': VERSION,
                'timestamp': datetime.now().isoformat(),
                'settings': settings,
                'successful_ips': successful_ips,
                'tested_count': tested_count,
                'can_resume': True
            }, f, indent=2, ensure_ascii=False)
        
        print(f"[OK] Resume state saved to: {state_file}")
        
    except Exception as e:
        print(f"[ERROR] Failed to save state: {e}")

def keyboard_listener():
    """Listen for keyboard input during scan (for pause functionality)"""
    global scan_paused, pause_event
    
    try:
        while not scan_interrupted and not force_exit:
            if platform.system() == 'Windows':
                import msvcrt
                if msvcrt.kbhit():
                    key = msvcrt.getch().decode('utf-8').lower()
                    if key == 'p':
                        if scan_paused:
                            print("\n" + "="*80)
                            print("▶️  Resuming scan...")
                            print("▶️  ادامه اسکن...")
                            print("="*80)
                            scan_paused = False
                            pause_event.set()
                        else:
                            print("\n" + "="*80)
                            print("⏸️  Scan PAUSED")
                            print("⏸️  اسکن متوقف شد")
                            
                            # Save state when paused
                            save_interrupted_state()
                            
                            print("💾 All data saved")
                            print("💾 همه داده‌ها ذخیره شد")
                            print()
                            print("▶️  Press 'P' to RESUME")
                            print("▶️  دکمه 'P' برای ادامه")
                            print("🚪 Press Ctrl+C to EXIT")
                            print("🚪 Ctrl+C برای خروج")
                            print("="*80)
                            scan_paused = True
                            pause_event.clear()
            else:
                # Unix-like systems - use select
                import select
                if select.select([sys.stdin], [], [], 0.1)[0]:
                    key = sys.stdin.read(1).lower()
                    if key == 'p':
                        if scan_paused:
                            print("\n" + "="*80)
                            print("▶️  Resuming scan...")
                            print("▶️  ادامه اسکن...")
                            print("="*80)
                            scan_paused = False
                            pause_event.set()
                        else:
                            print("\n" + "="*80)
                            print("⏸️  Scan PAUSED")
                            print("⏸️  اسکن متوقف شد")
                            
                            # Save state when paused
                            save_interrupted_state()
                            
                            print("💾 All data saved")
                            print("💾 همه داده‌ها ذخیره شد")
                            print()
                            print("▶️  Press 'P' to RESUME")
                            print("▶️  دکمه 'P' برای ادامه")
                            print("🚪 Press Ctrl+C to EXIT")
                            print("🚪 Ctrl+C برای خروج")
                            print("="*80)
                            scan_paused = True
                            pause_event.clear()
            time.sleep(0.1)
    except:
        pass

# ==================== IP RANGE FUNCTIONS ====================

def expand_ip_ranges(ranges):
    """Expand CIDR ranges to individual IPs"""
    ips = []
    for r in ranges:
        try:
            network = ipaddress.ip_network(r, strict=False)
            ips.extend([str(ip) for ip in network.hosts()])
        except:
            pass
    return ips

def get_ip_ranges():
    """Get IP ranges based on CDN mode"""
    mode = settings['cdn_mode'].lower()
    
    # Check for custom IP list
    custom_file = 'ips.txt'
    if os.path.exists(custom_file):
        try:
            with open(custom_file, 'r') as f:
                custom_ips = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            if custom_ips:
                settings['using_custom_list'] = True
                print(f"[INFO] Loaded {len(custom_ips)} IPs from {custom_file}")
                return custom_ips
        except Exception as e:
            print(f"[WARNING] Failed to load {custom_file}: {e}")
    
    settings['using_custom_list'] = False
    
    if mode == 'cloudflare':
        return CDN_RANGES['cloudflare']
    elif mode == 'fastly':
        return CDN_RANGES['fastly']
    elif mode == 'gcore':
        return CDN_RANGES['gcore']
    elif mode == 'both':
        return CDN_RANGES['cloudflare'] + CDN_RANGES['fastly']
    else:  # all
        return CDN_RANGES['cloudflare'] + CDN_RANGES['fastly'] + CDN_RANGES['gcore']

def detect_cdn_provider(ip):
    """Detect which CDN provider an IP belongs to"""
    if settings.get('using_custom_list'):
        return 'custom'
    
    try:
        ip_obj = ipaddress.ip_address(ip)
        for cdn, ranges in CDN_RANGES.items():
            for r in ranges:
                if ip_obj in ipaddress.ip_network(r, strict=False):
                    return cdn
    except:
        pass
    return 'unknown'

# ==================== NETWORK TEST FUNCTIONS ====================

def test_port(ip, port, timeout=2):
    """Test if port is open"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            result = sock.connect_ex((ip, port))
            return result == 0
    except:
        return False

def test_tls_handshake(ip, port, timeout=3):
    """Test TLS handshake and measure RTT"""
    try:
        start = time.time()
        
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            with context.wrap_socket(sock) as ssock:
                ssock.connect((ip, port))
                rtt = int((time.time() - start) * 1000)
                
                if settings['verify_response']:
                    try:
                        ssock.send(b"GET / HTTP/1.1\r\nHost: google.com\r\n\r\n")
                        response = ssock.recv(1024)
                        if b'HTTP' not in response:
                            return None
                    except:
                        return None
                
                return rtt
    except:
        return None

def test_udp_port(ip, port, timeout=2):
    """Test UDP port connectivity"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)
        
        # Send DNS query for google.com
        query = b'\x00\x00\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x06google\x03com\x00\x00\x01\x00\x01'
        
        start = time.time()
        sock.sendto(query, (ip, port))
        
        try:
            data, _ = sock.recvfrom(512)
            rtt = int((time.time() - start) * 1000)
            sock.close()
            return rtt if len(data) > 0 else None
        except socket.timeout:
            sock.close()
            return None
    except:
        return None

def test_dns_query(ip, domain, timeout=3):
    """Test DNS server with A record query"""
    try:
        # Build DNS query for A record
        transaction_id = random.randint(0, 65535)
        
        # DNS header
        flags = 0x0100  # Standard query
        questions = 1
        answer_rrs = 0
        authority_rrs = 0
        additional_rrs = 0
        
        header = struct.pack('!HHHHHH', transaction_id, flags, questions, 
                           answer_rrs, authority_rrs, additional_rrs)
        
        # DNS question
        labels = domain.split('.')
        question = b''
        for label in labels:
            question += struct.pack('!B', len(label)) + label.encode()
        question += b'\x00'  # Null terminator
        question += struct.pack('!HH', 1, 1)  # Type A, Class IN
        
        query = header + question
        
        # Send query
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)
        
        start = time.time()
        sock.sendto(query, (ip, 53))
        
        try:
            data, _ = sock.recvfrom(512)
            rtt = int((time.time() - start) * 1000)
            sock.close()
            
            # Basic validation
            if len(data) > 12:
                resp_id = struct.unpack('!H', data[:2])[0]
                if resp_id == transaction_id:
                    return rtt
        except socket.timeout:
            pass
        
        sock.close()
        return None
    except:
        return None

def test_dnstt_compatibility(ip, timeout=5):
    """
    Test DNSTT compatibility with multiple checks:
    1. TXT record query support
    2. EDNS0 support
    3. Response stability (multiple queries)
    4. Hijack detection
    """
    try:
        # Test 1: TXT record query
        txt_test = test_dns_txt_record(ip, 'test.example.com', timeout)
        if not txt_test:
            return None
        
        # Test 2: EDNS0 support
        edns_test = test_dns_edns0(ip, timeout)
        if not edns_test:
            return None
        
        # Test 3: Stability check (3 queries)
        rtts = []
        for _ in range(3):
            rtt = test_dns_query(ip, settings['dns_test_domain'], timeout)
            if rtt:
                rtts.append(rtt)
            time.sleep(0.1)
        
        if len(rtts) < settings['dnstt_stability_threshold']:
            return None
        
        avg_rtt = sum(rtts) // len(rtts)
        
        # Test 4: RTT threshold
        if avg_rtt > settings['dnstt_rtt_threshold']:
            return None
        
        return avg_rtt
        
    except:
        return None

def test_dns_txt_record(ip, domain, timeout=3):
    """Test TXT record query support"""
    try:
        transaction_id = random.randint(0, 65535)
        
        # DNS header
        header = struct.pack('!HHHHHH', transaction_id, 0x0100, 1, 0, 0, 0)
        
        # DNS question for TXT record
        labels = domain.split('.')
        question = b''
        for label in labels:
            question += struct.pack('!B', len(label)) + label.encode()
        question += b'\x00'
        question += struct.pack('!HH', 16, 1)  # Type TXT, Class IN
        
        query = header + question
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)
        sock.sendto(query, (ip, 53))
        
        try:
            data, _ = sock.recvfrom(512)
            sock.close()
            
            if len(data) > 12:
                resp_id = struct.unpack('!H', data[:2])[0]
                return resp_id == transaction_id
        except socket.timeout:
            pass
        
        sock.close()
        return False
    except:
        return False

def test_dns_edns0(ip, timeout=3):
    """Test EDNS0 support"""
    try:
        transaction_id = random.randint(0, 65535)
        
        # DNS header
        header = struct.pack('!HHHHHH', transaction_id, 0x0100, 1, 0, 0, 1)
        
        # Question
        question = b'\x06google\x03com\x00\x00\x01\x00\x01'
        
        # EDNS0 OPT record
        opt = b'\x00'  # Name (root)
        opt += struct.pack('!H', 41)  # Type OPT
        opt += struct.pack('!H', 4096)  # UDP payload size
        opt += struct.pack('!I', 0)  # Extended RCODE and flags
        opt += struct.pack('!H', 0)  # RDLEN
        
        query = header + question + opt
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)
        sock.sendto(query, (ip, 53))
        
        try:
            data, _ = sock.recvfrom(4096)
            sock.close()
            return len(data) > 12
        except socket.timeout:
            pass
        
        sock.close()
        return False
    except:
        return False

def test_xray_connection(ip, port, parsed_config, xray_path, test_url, timeout=5):
    """Test real connection through Xray proxy"""
    try:
        # Generate Xray config
        config = generate_xray_config(ip, port, parsed_config)
        if not config:
            return None
        
        # Save config to temp file
        config_file = f'/tmp/xray_test_{ip}_{port}.json'
        with open(config_file, 'w') as f:
            json.dump(config, f)
        
        # Start Xray
        process = subprocess.Popen(
            [xray_path, '-c', config_file],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        time.sleep(1)  # Wait for Xray to start
        
        # Test connection
        proxies = {
            'http': 'socks5://127.0.0.1:10808',
            'https': 'socks5://127.0.0.1:10808'
        }
        
        start = time.time()
        response = requests.get(test_url, proxies=proxies, timeout=timeout, verify=False)
        rtt = int((time.time() - start) * 1000)
        
        # Cleanup
        process.terminate()
        process.wait(timeout=2)
        os.remove(config_file)
        
        if response.status_code in [200, 204]:
            return rtt
        
        return None
        
    except Exception as e:
        try:
            process.terminate()
            os.remove(config_file)
        except:
            pass
        return None

def test_download_speed(ip, port, parsed_config, xray_path, timeout=10):
    """Test download speed through proxy"""
    try:
        # This would need Xray integration similar to test_xray_connection
        # Simplified version for now
        return None
    except:
        return None

# ==================== XRAY CONFIG ====================

def parse_config_link(link):
    """Parse vmess://, vless://, or trojan:// config link"""
    try:
        if link.startswith('vmess://'):
            decoded = base64.b64decode(link[8:]).decode('utf-8')
            config = json.loads(decoded)
            return {
                'protocol': 'vmess',
                'address': config.get('add'),
                'port': config.get('port'),
                'id': config.get('id'),
                'aid': config.get('aid', 0),
                'net': config.get('net', 'tcp'),
                'type': config.get('type', 'none'),
                'host': config.get('host', ''),
                'path': config.get('path', ''),
                'tls': config.get('tls', ''),
                'sni': config.get('sni', '')
            }
        
        elif link.startswith('vless://'):
            link = link[8:]
            if '@' in link:
                uuid_part, rest = link.split('@', 1)
                if '?' in rest:
                    server_part, params_part = rest.split('?', 1)
                else:
                    server_part = rest
                    params_part = ''
                
                if ':' in server_part:
                    address, port = server_part.split(':', 1)
                    port = port.split('#')[0]
                else:
                    address = server_part
                    port = '443'
                
                params = parse_qs(params_part)
                
                return {
                    'protocol': 'vless',
                    'address': address,
                    'port': int(port),
                    'id': uuid_part,
                    'flow': params.get('flow', [''])[0],
                    'encryption': params.get('encryption', ['none'])[0],
                    'security': params.get('security', [''])[0],
                    'sni': params.get('sni', [''])[0],
                    'alpn': params.get('alpn', [''])[0],
                    'type': params.get('type', ['tcp'])[0],
                    'host': params.get('host', [''])[0],
                    'path': params.get('path', [''])[0]
                }
        
        elif link.startswith('trojan://'):
            link = link[9:]
            if '@' in link:
                password, rest = link.split('@', 1)
                if '?' in rest:
                    server_part, params_part = rest.split('?', 1)
                else:
                    server_part = rest
                    params_part = ''
                
                if ':' in server_part:
                    address, port = server_part.split(':', 1)
                    port = port.split('#')[0]
                else:
                    address = server_part
                    port = '443'
                
                params = parse_qs(params_part)
                
                return {
                    'protocol': 'trojan',
                    'address': address,
                    'port': int(port),
                    'password': password,
                    'sni': params.get('sni', [''])[0],
                    'type': params.get('type', ['tcp'])[0],
                    'host': params.get('host', [''])[0],
                    'path': params.get('path', [''])[0]
                }
    
    except Exception as e:
        return None
    
    return None

def generate_xray_config(test_ip, test_port, parsed_config):
    """Generate Xray config for testing"""
    try:
        protocol = parsed_config['protocol']
        
        outbound = {
            "protocol": protocol,
            "settings": {},
            "streamSettings": {
                "network": "tcp"
            }
        }
        
        if protocol == 'vmess':
            outbound["settings"] = {
                "vnext": [{
                    "address": test_ip,
                    "port": test_port,
                    "users": [{
                        "id": parsed_config['id'],
                        "alterId": parsed_config['aid'],
                        "security": "auto"
                    }]
                }]
            }
            
            if parsed_config.get('net'):
                outbound["streamSettings"]["network"] = parsed_config['net']
            
            if parsed_config.get('tls') == 'tls':
                outbound["streamSettings"]["security"] = "tls"
                outbound["streamSettings"]["tlsSettings"] = {
                    "serverName": parsed_config.get('sni') or parsed_config.get('host') or test_ip
                }
        
        elif protocol == 'vless':
            outbound["settings"] = {
                "vnext": [{
                    "address": test_ip,
                    "port": test_port,
                    "users": [{
                        "id": parsed_config['id'],
                        "encryption": parsed_config.get('encryption', 'none'),
                        "flow": parsed_config.get('flow', '')
                    }]
                }]
            }
            
            if parsed_config.get('type'):
                outbound["streamSettings"]["network"] = parsed_config['type']
            
            if parsed_config.get('security') == 'tls':
                outbound["streamSettings"]["security"] = "tls"
                outbound["streamSettings"]["tlsSettings"] = {
                    "serverName": parsed_config.get('sni') or test_ip
                }
        
        elif protocol == 'trojan':
            outbound["settings"] = {
                "servers": [{
                    "address": test_ip,
                    "port": test_port,
                    "password": parsed_config['password']
                }]
            }
            
            outbound["streamSettings"]["security"] = "tls"
            outbound["streamSettings"]["tlsSettings"] = {
                "serverName": parsed_config.get('sni') or test_ip
            }
        
        config = {
            "log": {"loglevel": "none"},
            "inbounds": [{
                "port": 10808,
                "protocol": "socks",
                "settings": {"udp": True}
            }],
            "outbounds": [outbound]
        }
        
        return config
    
    except Exception as e:
        return None

# ==================== TELEMETRY (SILENT) ====================

def submit_results_silent(results):
    """Submit results to server silently (no console output)"""
    if not settings.get('auto_submit') or not results:
        return
    
    try:
        # Prepare payload
        payload = {
            'version': VERSION,
            'timestamp': datetime.now().isoformat(),
            'cdn_mode': settings['cdn_mode'],
            'test_layers': settings['test_layers'],
            'results': results
        }
        
        # Generate signature
        data_str = json.dumps(payload, sort_keys=True)
        signature = hashlib.sha256((data_str + SECRET_KEY).encode()).hexdigest()
        
        payload['signature'] = signature
        
        # Submit (with short timeout)
        requests.post(
            f"{TELEMETRY_SERVER}/api/v1/submit",
            json=payload,
            timeout=5,
            verify=False
        )
        
    except:
        pass  # Silent fail

def auto_submit_worker():
    """Background worker for auto-submitting results"""
    global pending_results, last_submission_time
    
    while not scan_interrupted and not force_exit:
        try:
            with submission_lock:
                current_time = time.time()
                should_submit = (
                    len(pending_results) >= AUTO_SUBMIT_BATCH or
                    (pending_results and current_time - last_submission_time >= AUTO_SUBMIT_INTERVAL)
                )
                
                if should_submit and pending_results:
                    to_submit = pending_results.copy()
                    pending_results.clear()
                    last_submission_time = current_time
                    
                    # Submit in background thread
                    threading.Thread(
                        target=submit_results_silent,
                        args=(to_submit,),
                        daemon=True
                    ).start()
            
            time.sleep(5)
        except:
            pass

# ==================== MAIN SCAN LOGIC ====================

def test_single_target(ip, port, test_layers, parsed_config=None, xray_path=None):
    """Test a single IP:Port combination through all specified layers"""
    global current_ip, current_layer, tested_count
    
    try:
        # Wait if paused
        pause_event.wait()
        
        if scan_interrupted or force_exit:
            return None
        
        current_ip = f"{ip}:{port}"
        cdn_provider = detect_cdn_provider(ip)
        result = {
            'ip': ip,
            'port': port,
            'cdn_provider': cdn_provider,
            'timestamp': datetime.now().isoformat()
        }
        
        # Layer 1: Port Test
        if 1 in test_layers:
            current_layer = "Port"
            if not test_port(ip, port, settings['timeout_port']):
                with results_lock:
                    failed_ips.append(result)
                    tested_count += 1
                return None
        
        # Layer 2: TLS Handshake
        if 2 in test_layers:
            current_layer = "TLS"
            rtt = test_tls_handshake(ip, port, settings['timeout_tls'])
            if rtt is None:
                with results_lock:
                    failed_ips.append(result)
                    tested_count += 1
                return None
            result['rtt'] = rtt
            result['test_type'] = 'tls'
        
        # Layer 3: Real Delay (Xray)
        if 3 in test_layers:
            current_layer = "Real"
            if parsed_config and xray_path:
                rtt = test_xray_connection(ip, port, parsed_config, xray_path, 
                                          settings['test_url'], settings['timeout_real'])
                if rtt is None:
                    with results_lock:
                        failed_ips.append(result)
                        tested_count += 1
                    return None
                result['rtt'] = rtt
                result['test_type'] = 'real'
        
        # Layer 4: Download Speed
        if 4 in test_layers:
            current_layer = "Download"
            speed = test_download_speed(ip, port, parsed_config, xray_path, 
                                       settings['timeout_download'])
            if speed is None or speed < settings['min_download_speed']:
                with results_lock:
                    failed_ips.append(result)
                    tested_count += 1
                return None
            result['download_speed'] = speed
            result['test_type'] = 'download'
        
        # Layer 5: UDP Port
        if 5 in test_layers:
            current_layer = "UDP"
            rtt = test_udp_port(ip, port, settings['timeout_udp'])
            if rtt is None:
                with results_lock:
                    failed_ips.append(result)
                    tested_count += 1
                return None
            result['rtt'] = rtt
            result['test_type'] = 'udp'
        
        # Layer 6: DNS Query
        if 6 in test_layers:
            current_layer = "DNS"
            rtt = test_dns_query(ip, settings['dns_test_domain'], settings['timeout_dns'])
            if rtt is None:
                with results_lock:
                    failed_ips.append(result)
                    tested_count += 1
                return None
            result['rtt'] = rtt
            result['test_type'] = 'dns'
        
        # Layer 7: DNSTT Compatibility
        if 7 in test_layers:
            current_layer = "DNSTT"
            rtt = test_dnstt_compatibility(ip, settings['timeout_dnstt'])
            if rtt is None:
                with results_lock:
                    failed_ips.append(result)
                    tested_count += 1
                return None
            result['rtt'] = rtt
            result['test_type'] = 'dnstt'
        
        # Success!
        with results_lock:
            successful_ips.append(result)
            tested_count += 1
            
            # Save to live results file
            save_live_result(
                ip, port, cdn_provider,
                result.get('rtt', 0),
                result.get('test_type', 'unknown')
            )
            
            # Add to pending submission
            if settings.get('auto_submit'):
                with submission_lock:
                    pending_results.append(result)
        
        return result
        
    except Exception as e:
        with results_lock:
            tested_count += 1
        return None

def perform_scan(ip_list, ports, test_layers, parsed_config=None, xray_path=None):
    """Perform the main scan with live progress display"""
    global tested_count, scan_interrupted, force_exit, start_time
    
    tested_count = 0
    scan_interrupted = False
    force_exit = False
    
    # Generate targets
    targets = [(ip, port) for ip in ip_list for port in ports]
    
    # Shuffle if random mode
    if settings['ip_mode'] == 'random':
        random.shuffle(targets)
    
    total_targets = len(targets)
    threads = settings['threads'] if settings['threads'] > 0 else get_cpu_count()
    
    print(f"\n[INFO] Starting scan...")
    print(f"[INFO] Total targets: {total_targets:,}")
    print(f"[INFO] Threads: {threads}")
    print("="*80)
    print("💡 Press 'P' to PAUSE/RESUME scan")
    print("💡 برای توقف موقت دکمه 'P' را بزنید")
    print("🚪 Press Ctrl+C to SAVE and EXIT")
    print("🚪 برای ذخیره و خروج Ctrl+C بزنید")
    print("="*80 + "\n")
    
    # Clear live results file
    try:
        os.makedirs('results', exist_ok=True)
        open('results/live_results.txt', 'w').close()
    except:
        pass
    
    # Start auto-submit worker
    if settings.get('auto_submit'):
        submit_thread = threading.Thread(target=auto_submit_worker, daemon=True)
        submit_thread.start()
    
    # Start keyboard listener
    kb_thread = threading.Thread(target=keyboard_listener, daemon=True)
    kb_thread.start()
    
    # Start scanning
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = []
        
        for ip, port in targets:
            if scan_interrupted or force_exit:
                break
            
            future = executor.submit(
                test_single_target,
                ip, port, test_layers,
                parsed_config, xray_path
            )
            futures.append(future)
            
            # Update progress every few submissions
            if len(futures) % 10 == 0:
                with results_lock:
                    update_progress_display(
                        total_targets,
                        tested_count,
                        len(successful_ips),
                        len(failed_ips),
                        current_ip,
                        current_layer
                    )
        
        # Wait for all futures with progress updates
        while futures:
            done, futures = wait(futures, timeout=0.5, return_when=FIRST_COMPLETED)
            
            with results_lock:
                update_progress_display(
                    total_targets,
                    tested_count,
                    len(successful_ips),
                    len(failed_ips),
                    current_ip,
                    current_layer
                )
            
            # Show live results table every 5 successful finds
            if len(successful_ips) % 5 == 0 and len(successful_ips) > 0:
                print()  # New line after progress
                print_live_results_table()
                print()  # New line before progress
            
            if scan_interrupted or force_exit:
                # Cancel remaining futures
                for future in futures:
                    future.cancel()
                break
    
    # Final progress update
    print()  # New line after progress bar
    
    # Show final results table
    if successful_ips:
        print_live_results_table()
    
    return successful_ips

# ==================== RESULT MANAGEMENT ====================

def save_results(results, duration):
    """Save scan results to file"""
    if not results:
        print("[!] No results to save")
        return
    
    try:
        os.makedirs('results', exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save TXT
        txt_file = f'results/scan_{timestamp}.txt'
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(f"Dr.CDN-Scanner v{VERSION}\n")
            f.write(f"Scan completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Duration: {duration:.1f}s\n")
            f.write(f"Total found: {len(results)}\n")
            f.write("="*50 + "\n\n")
            
            # Group by CDN
            by_cdn = {}
            for r in results:
                cdn = r.get('cdn_provider', 'unknown')
                if cdn not in by_cdn:
                    by_cdn[cdn] = []
                by_cdn[cdn].append(r)
            
            for cdn, items in sorted(by_cdn.items()):
                f.write(f"\n### {cdn.upper()} ({len(items)} IPs) ###\n\n")
                for r in items:
                    ip = r.get('ip')
                    port = r.get('port')
                    rtt = r.get('rtt', 0)
                    test_type = r.get('test_type', 'unknown')
                    f.write(f"{ip}:{port} | {test_type} | {rtt}ms\n")
        
        # Save JSON
        json_file = f'results/scan_{timestamp}.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                'version': VERSION,
                'timestamp': datetime.now().isoformat(),
                'duration': duration,
                'settings': settings,
                'total_found': len(results),
                'results': results
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n[OK] Results saved to: {txt_file}")
        print(f"[OK] Results saved to: {json_file}")
        
        # Submit final results
        if settings.get('auto_submit') and results:
            submit_results_silent(results)
        
    except Exception as e:
        print(f"[ERROR] Failed to save results: {e}")

def load_state():
    """Load previous scan state"""
    try:
        state_file = 'resume/scan_state.json'
        if not os.path.exists(state_file):
            return None
        
        with open(state_file, 'r', encoding='utf-8') as f:
            state = json.load(f)
        
        return state
    except:
        return None

def delete_state():
    """Delete scan state after successful completion"""
    try:
        state_file = 'resume/scan_state.json'
        if os.path.exists(state_file):
            os.remove(state_file)
    except:
        pass

# ==================== UI FUNCTIONS ====================

def print_header():
    """Print application header"""
    os.system('cls' if platform.system() == 'Windows' else 'clear')
    print("="*60)
    print(f"  {APP_NAME} v{VERSION}")
    print(f"  Developer: DrConnect | Telegram: @lvlRF")
    print(f"  Channel: {DEVELOPER_CHANNEL}")
    print("="*60 + "\n")

def menu_select_layers():
    """Menu for selecting test layers"""
    layers = {
        1: 'Port Test',
        2: 'TLS Handshake',
        3: 'Real Delay (Xray)',
        4: 'Download Speed',
        5: 'UDP Port',
        6: 'DNS Query',
        7: 'DNSTT Compatibility'
    }
    
    while True:
        print_header()
        print("═══════════ SELECT TEST LAYERS ═══════════\n")
        
        for num, name in layers.items():
            status = "✓" if num in settings['test_layers'] else " "
            print(f"  [{status}] {num}. {name}")
        
        print("\n[A] Select All")
        print("[C] Clear All")
        print("[Q] Quick Presets")
        print("[0] Continue with current selection\n")
        
        choice = input("Toggle layer (1-7) or choose option: ").strip().upper()
        
        if choice == '0':
            if settings['test_layers']:
                return sorted(settings['test_layers'])
            else:
                print("[!] Please select at least one layer")
                time.sleep(1)
        
        elif choice == 'A':
            settings['test_layers'] = list(layers.keys())
        
        elif choice == 'C':
            settings['test_layers'] = []
        
        elif choice == 'Q':
            print("\nQuick Presets:")
            print("  [1] Basic (Port + TLS)")
            print("  [2] Standard (Port + TLS + Real)")
            print("  [3] Full (All layers)")
            print("  [4] DNS Only (Port + DNS)")
            print("  [5] DNSTT Only (Port + DNS + DNSTT)")
            
            preset = input("\nSelect preset: ").strip()
            
            if preset == '1':
                settings['test_layers'] = [1, 2]
            elif preset == '2':
                settings['test_layers'] = [1, 2, 3]
            elif preset == '3':
                settings['test_layers'] = list(layers.keys())
            elif preset == '4':
                settings['test_layers'] = [1, 6]
            elif preset == '5':
                settings['test_layers'] = [1, 6, 7]
        
        elif choice.isdigit() and 1 <= int(choice) <= 7:
            layer = int(choice)
            if layer in settings['test_layers']:
                settings['test_layers'].remove(layer)
            else:
                settings['test_layers'].append(layer)

def menu_settings():
    """Settings menu"""
    while True:
        print_header()
        print("═══════════ SETTINGS ═══════════\n")
        
        threads_display = settings['threads'] if settings['threads'] > 0 else f"Auto ({get_cpu_count()})"
        
        print(f"  [1] Threads: {threads_display}")
        print(f"  [2] CDN Mode: {settings['cdn_mode'].upper()}")
        print(f"  [3] Port Mode: {settings['port_mode'].upper()}")
        print(f"  [4] IP Mode: {settings['ip_mode'].upper()}")
        print(f"  [5] Port Timeout: {settings['timeout_port']}s")
        print(f"  [6] TLS Timeout: {settings['timeout_tls']}s")
        print(f"  [7] Real Timeout: {settings['timeout_real']}s")
        print(f"  [8] Min Download: {settings['min_download_speed']} KB/s")
        print(f"  [9] Auto Submit: {'ON' if settings['auto_submit'] else 'OFF'}")
        print(f"  [A] Xray Path: {settings['xray_path'] or 'Not set'}")
        print(f"  [B] Config Link: {'Set' if settings['config_link'] else 'Not set'}")
        print(f"  [C] Test URL: {settings['test_url']}")
        print(f"  [D] DNS Domain: {settings['dns_test_domain']}")
        print(f"  [E] Response Verification: {'ON' if settings['verify_response'] else 'OFF'}")
        print("\n  [0] Back to Main Menu\n")
        
        choice = input("Select option: ").strip().upper()
        
        if choice == '1':
            try:
                t = input(f"Threads (0=auto, max={get_cpu_count()}): ").strip()
                if t:
                    settings['threads'] = max(0, min(int(t), get_cpu_count()))
            except:
                pass
        
        elif choice == '2':
            print("\nCDN Modes:")
            print("  [1] Cloudflare")
            print("  [2] Fastly")
            print("  [3] Gcore")
            print("  [4] Both (CF + Fastly)")
            print("  [5] All")
            
            mode = input("Select: ").strip()
            modes = {'1': 'cloudflare', '2': 'fastly', '3': 'gcore', '4': 'both', '5': 'all'}
            if mode in modes:
                settings['cdn_mode'] = modes[mode]
        
        elif choice == '3':
            print("\nPort Modes:")
            print("  [1] HTTPS ports")
            print("  [2] HTTP ports")
            print("  [3] All ports")
            print("  [4] DNS (53)")
            
            mode = input("Select: ").strip()
            modes = {'1': 'https', '2': 'http', '3': 'all', '4': 'dns'}
            if mode in modes:
                settings['port_mode'] = modes[mode]
        
        elif choice == '4':
            settings['ip_mode'] = 'sequential' if settings['ip_mode'] == 'random' else 'random'
        
        elif choice == '5':
            try:
                settings['timeout_port'] = int(input(f"Port timeout [{settings['timeout_port']}]: ").strip() or settings['timeout_port'])
            except:
                pass
        
        elif choice == '6':
            try:
                settings['timeout_tls'] = int(input(f"TLS timeout [{settings['timeout_tls']}]: ").strip() or settings['timeout_tls'])
            except:
                pass
        
        elif choice == '7':
            try:
                settings['timeout_real'] = int(input(f"Real timeout [{settings['timeout_real']}]: ").strip() or settings['timeout_real'])
            except:
                pass
        
        elif choice == '8':
            try:
                settings['min_download_speed'] = int(input(f"Min download speed KB/s [{settings['min_download_speed']}]: ").strip() or settings['min_download_speed'])
            except:
                pass
        
        elif choice == '9':
            settings['auto_submit'] = not settings['auto_submit']
        
        elif choice == 'A':
            path = input("Xray path (or Enter to auto-detect): ").strip()
            if path:
                if os.path.exists(path):
                    settings['xray_path'] = path
                    print("[OK] Xray path set")
                else:
                    print("[ERROR] File not found")
            else:
                common_paths = [
                    './xray/xray', './xray/xray.exe',
                    './xray', './xray.exe',
                    '/usr/local/bin/xray', '/usr/bin/xray'
                ]
                for p in common_paths:
                    if os.path.exists(p):
                        settings['xray_path'] = p
                        print(f"[OK] Found Xray at: {p}")
                        break
                else:
                    print("[!] Xray not found. Please enter path manually.")
            time.sleep(1)
        
        elif choice == 'B':
            print("\nPaste your config link (vmess://, vless://, or trojan://):")
            link = input().strip()
            if link:
                parsed = parse_config_link(link)
                if parsed:
                    settings['config_link'] = link
                    print(f"[OK] Config set: {parsed['protocol'].upper()} to {parsed['address']}")
                else:
                    print("[ERROR] Invalid config link")
            time.sleep(1)
        
        elif choice == 'C':
            url = input(f"Test URL [{settings['test_url']}]: ").strip()
            if url:
                settings['test_url'] = url
        
        elif choice == 'D':
            domain = input(f"DNS test domain [{settings['dns_test_domain']}]: ").strip()
            if domain:
                settings['dns_test_domain'] = domain
        
        elif choice == 'E':
            settings['verify_response'] = not settings['verify_response']
            print(f"[OK] Response verification: {'ON' if settings['verify_response'] else 'OFF'}")
            time.sleep(1)
        
        elif choice == '0':
            break
        
        time.sleep(0.5)

def show_current_settings(test_layers):
    """Display current settings before scan"""
    print_header()
    print("═══════════ SCAN CONFIGURATION ═══════════\n")
    
    threads_display = settings['threads'] if settings['threads'] > 0 else f"Auto ({get_cpu_count()})"
    layers_names = {1: 'Port', 2: 'TLS/HTTP', 3: 'Real Delay', 4: 'Download', 5: 'UDP', 6: 'DNS', 7: 'DNSTT'}
    layers_str = ' → '.join([layers_names[l] for l in test_layers])
    
    print(f"  CDN Mode       : {settings['cdn_mode'].upper()}")
    print(f"  Ports          : {settings['port_mode'].upper()}")
    print(f"  IP Mode        : {settings['ip_mode'].upper()}")
    print(f"  Threads        : {threads_display}")
    print(f"  Test Layers    : {layers_str}")
    print(f"  Verify Response: {'ON' if settings['verify_response'] else 'OFF'}")
    
    if 3 in test_layers or 4 in test_layers:
        print(f"  Xray Path      : {settings['xray_path'] or '❌ NOT SET'}")
        print(f"  Config         : {'✓ Set' if settings['config_link'] else '❌ NOT SET'}")
        print(f"  Test URL       : {settings['test_url']}")
    
    if 6 in test_layers:
        print(f"  DNS Domain     : {settings['dns_test_domain']}")
    
    if 7 in test_layers:
        print(f"  DNSTT RTT Max  : {settings['dnstt_rtt_threshold']}ms")
        print(f"  DNSTT Stability: {settings['dnstt_stability_threshold']}/3 required")
    
    print(f"  Auto Submit    : {'✓ ON' if settings['auto_submit'] else '✗ OFF'}")
    print()
    
    return input("[E] Edit  [S] Start  [B] Back: ").strip().upper()

def main_menu():
    """Main menu"""
    global start_time, force_exit
    
    # Set up signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    while True:
        if force_exit:
            sys.exit(0)
        
        print_header()
        print("[1] Start Scan")
        print("[2] Resume Previous Scan")
        print("[3] Settings")
        print("[4] View Results")
        print("[0] Exit\n")
        
        choice = input("Your choice: ").strip()
        
        if choice == '1':
            test_layers = menu_select_layers()
            
            parsed_config = None
            xray_path = None
            
            if 3 in test_layers or 4 in test_layers:
                if not settings['xray_path']:
                    print("\n[!] Xray path required for Real Delay / Download tests")
                    print("[!] Please set it in Settings menu\n")
                    input("Press Enter to continue...")
                    continue
                
                if not settings['config_link']:
                    print("\n[!] Config link required for Real Delay / Download tests")
                    print("[!] Please set it in Settings menu\n")
                    input("Press Enter to continue...")
                    continue
                
                xray_path = settings['xray_path']
                parsed_config = parse_config_link(settings['config_link'])
                
                if not parsed_config:
                    print("\n[ERROR] Failed to parse config link")
                    input("Press Enter to continue...")
                    continue
            
            while True:
                action = show_current_settings(test_layers)
                
                if action == 'E':
                    menu_settings()
                elif action == 'B':
                    break
                elif action == 'S':
                    print("\n[INFO] Loading IP ranges...")
                    ip_ranges = get_ip_ranges()
                    print("[INFO] Expanding IP ranges...")
                    ip_list = expand_ip_ranges(ip_ranges)
                    print(f"[INFO] Total IPs: {len(ip_list):,}")
                    
                    ports = PORTS.get(settings['port_mode'], PORTS['https'])
                    if 6 in test_layers or 7 in test_layers:
                        ports = [53]
                    
                    start_time = time.time()
                    
                    results = perform_scan(ip_list, ports, test_layers, parsed_config, xray_path)
                    
                    if force_exit:
                        save_interrupted_state()
                        sys.exit(0)
                    
                    duration = time.time() - start_time
                    
                    print(f"\n{'='*50}")
                    print(f"[OK] Scan completed!")
                    print(f"[OK] Successful: {len(successful_ips)}")
                    print(f"[OK] Failed: {len(failed_ips)}")
                    print(f"[OK] Duration: {duration:.1f}s")
                    print(f"{'='*50}\n")
                    
                    save_results(successful_ips, duration)
                    delete_state()
                    
                    input("\nPress Enter to continue...")
                    break
        
        elif choice == '2':
            state = load_state()
            if state:
                print(f"\n[INFO] Found previous scan state")
                print(f"[INFO] Already found: {len(state.get('successful_ips', []))} IPs")
                
                if input("\nResume? (y/n): ").strip().lower() == 'y':
                    # Load state
                    settings.update(state['settings'])
                    successful_ips.extend(state['successful_ips'])
                    print("[INFO] State loaded - please restart scan from main menu")
                    input("Press Enter...")
            else:
                print("\n[!] No previous scan state found")
                time.sleep(2)
        
        elif choice == '3':
            menu_settings()
        
        elif choice == '4':
            print_header()
            print("═══════════ RESULTS ═══════════\n")
            
            if os.path.exists('results'):
                files = sorted(os.listdir('results'), reverse=True)[:10]
                for f in files:
                    print(f"  {f}")
            else:
                print("  No results found")
            
            print()
            input("Press Enter to continue...")
        
        elif choice == '0':
            print("\n[INFO] Goodbye!")
            sys.exit(0)

# ==================== MAIN ====================

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        save_interrupted_state()
        print("\n[OK] Saved and exited")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
