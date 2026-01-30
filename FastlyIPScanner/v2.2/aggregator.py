#!/usr/bin/env python3
"""
Dr.CDN-Scanner - Result Aggregator
Version: 3.3
Developed by: DrConnect
Channel: https://t.me/drconnect

Description:
Aggregates scan results from submissions directory.
Groups by IP with port list and test type statistics.

Changes in v3.3:
- Added DNSTT test type support
- Updated TEST_TYPE_PRIORITY

Changes in v3.2:
- Support for UDP and DNS test types
- Protocol tracking (tcp/udp)
- Better is_official detection
"""

import json
import os
from collections import defaultdict
from datetime import datetime
import ipaddress

# Configuration
SUBMISSIONS_DIR = 'submissions'
AGGREGATED_FILE = 'aggregated/results.json'
ADMIN_FILE = 'aggregated/admin_results.json'
AUTO_CLEANUP = True

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

# Pre-compute networks
CDN_NETWORKS = {}
for cdn_name, ranges in CDN_RANGES.items():
    CDN_NETWORKS[cdn_name] = [ipaddress.ip_network(r) for r in ranges]

# Test type priority (higher = better)
TEST_TYPE_PRIORITY = {
    'port': 1, '1': 1, 1: 1,
    'tls': 2, '2': 2, 2: 2,
    'udp': 2, '5': 2, 5: 2,
    'dns': 2, '6': 2, 6: 2,
    'dnstt': 3, '7': 3, 7: 3,
    'real': 3, '3': 3, 3: 3,
    'download': 4, '4': 4, 4: 4
}

def normalize_test_type(test_type):
    """Normalize test type to string"""
    type_map = {1: 'port', 2: 'tls', 3: 'real', 4: 'download', 5: 'udp', 6: 'dns', 7: 'dnstt'}
    if isinstance(test_type, int):
        return type_map.get(test_type, 'port')
    if test_type in type_map:
        return type_map[test_type]
    return str(test_type).lower() if test_type else 'port'

def get_cdn_type(ip_str):
    """Detect which CDN the IP belongs to"""
    try:
        ip = ipaddress.ip_address(ip_str)
        for cdn_name, networks in CDN_NETWORKS.items():
            for network in networks:
                if ip in network:
                    return cdn_name
        return 'unknown'
    except:
        return 'unknown'

def is_official_cdn(ip_str):
    """Check if IP belongs to any known CDN"""
    return get_cdn_type(ip_str) != 'unknown'

def load_existing_aggregated():
    """Load existing aggregated data"""
    existing_public = None
    existing_admin = None
    
    if os.path.exists(AGGREGATED_FILE):
        try:
            with open(AGGREGATED_FILE, 'r') as f:
                existing_public = json.load(f)
        except:
            pass
    
    if os.path.exists(ADMIN_FILE):
        try:
            with open(ADMIN_FILE, 'r') as f:
                existing_admin = json.load(f)
        except:
            pass
    
    return existing_public, existing_admin

def load_all_submissions():
    """Load all submission files"""
    submissions = []
    
    if not os.path.exists(SUBMISSIONS_DIR):
        return submissions
    
    for filename in os.listdir(SUBMISSIONS_DIR):
        if filename.endswith('.json'):
            filepath = os.path.join(SUBMISSIONS_DIR, filename)
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    data['_filename'] = filepath
                    submissions.append(data)
            except Exception as e:
                print(f"[ERROR] Failed to load {filename}: {e}")
    
    return submissions

