#!/usr/bin/env python3
"""
Dr.CDN-Scanner v2.1
Developed by: DrConnect
Telegram: @lvlRF | Channel: @drconnect
Phone: +98 912 741 9412

Description:
Advanced CDN IP Scanner with Xray integration for real connectivity testing.
Supports Cloudflare, Fastly, Gcore and other CDN providers.

Changes in v2.1:
- Added UDP port test
- Added DNS test (UDP 53)
- Reduced false positives with better verification
- Improved TLS handshake validation
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
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from threading import Lock
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
    print(f"  {pip_cmd} install requests tqdm")
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

VERSION = "2.1"
APP_NAME = "Dr.CDN-Scanner"

# Telemetry
TELEMETRY_SERVER = "http://194.36.174.102:8080"
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
    'retry_count': 3,
    'min_download_speed': 50,  # KB/s
    'min_upload_speed': 30,    # KB/s
    'port_mode': 'https',
    'cdn_mode': 'both',  # cloudflare, fastly, gcore, both, all
    'ip_mode': 'random',  # random, sequential
    'test_layers': [1, 2],  # 1=port, 2=tls, 3=real, 4=download, 5=udp, 6=dns
    'protocol': 'tcp',  # tcp, udp, both
    'auto_submit': True,
    'xray_path': '',
    'config_link': '',
    'test_url': 'https://www.google.com/generate_204',
    'dns_test_domain': 'google.com',
    'verify_response': True  # Enable response verification to reduce false positives
}

# Global State
settings = DEFAULT_SETTINGS.copy()
scan_interrupted = False
force_exit = False
ctrl_c_count = 0
results_lock = Lock()
submission_lock = Lock()

successful_ips = []
failed_ips = []
tested_count = 0
pending_results = []
last_submission_time = 0

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

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    global scan_interrupted, force_exit, ctrl_c_count
    
    ctrl_c_count += 1
    if ctrl_c_count >= 2:
        print("\n\n[!] Force exit")
        os._exit(1)
    
    scan_interrupted = True
    force_exit = True
    print("\n\n[!] Interrupted - Press Ctrl+C again to force exit")
    
    try:
        with submission_lock:
            if pending_results:
                print(f"[INFO] Submitting {len(pending_results)} pending results...")
                submit_telemetry(pending_results.copy(), get_public_ip(), 1)
                pending_results.clear()
    except:
        pass
    
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def get_public_ip():
    try:
        response = requests.get(f'{TELEMETRY_SERVER}/myip', timeout=3)
        if response.status_code == 200:
            return response.text.strip()
    except:
        pass
    return get_local_ip()

def print_header():
    clear_screen()
    print("╔════════════════════════════════════════════════════════╗")
    print(f"║           {APP_NAME} v{VERSION}                        ║")
    print("║           Developed by: DrConnect                      ║")
    print("║           Channel: https://t.me/drconnect              ║")
    print("╚════════════════════════════════════════════════════════╝")
    print()

def generate_token(timestamp):
    data = f"{timestamp}{SECRET_KEY}"
    return hashlib.sha256(data.encode()).hexdigest()

def get_server_timestamp():
    try:
        response = requests.get(f'{TELEMETRY_SERVER}/timestamp', timeout=3)
        if response.status_code == 200:
            return response.json().get('timestamp')
    except:
        pass
    return None

def submit_telemetry(results, public_ip, duration):
    """Submit results to server"""
    try:
        timestamp = get_server_timestamp()
        if not timestamp:
            return False
        
        payload = {
            'timestamp': timestamp,
            'token': generate_token(timestamp),
            'public_ip': public_ip,
            'scan_duration': duration,
            'scanner_version': VERSION,
            'total_successful': len(results),
            'results': results
        }
        
        response = requests.post(f'{TELEMETRY_SERVER}/submit', json=payload, timeout=5)
        return response.status_code == 200
    except:
        return False

# ==================== CDN & IP FUNCTIONS ====================

def is_official_cdn_ip(ip_str, cdn_type=None):
    """Check if IP belongs to official CDN ranges"""
    try:
        ip = ipaddress.ip_address(ip_str)
        
        ranges_to_check = []
        if cdn_type:
            ranges_to_check = CDN_RANGES.get(cdn_type, [])
        else:
            for ranges in CDN_RANGES.values():
                ranges_to_check.extend(ranges)
        
        for cidr in ranges_to_check:
            if ip in ipaddress.ip_network(cidr):
                return True
        return False
    except:
        return False

def get_cdn_type(ip_str):
    """Detect which CDN the IP belongs to"""
    try:
        ip = ipaddress.ip_address(ip_str)
        for cdn_name, ranges in CDN_RANGES.items():
            for cidr in ranges:
                if ip in ipaddress.ip_network(cidr):
                    return cdn_name
        return 'unknown'
    except:
        return 'unknown'

def expand_ip_ranges(ranges):
    """Expand CIDR to individual IPs"""
    all_ips = []
    for cidr in ranges:
        try:
            network = ipaddress.ip_network(cidr, strict=False)
            all_ips.extend([str(ip) for ip in network.hosts()])
        except:
            pass
    return all_ips

def load_ip_list_from_file(filename='ip_list.txt'):
    """Load custom IP list from file"""
    if not os.path.exists(filename):
        return None
    
    ranges = []
    try:
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                if '/' in line:
                    try:
                        ipaddress.ip_network(line, strict=False)
                        ranges.append(line)
                    except:
                        pass
                elif '-' in line:
                    try:
                        start_ip, end_ip = line.split('-')
                        start = ipaddress.ip_address(start_ip.strip())
                        end = ipaddress.ip_address(end_ip.strip())
                        for ip_int in range(int(start), int(end) + 1):
                            ranges.append(f"{ipaddress.ip_address(ip_int)}/32")
                    except:
                        pass
                else:
                    try:
                        ipaddress.ip_address(line)
                        ranges.append(f"{line}/32")
                    except:
                        pass
        
        return ranges if ranges else None
    except:
        return None

def get_ip_ranges():
    """Get IP ranges based on settings"""
    custom = load_ip_list_from_file('ip_list.txt')
    if custom:
        print("[INFO] Using custom IP list from: ip_list.txt")
        return custom
    
    ranges = []
    cdn_mode = settings.get('cdn_mode', 'both')
    
    if cdn_mode == 'cloudflare':
        ranges = CDN_RANGES['cloudflare']
    elif cdn_mode == 'fastly':
        ranges = CDN_RANGES['fastly']
    elif cdn_mode == 'gcore':
        ranges = CDN_RANGES['gcore']
    elif cdn_mode == 'both':
        ranges = CDN_RANGES['cloudflare'] + CDN_RANGES['fastly']
    elif cdn_mode == 'all':
        for r in CDN_RANGES.values():
            ranges.extend(r)
    
    print(f"[INFO] Using {cdn_mode.upper()} CDN ranges ({len(ranges)} subnets)")
    return ranges

# ==================== CONFIG PARSING ====================

def parse_vmess_link(link):
    """Parse vmess:// link"""
    try:
        encoded = link.replace('vmess://', '')
        decoded = base64.b64decode(encoded).decode('utf-8')
        config = json.loads(decoded)
        return {
            'protocol': 'vmess',
            'address': config.get('add', ''),
            'port': int(config.get('port', 443)),
            'uuid': config.get('id', ''),
            'aid': int(config.get('aid', 0)),
            'network': config.get('net', 'tcp'),
            'type': config.get('type', 'none'),
            'host': config.get('host', ''),
            'path': config.get('path', ''),
            'tls': config.get('tls', ''),
            'sni': config.get('sni', config.get('host', '')),
            'raw': config
        }
    except Exception as e:
        print(f"[ERROR] Failed to parse vmess: {e}")
        return None

def parse_vless_link(link):
    """Parse vless:// link"""
    try:
        link = link.replace('vless://', '')
        
        if '#' in link:
            link, name = link.rsplit('#', 1)
        else:
            name = ''
        
        if '?' in link:
            main, params_str = link.split('?', 1)
            params = dict(p.split('=') for p in params_str.split('&') if '=' in p)
        else:
            main = link
            params = {}
        
        uuid, rest = main.split('@', 1)
        address, port = rest.rsplit(':', 1)
        
        return {
            'protocol': 'vless',
            'address': address,
            'port': int(port),
            'uuid': uuid,
            'network': params.get('type', 'tcp'),
            'security': params.get('security', 'none'),
            'host': unquote(params.get('host', '')),
            'path': unquote(params.get('path', '')),
            'sni': unquote(params.get('sni', '')),
            'flow': params.get('flow', ''),
            'fp': params.get('fp', ''),
            'params': params
        }
    except Exception as e:
        print(f"[ERROR] Failed to parse vless: {e}")
        return None

def parse_trojan_link(link):
    """Parse trojan:// link"""
    try:
        link = link.replace('trojan://', '')
        
        if '#' in link:
            link, name = link.rsplit('#', 1)
        else:
            name = ''
        
        if '?' in link:
            main, params_str = link.split('?', 1)
            params = dict(p.split('=') for p in params_str.split('&') if '=' in p)
        else:
            main = link
            params = {}
        
        password, rest = main.split('@', 1)
        address, port = rest.rsplit(':', 1)
        
        return {
            'protocol': 'trojan',
            'address': address,
            'port': int(port),
            'password': password,
            'network': params.get('type', 'tcp'),
            'security': params.get('security', 'tls'),
            'host': unquote(params.get('host', '')),
            'path': unquote(params.get('path', '')),
            'sni': unquote(params.get('sni', '')),
            'params': params
        }
    except Exception as e:
        print(f"[ERROR] Failed to parse trojan: {e}")
        return None

def parse_config_link(link):
    """Parse any config link"""
    link = link.strip()
    
    if link.startswith('vmess://'):
        return parse_vmess_link(link)
    elif link.startswith('vless://'):
        return parse_vless_link(link)
    elif link.startswith('trojan://'):
        return parse_trojan_link(link)
    else:
        print("[ERROR] Unsupported protocol. Use vmess://, vless://, or trojan://")
        return None