def aggregate_results(submissions):
    """Aggregate results - group by IP with test type tracking"""
    
    ip_stats = defaultdict(lambda: {
        'ports': {},
        'total_success': 0,
        'scanners': set(),
        'last_seen': None,
        'cdn': 'unknown',
        'is_official': False,
        'best_test_type': 'port',
        'best_delay': None,
        'best_speed': None,
        'protocol': 'tcp'
    })
    
    total_scans = len(submissions)
    all_scanners = set()
    port_totals = defaultdict(int)
    test_type_counts = defaultdict(int)
    cdn_counts = defaultdict(int)
    protocol_counts = defaultdict(int)
    
    for submission in submissions:
        scanner_ip = submission.get('public_ip', 'Unknown')
        all_scanners.add(scanner_ip)
        received_at = submission.get('received_at', datetime.now().isoformat() + 'Z')
        
        for result in submission.get('results', []):
            ip = result.get('ip')
            port = result.get('port')
            
            if not ip or not port:
                continue
            
            port = int(port)
            test_type = normalize_test_type(result.get('test_type', 'port'))
            cdn = result.get('cdn') or get_cdn_type(ip)
            delay = result.get('delay_ms') or result.get('latency_ms')
            speed = result.get('download_speed')
            protocol = result.get('protocol', 'tcp')
            
            # Update IP stats
            ip_stats[ip]['total_success'] += 1
            ip_stats[ip]['scanners'].add(scanner_ip)
            ip_stats[ip]['last_seen'] = received_at
            ip_stats[ip]['cdn'] = cdn
            ip_stats[ip]['is_official'] = is_official_cdn(ip)
            
            # Track protocol
            if test_type in ['udp', 'dns']:
                ip_stats[ip]['protocol'] = 'udp'
            
            # Track best test type
            current_priority = TEST_TYPE_PRIORITY.get(ip_stats[ip]['best_test_type'], 0)
            new_priority = TEST_TYPE_PRIORITY.get(test_type, 0)
            if new_priority > current_priority:
                ip_stats[ip]['best_test_type'] = test_type
            
            # Track best delay/speed
            if delay:
                try:
                    delay = float(delay)
                    if ip_stats[ip]['best_delay'] is None or delay < ip_stats[ip]['best_delay']:
                        ip_stats[ip]['best_delay'] = delay
                except:
                    pass
            
            if speed:
                try:
                    speed = float(speed)
                    if ip_stats[ip]['best_speed'] is None or speed > ip_stats[ip]['best_speed']:
                        ip_stats[ip]['best_speed'] = speed
                except:
                    pass
            
            # Update port stats
            if port not in ip_stats[ip]['ports']:
                ip_stats[ip]['ports'][port] = {
                    'count': 0,
                    'scanners': set(),
                    'test_types': set(),
                    'best_test_type': 'port',
                    'delay_ms': None,
                    'download_speed': None,
                    'protocol': 'tcp'
                }
            
            port_data = ip_stats[ip]['ports'][port]
            port_data['count'] += 1
            port_data['scanners'].add(scanner_ip)
            port_data['test_types'].add(test_type)
            
            if test_type in ['udp', 'dns']:
                port_data['protocol'] = 'udp'
            
            # Update best test type for port
            current_port_priority = TEST_TYPE_PRIORITY.get(port_data['best_test_type'], 0)
            if new_priority > current_port_priority:
                port_data['best_test_type'] = test_type
            
            if delay:
                try:
                    delay = float(delay)
                    if port_data['delay_ms'] is None or delay < port_data['delay_ms']:
                        port_data['delay_ms'] = delay
                except:
                    pass
            
            if speed:
                try:
                    speed = float(speed)
                    if port_data['download_speed'] is None or speed > port_data['download_speed']:
                        port_data['download_speed'] = speed
                except:
                    pass
            
            # Global counters
            port_totals[port] += 1
            test_type_counts[test_type] += 1
            cdn_counts[cdn] += 1
            protocol_counts[protocol] += 1
    
    # Convert to list format
    results = []
    for ip, stats in ip_stats.items():
        ports_list = []
        for port, port_data in stats['ports'].items():
            ports_list.append({
                'port': port,
                'count': port_data['count'],
                'scanners': list(port_data['scanners']),
                'test_types': list(port_data['test_types']),
                'best_test_type': port_data['best_test_type'],
                'delay_ms': port_data['delay_ms'],
                'download_speed': port_data['download_speed'],
                'protocol': port_data['protocol']
            })
        ports_list.sort(key=lambda x: x['count'], reverse=True)
        
        results.append({
            'ip': ip,
            'ports': ports_list,
            'port_numbers': sorted([p['port'] for p in ports_list]),
            'total_success': stats['total_success'],
            'scanner_count': len(stats['scanners']),
            'scanners': list(stats['scanners']),
            'last_seen': stats['last_seen'],
            'cdn': stats['cdn'],
            'is_official': stats['is_official'],
            'best_test_type': stats['best_test_type'],
            'best_delay': stats['best_delay'],
            'best_speed': stats['best_speed'],
            'protocol': stats['protocol']
        })
    
    results.sort(key=lambda x: x['total_success'], reverse=True)
    
    # Calculate port coverage
    total_ips = len(results)
    port_coverage = {}
    for port, count in port_totals.items():
        ips_with_port = sum(1 for r in results if port in r['port_numbers'])
        port_coverage[str(port)] = {
            'total_hits': count,
            'unique_ips': ips_with_port,
            'percentage': round((ips_with_port / total_ips * 100), 1) if total_ips > 0 else 0
        }
    
    metadata = {
        'generated': datetime.now().isoformat() + 'Z',
        'aggregator_version': '3.2',
        'total_scans': total_scans,
        'total_scanners': len(all_scanners),
        'working_ips': total_ips,
        'by_cdn': dict(cdn_counts),
        'by_test_type': dict(test_type_counts),
        'by_protocol': dict(protocol_counts),
        'official_ips': sum(1 for r in results if r['is_official']),
        'non_official_ips': sum(1 for r in results if not r['is_official']),
        'port_coverage': port_coverage
    }
    
    # Public output (simplified)
    public_results = []
    for r in results:
        public_results.append({
            'ip': r['ip'],
            'ports': r['port_numbers'],
            'total_success': r['total_success'],
            'scanner_count': r['scanner_count'],
            'last_seen': r['last_seen'],
            'cdn': r['cdn'],
            'is_official': r['is_official'],
            'best_test_type': r['best_test_type'],
            'best_delay': r['best_delay'],
            'best_speed': r['best_speed'],
            'protocol': r['protocol']
        })
    
    public_output = {'metadata': metadata, 'results': public_results}
    admin_output = {'metadata': metadata, 'results': results}
    
    return public_output, admin_output