def generate_xray_config(parsed_config, test_ip, test_port):
    """Generate Xray config JSON for testing"""
    
    protocol = parsed_config['protocol']
    sni = parsed_config.get('sni') or parsed_config.get('host') or parsed_config.get('address', '')
    host = parsed_config.get('host') or sni
    
    config = {
        "log": {"loglevel": "warning"},
        "inbounds": [{
            "port": 10808,
            "listen": "127.0.0.1",
            "protocol": "socks",
            "settings": {"udp": True}
        }],
        "outbounds": [{
            "protocol": protocol,
            "settings": {},
            "streamSettings": {}
        }]
    }
    
    outbound = config["outbounds"][0]
    
    if protocol == 'vmess':
        outbound["settings"] = {
            "vnext": [{
                "address": test_ip,
                "port": test_port,
                "users": [{
                    "id": parsed_config['uuid'],
                    "alterId": parsed_config.get('aid', 0),
                    "security": "auto"
                }]
            }]
        }
    
    elif protocol == 'vless':
        user = {
            "id": parsed_config['uuid'],
            "encryption": "none"
        }
        if parsed_config.get('flow'):
            user["flow"] = parsed_config['flow']
        
        outbound["settings"] = {
            "vnext": [{
                "address": test_ip,
                "port": test_port,
                "users": [user]
            }]
        }
    
    elif protocol == 'trojan':
        outbound["settings"] = {
            "servers": [{
                "address": test_ip,
                "port": test_port,
                "password": parsed_config['password']
            }]
        }
    
    network = parsed_config.get('network', 'tcp')
    stream = {"network": network}
    
    tls = parsed_config.get('tls') or parsed_config.get('security', '')
    if tls in ['tls', 'xtls']:
        stream["security"] = "tls"
        stream["tlsSettings"] = {
            "serverName": sni,
            "allowInsecure": True
        }
        if parsed_config.get('fp'):
            stream["tlsSettings"]["fingerprint"] = parsed_config['fp']
    
    if network == 'ws':
        stream["wsSettings"] = {
            "path": parsed_config.get('path', '/'),
            "headers": {"Host": host}
        }
    elif network == 'grpc':
        stream["grpcSettings"] = {
            "serviceName": parsed_config.get('path', '')
        }
    elif network == 'tcp' and parsed_config.get('type') == 'http':
        stream["tcpSettings"] = {
            "header": {
                "type": "http",
                "request": {
                    "path": [parsed_config.get('path', '/')],
                    "headers": {"Host": [host]}
                }
            }
        }
    
    outbound["streamSettings"] = stream
    
    return config

# ==================== TEST FUNCTIONS ====================

def test_tcp_port(ip, port, timeout=2):
    """Layer 1: TCP Port Check with response verification"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        
        start_time = time.time()
        result = sock.connect_ex((ip, port))
        latency = (time.time() - start_time) * 1000
        
        if result == 0:
            # Additional verification: try to get some response
            if settings.get('verify_response', True):
                try:
                    # Send a minimal request to verify it's not just accepting connections
                    sock.settimeout(1)
                    if port in HTTPS_PORTS:
                        # For HTTPS, just check connection is stable
                        sock.send(b'\x16\x03\x01\x00\x01')  # TLS Client Hello start
                    else:
                        # For HTTP, send minimal request
                        sock.send(b'HEAD / HTTP/1.0\r\n\r\n')
                    
                    # Try to receive something (even error is fine)
                    sock.settimeout(1)
                    try:
                        data = sock.recv(1)
                        if data:
                            sock.close()
                            return {'success': True, 'latency_ms': round(latency, 1), 'verified': True}
                    except socket.timeout:
                        # Timeout on receive is OK for some servers
                        pass
                except:
                    pass
            
            sock.close()
            return {'success': True, 'latency_ms': round(latency, 1), 'verified': False}
        
        sock.close()
        return {'success': False}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def test_udp_port(ip, port, timeout=2):
    """Layer 5: UDP Port Check"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)
        
        start_time = time.time()
        
        # Send a probe packet
        if port == 53:
            # DNS query for google.com
            probe = build_dns_query(settings.get('dns_test_domain', 'google.com'))
        else:
            # Generic UDP probe
            probe = b'\x00\x00\x00\x00'
        
        sock.sendto(probe, (ip, port))
        
        try:
            data, addr = sock.recvfrom(1024)
            latency = (time.time() - start_time) * 1000
            sock.close()
            
            if data:
                return {'success': True, 'latency_ms': round(latency, 1), 'response_size': len(data)}
            return {'success': False, 'error': 'Empty response'}
        except socket.timeout:
            sock.close()
            # UDP timeout doesn't necessarily mean port is closed
            # It could mean filtered or no response expected
            return {'success': False, 'error': 'Timeout (may be filtered)'}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def build_dns_query(domain):
    """Build a DNS query packet"""
    # Transaction ID
    transaction_id = random.randint(0, 65535)
    
    # Flags: Standard query
    flags = 0x0100
    
    # Questions: 1, Answers: 0, Authority: 0, Additional: 0
    header = struct.pack('>HHHHHH', transaction_id, flags, 1, 0, 0, 0)
    
    # Query section
    query = b''
    for part in domain.split('.'):
        query += bytes([len(part)]) + part.encode()
    query += b'\x00'  # End of domain name
    
    # Type A (1), Class IN (1)
    query += struct.pack('>HH', 1, 1)
    
    return header + query

def parse_dns_response(data):
    """Parse DNS response to verify it's valid"""
    try:
        if len(data) < 12:
            return False, "Too short"
        
        # Check response flags
        flags = struct.unpack('>H', data[2:4])[0]
        qr = (flags >> 15) & 1  # Query/Response flag
        rcode = flags & 0xF  # Response code
        
        if qr != 1:
            return False, "Not a response"
        
        if rcode != 0:
            return False, f"DNS error: {rcode}"
        
        # Get answer count
        ancount = struct.unpack('>H', data[6:8])[0]
        
        return True, f"Answers: {ancount}"
    except:
        return False, "Parse error"

def test_dns(ip, port=53, timeout=3, domain=None):
    """Layer 6: DNS Resolution Test"""
    if domain is None:
        domain = settings.get('dns_test_domain', 'google.com')
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)
        
        query = build_dns_query(domain)
        
        start_time = time.time()
        sock.sendto(query, (ip, port))
        
        data, addr = sock.recvfrom(1024)
        latency = (time.time() - start_time) * 1000
        
        sock.close()
        
        if data:
            valid, info = parse_dns_response(data)
            if valid:
                return {
                    'success': True,
                    'latency_ms': round(latency, 1),
                    'response_size': len(data),
                    'info': info
                }
            else:
                return {'success': False, 'error': info}
        
        return {'success': False, 'error': 'Empty response'}
    except socket.timeout:
        return {'success': False, 'error': 'Timeout'}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def test_tls_http(ip, port, timeout=3):
    """Layer 2: TLS Handshake or HTTP Check with better verification"""
    try:
        if port in HTTPS_PORTS:
            # TLS Handshake with full verification
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            
            start_time = time.time()
            
            with context.wrap_socket(sock, server_hostname=ip) as ssock:
                ssock.connect((ip, port))
                latency = (time.time() - start_time) * 1000
                
                # Get certificate info
                cert = ssock.getpeercert(binary_form=True)
                cipher = ssock.cipher()
                version = ssock.version()
                
                return {
                    'success': True,
                    'type': 'tls',
                    'latency_ms': round(latency, 1),
                    'has_cert': cert is not None,
                    'tls_version': version,
                    'cipher': cipher[0] if cipher else None
                }
        else:
            # HTTP Check with response verification
            start_time = time.time()
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((ip, port))
            
            # Send HTTP request
            request = f"HEAD / HTTP/1.1\r\nHost: {ip}\r\nConnection: close\r\n\r\n"
            sock.send(request.encode())
            
            # Receive response
            response = b''
            while True:
                try:
                    data = sock.recv(1024)
                    if not data:
                        break
                    response += data
                    if b'\r\n\r\n' in response:
                        break
                except socket.timeout:
                    break
            
            sock.close()
            latency = (time.time() - start_time) * 1000
            
            if response:
                # Parse status code
                try:
                    status_line = response.split(b'\r\n')[0].decode()
                    status_code = int(status_line.split()[1])
                except:
                    status_code = 0
                
                # Check for CDN headers
                response_str = response.decode(errors='ignore').lower()
                is_cdn = any(h in response_str for h in ['cloudflare', 'fastly', 'server: gcore'])
                
                return {
                    'success': status_code > 0 and status_code < 500,
                    'type': 'http',
                    'latency_ms': round(latency, 1),
                    'status_code': status_code,
                    'is_cdn': is_cdn
                }
            
            return {'success': False, 'error': 'No response'}
            
    except ssl.SSLError as e:
        return {'success': False, 'error': f'SSL: {str(e)[:50]}'}
    except socket.timeout:
        return {'success': False, 'error': 'Timeout'}
    except Exception as e:
        return {'success': False, 'error': str(e)[:50]}