def merge_with_existing(new_public, new_admin, existing_public, existing_admin):
    """Merge new results with existing data"""
    
    if not existing_admin or 'results' not in existing_admin:
        return new_public, new_admin
    
    # Handle old format conversion
    if 'ip_port_stats' in existing_admin:
        print("[INFO] Converting old format to new format...")
        return new_public, new_admin
    
    existing_ips = {r['ip']: r for r in existing_admin.get('results', [])}
    
    for new_result in new_admin.get('results', []):
        ip = new_result['ip']
        
        if ip in existing_ips:
            old = existing_ips[ip]
            
            # Merge scanners
            all_scanners = set(old.get('scanners', []) + new_result.get('scanners', []))
            
            # Merge ports
            old_ports = {p['port']: p for p in old.get('ports', [])}
            for new_port in new_result.get('ports', []):
                port_num = new_port['port']
                if port_num in old_ports:
                    old_ports[port_num]['count'] += new_port['count']
                    old_scanners = set(old_ports[port_num].get('scanners', []))
                    old_scanners.update(new_port.get('scanners', []))
                    old_ports[port_num]['scanners'] = list(old_scanners)
                    
                    # Merge test types
                    old_types = set(old_ports[port_num].get('test_types', []))
                    old_types.update(new_port.get('test_types', []))
                    old_ports[port_num]['test_types'] = list(old_types)
                    
                    # Update best values
                    old_priority = TEST_TYPE_PRIORITY.get(old_ports[port_num].get('best_test_type', 'port'), 0)
                    new_priority = TEST_TYPE_PRIORITY.get(new_port.get('best_test_type', 'port'), 0)
                    if new_priority > old_priority:
                        old_ports[port_num]['best_test_type'] = new_port['best_test_type']
                    
                    if new_port.get('delay_ms'):
                        if not old_ports[port_num].get('delay_ms') or new_port['delay_ms'] < old_ports[port_num]['delay_ms']:
                            old_ports[port_num]['delay_ms'] = new_port['delay_ms']
                    
                    if new_port.get('download_speed'):
                        if not old_ports[port_num].get('download_speed') or new_port['download_speed'] > old_ports[port_num]['download_speed']:
                            old_ports[port_num]['download_speed'] = new_port['download_speed']
                else:
                    old_ports[port_num] = new_port
            
            existing_ips[ip]['ports'] = list(old_ports.values())
            existing_ips[ip]['port_numbers'] = sorted(old_ports.keys())
            existing_ips[ip]['total_success'] = old.get('total_success', 0) + new_result.get('total_success', 0)
            existing_ips[ip]['scanners'] = list(all_scanners)
            existing_ips[ip]['scanner_count'] = len(all_scanners)
            existing_ips[ip]['last_seen'] = new_result['last_seen']
            
            # Update best test type
            old_priority = TEST_TYPE_PRIORITY.get(old.get('best_test_type', 'port'), 0)
            new_priority = TEST_TYPE_PRIORITY.get(new_result.get('best_test_type', 'port'), 0)
            if new_priority > old_priority:
                existing_ips[ip]['best_test_type'] = new_result['best_test_type']
            
            # Update best delay/speed
            if new_result.get('best_delay'):
                if not existing_ips[ip].get('best_delay') or new_result['best_delay'] < existing_ips[ip]['best_delay']:
                    existing_ips[ip]['best_delay'] = new_result['best_delay']
            if new_result.get('best_speed'):
                if not existing_ips[ip].get('best_speed') or new_result['best_speed'] > existing_ips[ip]['best_speed']:
                    existing_ips[ip]['best_speed'] = new_result['best_speed']
            
            # Ensure is_official is set correctly
            existing_ips[ip]['is_official'] = is_official_cdn(ip)
        else:
            existing_ips[ip] = new_result
    
    merged_results = list(existing_ips.values())
    merged_results.sort(key=lambda x: x['total_success'], reverse=True)
    
    # Recalculate metadata
    total_ips = len(merged_results)
    port_totals = defaultdict(lambda: {'ips': 0})
    all_scanners = set()
    test_type_counts = defaultdict(int)
    cdn_counts = defaultdict(int)
    protocol_counts = defaultdict(int)
    
    for r in merged_results:
        all_scanners.update(r.get('scanners', []))
        for port in r.get('port_numbers', []):
            port_totals[port]['ips'] += 1
        test_type_counts[r.get('best_test_type', 'port')] += 1
        cdn_counts[r.get('cdn', 'unknown')] += 1
        protocol_counts[r.get('protocol', 'tcp')] += 1
    
    port_coverage = {}
    for port, data in port_totals.items():
        port_coverage[str(port)] = {
            'unique_ips': data['ips'],
            'percentage': round((data['ips'] / total_ips * 100), 1) if total_ips > 0 else 0
        }
    
    metadata = {
        'generated': datetime.now().isoformat() + 'Z',
        'aggregator_version': '3.2',
        'total_scans': existing_public['metadata'].get('total_scans', 0) + new_public['metadata'].get('total_scans', 0),
        'total_scanners': len(all_scanners),
        'working_ips': total_ips,
        'by_cdn': dict(cdn_counts),
        'by_test_type': dict(test_type_counts),
        'by_protocol': dict(protocol_counts),
        'official_ips': sum(1 for r in merged_results if r.get('is_official', False)),
        'non_official_ips': sum(1 for r in merged_results if not r.get('is_official', False)),
        'port_coverage': port_coverage
    }
    
    # Public results
    public_results = []
    for r in merged_results:
        public_results.append({
            'ip': r['ip'],
            'ports': r.get('port_numbers', []),
            'total_success': r['total_success'],
            'scanner_count': r.get('scanner_count', len(r.get('scanners', []))),
            'last_seen': r['last_seen'],
            'cdn': r.get('cdn', 'unknown'),
            'is_official': r.get('is_official', is_official_cdn(r['ip'])),
            'best_test_type': r.get('best_test_type', 'port'),
            'best_delay': r.get('best_delay'),
            'best_speed': r.get('best_speed'),
            'protocol': r.get('protocol', 'tcp')
        })
    
    new_public['metadata'] = metadata
    new_public['results'] = public_results
    new_admin['metadata'] = metadata
    new_admin['results'] = merged_results
    
    return new_public, new_admin