def test_real_delay(ip, port, parsed_config, xray_path, timeout=5, retries=3):
    """Layer 3: Real Delay Test with Xray"""
    
    if not parsed_config or not xray_path:
        return {'success': False, 'error': 'No config or xray path'}
    
    if not os.path.exists(xray_path):
        return {'success': False, 'error': 'Xray not found'}
    
    xray_config = generate_xray_config(parsed_config, ip, port)
    
    # Use unique port to avoid conflicts
    local_port = 10808 + random.randint(0, 1000)
    xray_config['inbounds'][0]['port'] = local_port
    
    config_file = f'/tmp/xray_test_{ip}_{port}_{local_port}.json'
    
    process = None
    try:
        with open(config_file, 'w') as f:
            json.dump(xray_config, f)
        
        process = subprocess.Popen(
            [xray_path, 'run', '-c', config_file],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        time.sleep(1.5)  # Wait for Xray to start
        
        if process.poll() is not None:
            return {'success': False, 'error': 'Xray failed to start'}
        
        test_url = settings.get('test_url', TEST_URLS['real_delay'])
        proxies = {
            'http': f'socks5://127.0.0.1:{local_port}',
            'https': f'socks5://127.0.0.1:{local_port}'
        }
        
        delays = []
        for attempt in range(retries):
            try:
                start = time.time()
                response = requests.get(test_url, proxies=proxies, timeout=timeout, verify=False)
                delay = (time.time() - start) * 1000
                
                if response.status_code in [200, 204]:
                    delays.append(delay)
            except:
                pass
        
        if delays:
            avg_delay = sum(delays) / len(delays)
            return {
                'success': True,
                'type': 'real',
                'delay_ms': round(avg_delay, 1),
                'min_delay': round(min(delays), 1),
                'max_delay': round(max(delays), 1),
                'attempts': len(delays)
            }
        else:
            return {'success': False, 'error': 'All attempts failed'}
    
    except Exception as e:
        return {'success': False, 'error': str(e)}
    
    finally:
        try:
            os.remove(config_file)
        except:
            pass
        if process:
            try:
                process.terminate()
                process.wait(timeout=2)
            except:
                try:
                    process.kill()
                except:
                    pass

def test_download_speed(ip, port, parsed_config, xray_path, timeout=10):
    """Layer 4: Download Speed Test"""
    
    if not parsed_config or not xray_path:
        return {'success': False, 'error': 'No config or xray path'}
    
    xray_config = generate_xray_config(parsed_config, ip, port)
    local_port = 10808 + random.randint(0, 1000)
    xray_config['inbounds'][0]['port'] = local_port
    
    config_file = f'/tmp/xray_dl_{ip}_{port}_{local_port}.json'
    
    process = None
    try:
        with open(config_file, 'w') as f:
            json.dump(xray_config, f)
        
        process = subprocess.Popen(
            [xray_path, 'run', '-c', config_file],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        time.sleep(1.5)
        
        if process.poll() is not None:
            return {'success': False, 'error': 'Xray failed to start'}
        
        proxies = {
            'http': f'socks5://127.0.0.1:{local_port}',
            'https': f'socks5://127.0.0.1:{local_port}'
        }
        
        start = time.time()
        response = requests.get(TEST_URLS['download'], proxies=proxies, 
                               timeout=timeout, verify=False, stream=True)
        
        total_bytes = 0
        for chunk in response.iter_content(chunk_size=8192):
            total_bytes += len(chunk)
            if time.time() - start > timeout:
                break
        
        elapsed = time.time() - start
        speed_kbps = (total_bytes / 1024) / elapsed if elapsed > 0 else 0
        
        min_speed = settings.get('min_download_speed', 50)
        
        return {
            'success': speed_kbps >= min_speed,
            'type': 'download',
            'speed_kbps': round(speed_kbps, 1),
            'bytes': total_bytes,
            'time_s': round(elapsed, 2)
        }
    
    except Exception as e:
        return {'success': False, 'error': str(e)}
    
    finally:
        try:
            os.remove(config_file)
        except:
            pass
        if process:
            try:
                process.terminate()
                process.wait(timeout=2)
            except:
                try:
                    process.kill()
                except:
                    pass

# ==================== MAIN SCAN FUNCTION ====================

def scan_ip_port(ip, port, test_layers, parsed_config=None, xray_path=None):
    """Scan single IP:port with selected test layers"""
    global tested_count, scan_interrupted
    
    if scan_interrupted:
        return None
    
    result = {
        'ip': ip,
        'port': port,
        'cdn': get_cdn_type(ip),
        'is_official': is_official_cdn_ip(ip),
        'timestamp': datetime.now().isoformat(),
        'tests': {},
        'protocol': 'tcp'
    }
    
    # Layer 1: TCP Port Check
    if 1 in test_layers:
        port_result = test_tcp_port(ip, port, settings['timeout_port'])
        result['tests']['port'] = port_result
        result['latency_ms'] = port_result.get('latency_ms', 0)
        
        if not port_result.get('success'):
            result['success'] = False
            result['test_type'] = 'port'
            with results_lock:
                tested_count += 1
                failed_ips.append(result)
            return result
    
    # Layer 2: TLS/HTTP Check
    if 2 in test_layers:
        tls_result = test_tls_http(ip, port, settings['timeout_tls'])
        result['tests']['tls'] = tls_result
        if tls_result.get('latency_ms'):
            result['latency_ms'] = tls_result['latency_ms']
        
        if not tls_result.get('success'):
            result['success'] = False
            result['test_type'] = 'tls'
            with results_lock:
                tested_count += 1
                failed_ips.append(result)
            return result
    
    # Layer 3: Real Delay
    if 3 in test_layers and parsed_config and xray_path:
        real_result = test_real_delay(ip, port, parsed_config, xray_path,
                                      settings['timeout_real'], settings['retry_count'])
        result['tests']['real'] = real_result
        result['delay_ms'] = real_result.get('delay_ms', 0)
        
        if not real_result.get('success'):
            result['success'] = False
            result['test_type'] = 'real'
            with results_lock:
                tested_count += 1
                failed_ips.append(result)
            return result
    
    # Layer 4: Download Speed
    if 4 in test_layers and parsed_config and xray_path:
        dl_result = test_download_speed(ip, port, parsed_config, xray_path,
                                        settings['timeout_download'])
        result['tests']['download'] = dl_result
        result['download_speed'] = dl_result.get('speed_kbps', 0)
        
        if not dl_result.get('success'):
            result['success'] = False
            result['test_type'] = 'download'
            with results_lock:
                tested_count += 1
                failed_ips.append(result)
            return result
    
    # Layer 5: UDP Port (if selected)
    if 5 in test_layers:
        udp_result = test_udp_port(ip, port, settings['timeout_udp'])
        result['tests']['udp'] = udp_result
        result['protocol'] = 'udp'
        
        if not udp_result.get('success'):
            result['success'] = False
            result['test_type'] = 'udp'
            with results_lock:
                tested_count += 1
                failed_ips.append(result)
            return result
    
    # Layer 6: DNS (if selected and port is 53)
    if 6 in test_layers:
        dns_result = test_dns(ip, 53, settings['timeout_dns'])
        result['tests']['dns'] = dns_result
        result['protocol'] = 'udp'
        
        if not dns_result.get('success'):
            result['success'] = False
            result['test_type'] = 'dns'
            with results_lock:
                tested_count += 1
                failed_ips.append(result)
            return result
    
    # Determine final test type
    test_type_map = {1: 'port', 2: 'tls', 3: 'real', 4: 'download', 5: 'udp', 6: 'dns'}
    result['success'] = True
    result['test_type'] = test_type_map.get(max(test_layers), 'port')
    
    with results_lock:
        tested_count += 1
        successful_ips.append(result)
    
    with submission_lock:
        pending_results.append(result)
    
    return result

def auto_submit_worker(public_ip):
    """Background auto-submit thread"""
    global pending_results, last_submission_time, scan_interrupted
    
    last_submission_time = time.time()
    
    while not scan_interrupted:
        try:
            time.sleep(5)
            
            current_time = time.time()
            should_submit = False
            
            with submission_lock:
                if len(pending_results) >= AUTO_SUBMIT_BATCH:
                    should_submit = True
                elif len(pending_results) > 0 and (current_time - last_submission_time) >= AUTO_SUBMIT_INTERVAL:
                    should_submit = True
            
            if should_submit:
                with submission_lock:
                    results_to_send = pending_results.copy()
                    pending_results.clear()
                    last_submission_time = current_time
                
                if results_to_send:
                    duration = int(current_time - (last_submission_time - AUTO_SUBMIT_INTERVAL))
                    success = submit_telemetry(results_to_send, public_ip, duration)
                    
                    if success:
                        print(f"\n[OK] Auto-submitted {len(results_to_send)} results")
                    else:
                        with submission_lock:
                            pending_results.extend(results_to_send)
        except:
            pass

def perform_scan(ip_list, ports, test_layers, parsed_config=None, xray_path=None):
    """Main scan function"""
    global tested_count, scan_interrupted, successful_ips, failed_ips
    global pending_results, last_submission_time
    
    tested_count = 0
    scan_interrupted = False
    successful_ips = []
    failed_ips = []
    
    with submission_lock:
        pending_results.clear()
    
    if settings.get('auto_submit', True):
        public_ip = get_public_ip()
        submit_thread = threading.Thread(target=auto_submit_worker, args=(public_ip,), daemon=True)
        submit_thread.start()
        print(f"[INFO] Auto-submit: Every {AUTO_SUBMIT_BATCH} IPs or {AUTO_SUBMIT_INTERVAL}s")
    
    # For DNS test, only use port 53
    if 6 in test_layers:
        ports = [53]
    
    targets = [(ip, port) for ip in ip_list for port in ports]
    
    if settings.get('ip_mode') == 'random':
        random.shuffle(targets)
    
    total_targets = len(targets)
    threads = settings.get('threads') or get_cpu_count()
    
    print(f"\n[INFO] Total targets: {total_targets:,}")
    print(f"[INFO] Threads: {threads} | Test layers: {test_layers}")
    print(f"[INFO] Press Ctrl+C to stop and save results\n")
    
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=threads) as executor:
        if HAS_TQDM:
            with tqdm(total=total_targets, desc="Scanning", unit="target") as pbar:
                futures = {}
                
                batch_size = threads * 3
                for target in targets[:batch_size]:
                    ip, port = target
                    future = executor.submit(scan_ip_port, ip, port, test_layers,
                                            parsed_config, xray_path)
                    futures[future] = target
                
                remaining = targets[batch_size:]
                
                while futures and not scan_interrupted:
                    done, _ = wait(futures.keys(), timeout=5.0, return_when=FIRST_COMPLETED)
                    
                    for future in done:
                        futures.pop(future)
                        pbar.update(1)
                        
                        try:
                            result = future.result()
                            elapsed = time.time() - start_time
                            speed = tested_count / elapsed if elapsed > 0 else 0
                            pbar.set_postfix({
                                '✓': len(successful_ips),
                                '✗': len(failed_ips),
                                'Speed': f"{speed:.1f}/s"
                            })
                        except:
                            pass
                        
                        if remaining and not scan_interrupted:
                            next_target = remaining.pop(0)
                            ip, port = next_target
                            future = executor.submit(scan_ip_port, ip, port, test_layers,
                                                    parsed_config, xray_path)
                            futures[future] = next_target
        else:
            for i, (ip, port) in enumerate(targets):
                if scan_interrupted:
                    break
                
                scan_ip_port(ip, port, test_layers, parsed_config, xray_path)
                
                if (i + 1) % 50 == 0:
                    print(f"\r[Progress] {i+1}/{total_targets} | ✓ {len(successful_ips)} | ✗ {len(failed_ips)}", end='')
    
    return successful_ips

# ==================== RESULT SAVING ====================

def save_results(results, duration):
    """Save results to files"""
    if not results:
        print("[INFO] No successful results to save")
        return
    
    os.makedirs('results', exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # TXT format
    txt_file = f'results/scan_{timestamp}.txt'
    with open(txt_file, 'w') as f:
        f.write(f"# Dr.CDN-Scanner v{VERSION} Results\n")
        f.write(f"# Date: {datetime.now().isoformat()}\n")
        f.write(f"# Duration: {duration:.1f}s\n")
        f.write(f"# Total: {len(results)}\n\n")
        
        for r in results:
            f.write(f"{r['ip']}:{r['port']}\n")
    
    # JSON format
    json_file = f'results/scan_{timestamp}.json'
    with open(json_file, 'w') as f:
        json.dump({
            'metadata': {
                'scanner': APP_NAME,
                'version': VERSION,
                'date': datetime.now().isoformat(),
                'duration': duration,
                'total': len(results)
            },
            'results': results
        }, f, indent=2)
    
    # CSV format
    csv_file = f'results/scan_{timestamp}.csv'
    with open(csv_file, 'w') as f:
        f.write('IP,Port,Protocol,CDN,Is_Official,Test_Type,Latency_ms,Delay_ms,Download_Speed\n')
        for r in results:
            f.write(f"{r['ip']},{r['port']},{r.get('protocol','tcp')},{r.get('cdn','')},")
            f.write(f"{r.get('is_official','')},{r.get('test_type','')},")
            f.write(f"{r.get('latency_ms','')},{r.get('delay_ms','')},{r.get('download_speed','')}\n")
    
    print(f"\n[OK] Results saved:")
    print(f"     - {txt_file}")
    print(f"     - {json_file}")
    print(f"     - {csv_file}")

# ==================== STATE MANAGEMENT ====================

def save_state(targets, scanned):
    """Save scan state for resume"""
    os.makedirs('resume', exist_ok=True)
    state = {
        'timestamp': datetime.now().isoformat(),
        'settings': settings,
        'remaining_targets': targets,
        'successful_ips': successful_ips,
        'tested_count': tested_count
    }
    with open('resume/scan_state.json', 'w') as f:
        json.dump(state, f)

def load_state():
    """Load previous scan state"""
    if os.path.exists('resume/scan_state.json'):
        with open('resume/scan_state.json', 'r') as f:
            return json.load(f)
    return None

def delete_state():
    """Delete scan state"""
    try:
        os.remove('resume/scan_state.json')
    except:
        pass

# ==================== MENU SYSTEM ====================

def menu_select_layers():
    """Select test layers"""
    print_header()
    print("═══════════ SELECT TEST LAYERS ═══════════\n")
    print("Select tests to perform (comma-separated):\n")
    print("[1] TCP Port Check     (fastest, ~50ms/IP)")
    print("[2] TLS/HTTP Verify    (medium, ~200ms/IP)")
    print("[3] Real Delay (Xray)  (slow, ~2-5s/IP)")
    print("[4] Download Speed     (slowest, ~10s/IP)")
    print("[5] UDP Port Check     (fast, ~100ms/IP)")
    print("[6] DNS Test (UDP 53)  (fast, ~100ms/IP)\n")
    print("Examples: 1,2 | 1,2,3 | 5 | 6 | 1,2,3,4\n")
    
    choice = input("Your choice [default: 1,2]: ").strip()
    
    if not choice:
        return [1, 2]
    
    try:
        layers = [int(x.strip()) for x in choice.split(',')]
        layers = [l for l in layers if l in [1, 2, 3, 4, 5, 6]]
        return sorted(layers) if layers else [1, 2]
    except:
        return [1, 2]

def menu_settings():
    """Settings menu"""
    while True:
        print_header()
        print("═══════════ SETTINGS ═══════════\n")
        
        threads_display = settings['threads'] if settings['threads'] > 0 else f"Auto ({get_cpu_count()})"
        
        print(f"[1] Threads           : {threads_display}")
        print(f"[2] CDN Mode          : {settings['cdn_mode']}")
        print(f"[3] Port Mode         : {settings['port_mode']}")
        print(f"[4] IP Mode           : {settings['ip_mode']}")
        print(f"[5] TCP Timeouts      : Port={settings['timeout_port']}s TLS={settings['timeout_tls']}s Real={settings['timeout_real']}s")
        print(f"[6] UDP/DNS Timeouts  : UDP={settings['timeout_udp']}s DNS={settings['timeout_dns']}s")
        print(f"[7] Retry Count       : {settings['retry_count']}")
        print(f"[8] Min Download      : {settings['min_download_speed']} KB/s")
        print(f"[9] Auto Submit       : {'ON' if settings['auto_submit'] else 'OFF'}")
        print(f"[A] Xray Path         : {settings['xray_path'] or 'Not set'}")
        print(f"[B] Config Link       : {'Set' if settings['config_link'] else 'Not set'}")
        print(f"[C] Test URL          : {settings['test_url']}")
        print(f"[D] DNS Test Domain   : {settings['dns_test_domain']}")
        print(f"[E] Verify Response   : {'ON' if settings['verify_response'] else 'OFF'}")
        print(f"[0] Back\n")
        
        choice = input("Your choice: ").strip().upper()
        
        if choice == '1':
            try:
                t = input(f"Threads (0=auto, current={threads_display}): ").strip()
                if t:
                    settings['threads'] = max(0, min(100, int(t)))
            except:
                pass
        
        elif choice == '2':
            print("\n[1] Cloudflare  [2] Fastly  [3] Gcore  [4] Both (CF+Fastly)  [5] All")
            c = input("Choice: ").strip()
            modes = {'1': 'cloudflare', '2': 'fastly', '3': 'gcore', '4': 'both', '5': 'all'}
            settings['cdn_mode'] = modes.get(c, settings['cdn_mode'])
        
        elif choice == '3':
            print("\n[1] HTTPS Only  [2] HTTP Only  [3] All Ports  [4] DNS (53)  [5] Custom")
            c = input("Choice: ").strip()
            if c == '4':
                settings['port_mode'] = 'dns'
            elif c == '5':
                custom = input("Enter ports (comma-separated): ").strip()
                try:
                    PORTS['custom'] = [int(p.strip()) for p in custom.split(',')]
                    settings['port_mode'] = 'custom'
                except:
                    pass
            else:
                modes = {'1': 'https', '2': 'http', '3': 'all'}
                settings['port_mode'] = modes.get(c, settings['port_mode'])
        
        elif choice == '4':
            settings['ip_mode'] = 'sequential' if settings['ip_mode'] == 'random' else 'random'
        
        elif choice == '5':
            try:
                settings['timeout_port'] = int(input(f"Port timeout [{settings['timeout_port']}]: ").strip() or settings['timeout_port'])
                settings['timeout_tls'] = int(input(f"TLS timeout [{settings['timeout_tls']}]: ").strip() or settings['timeout_tls'])
                settings['timeout_real'] = int(input(f"Real delay timeout [{settings['timeout_real']}]: ").strip() or settings['timeout_real'])
            except:
                pass
        
        elif choice == '6':
            try:
                settings['timeout_udp'] = int(input(f"UDP timeout [{settings['timeout_udp']}]: ").strip() or settings['timeout_udp'])
                settings['timeout_dns'] = int(input(f"DNS timeout [{settings['timeout_dns']}]: ").strip() or settings['timeout_dns'])
            except:
                pass
        
        elif choice == '7':
            try:
                settings['retry_count'] = int(input(f"Retry count [{settings['retry_count']}]: ").strip() or settings['retry_count'])
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
    layers_names = {1: 'Port', 2: 'TLS/HTTP', 3: 'Real Delay', 4: 'Download', 5: 'UDP', 6: 'DNS'}
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
    
    print(f"  Auto Submit    : {'✓ ON' if settings['auto_submit'] else '✗ OFF'}")
    print()
    
    return input("[E] Edit  [S] Start  [B] Back: ").strip().upper()

def main_menu():
    """Main menu"""
    global start_time, force_exit
    
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
                    if 6 in test_layers:
                        ports = [53]
                    
                    start_time = time.time()
                    
                    results = perform_scan(ip_list, ports, test_layers, parsed_config, xray_path)
                    
                    if force_exit:
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
                print(f"[INFO] Remaining: {len(state.get('remaining_targets', [])):,} targets")
                print(f"[INFO] Already found: {len(state.get('successful_ips', []))} IPs")
                
                if input("\nResume? (y/n): ").strip().lower() == 'y':
                    settings.update(state['settings'])
                    successful_ips.extend(state['successful_ips'])
                    print("[INFO] Resuming scan...")
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
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        sys.exit(1)