def cleanup_submissions(submissions):
    """Delete processed submission files"""
    deleted = 0
    for submission in submissions:
        filepath = submission.get('_filename')
        if filepath and os.path.exists(filepath):
            try:
                os.remove(filepath)
                deleted += 1
            except:
                pass
    return deleted

def save_aggregated_results(public_data, admin_data):
    """Save aggregated results"""
    os.makedirs('aggregated', exist_ok=True)
    
    with open(AGGREGATED_FILE, 'w') as f:
        json.dump(public_data, f, indent=2)
    print(f"[OK] Public results: {AGGREGATED_FILE}")
    
    with open(ADMIN_FILE, 'w') as f:
        json.dump(admin_data, f, indent=2)
    print(f"[OK] Admin results: {ADMIN_FILE}")

def main():
    print("="*50)
    print("Dr.CDN-Scanner - Result Aggregator v3.2")
    print("="*50)
    
    print("\n[INFO] Loading existing data...")
    existing_public, existing_admin = load_existing_aggregated()
    if existing_public:
        print(f"[OK] Found existing: {existing_public['metadata'].get('working_ips', 0)} IPs")
    
    print("\n[INFO] Loading submissions...")
    submissions = load_all_submissions()
    print(f"[OK] Loaded {len(submissions)} submissions")
    
    if not submissions:
        print("[!] No new submissions")
        if not existing_public:
            empty_meta = {
                'generated': datetime.now().isoformat() + 'Z',
                'aggregator_version': '3.2',
                'total_scans': 0,
                'total_scanners': 0,
                'working_ips': 0,
                'by_cdn': {},
                'by_test_type': {},
                'by_protocol': {},
                'official_ips': 0,
                'non_official_ips': 0,
                'port_coverage': {}
            }
            save_aggregated_results(
                {'metadata': empty_meta, 'results': []},
                {'metadata': empty_meta, 'results': []}
            )
        return
    
    print("\n[INFO] Aggregating...")
    public_data, admin_data = aggregate_results(submissions)
    print(f"[OK] Found {public_data['metadata']['working_ips']} IPs")
    
    by_cdn = public_data['metadata'].get('by_cdn', {})
    for cdn, count in by_cdn.items():
        print(f"    - {cdn}: {count}")
    
    by_test = public_data['metadata'].get('by_test_type', {})
    if by_test:
        print(f"    Tests: {by_test}")
    
    print("\n[INFO] Merging...")
    public_data, admin_data = merge_with_existing(public_data, admin_data, existing_public, existing_admin)
    print(f"[OK] Total after merge: {public_data['metadata']['working_ips']}")
    
    print("\n[INFO] Saving...")
    save_aggregated_results(public_data, admin_data)
    
    if AUTO_CLEANUP:
        print("\n[INFO] Cleanup...")
        deleted = cleanup_submissions(submissions)
        print(f"[OK] Deleted {deleted} files")
    
    print("\n" + "="*50)
    print("Done!")
    print(f"Working IPs: {public_data['metadata']['working_ips']}")
    print(f"Official: {public_data['metadata']['official_ips']}")
    print(f"Total Scans: {public_data['metadata']['total_scans']}")
    print("="*50)

if __name__ == "__main__":
    main()
