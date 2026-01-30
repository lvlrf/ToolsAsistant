#!/usr/bin/env python3
"""
Fastly CDN Scanner - Result Aggregator
Version: 3.0
Developed by: DrConnect
Channel: https://t.me/drconnect

Description:
Aggregates scan results from submissions directory and generates
statistics for the dashboard. Groups by IP with port list.

Changes in v3.0:
- Group by IP (not IP:Port)
- Each IP has list of working ports
- Fastly vs non-Fastly detection
- Port coverage statistics
- Auto-cleanup submissions
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

# Official Fastly IP ranges
FASTLY_RANGES = [
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

# Pre-compute Fastly networks for faster lookup
FASTLY_NETWORKS = [ipaddress.ip_network(r) for r in FASTLY_RANGES]

def is_fastly_ip(ip_str):
    """Check if IP belongs to Fastly ranges"""
    try:
        ip = ipaddress.ip_address(ip_str)
        for network in FASTLY_NETWORKS:
            if ip in network:
                return True
        return False
    except:
        return False

def load_existing_aggregated():
    """Load existing aggregated data to preserve historical data"""
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
    """Load all submission files and return with filenames"""
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
    """Aggregate results - group by IP with port list"""
    
    # Group by IP
    ip_stats = defaultdict(lambda: {
        'ports': {},
        'total_success': 0,
        'scanners': set(),
        'last_seen': None,
        'is_fastly': True
    })
    
    total_scans = len(submissions)
    all_scanners = set()
    port_totals = defaultdict(int)
    
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
            
            # Update IP stats
            ip_stats[ip]['total_success'] += 1
            ip_stats[ip]['scanners'].add(scanner_ip)
            ip_stats[ip]['last_seen'] = received_at
            ip_stats[ip]['is_fastly'] = is_fastly_ip(ip)
            
            # Update port stats for this IP
            if port not in ip_stats[ip]['ports']:
                ip_stats[ip]['ports'][port] = {
                    'count': 0,
                    'scanners': set()
                }
            ip_stats[ip]['ports'][port]['count'] += 1
            ip_stats[ip]['ports'][port]['scanners'].add(scanner_ip)
            
            # Global port counter
            port_totals[port] += 1
    
    # Convert to list format
    results = []
    for ip, stats in ip_stats.items():
        ports_list = []
        for port, port_data in stats['ports'].items():
            ports_list.append({
                'port': port,
                'count': port_data['count'],
                'scanners': list(port_data['scanners'])
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
            'is_fastly': stats['is_fastly']
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
        'total_scans': total_scans,
        'total_scanners': len(all_scanners),
        'working_ips': total_ips,
        'fastly_ips': sum(1 for r in results if r['is_fastly']),
        'non_fastly_ips': sum(1 for r in results if not r['is_fastly']),
        'port_coverage': port_coverage
    }
    
    # Public output
    public_results = []
    for r in results:
        public_results.append({
            'ip': r['ip'],
            'ports': r['port_numbers'],
            'total_success': r['total_success'],
            'scanner_count': r['scanner_count'],
            'last_seen': r['last_seen'],
            'is_fastly': r['is_fastly']
        })
    
    public_output = {'metadata': metadata, 'results': public_results}
    admin_output = {'metadata': metadata, 'results': results}
    
    return public_output, admin_output

def merge_with_existing(new_public, new_admin, existing_public, existing_admin):
    """Merge new results with existing aggregated data"""
    
    if not existing_public or not existing_admin:
        return new_public, new_admin
    
    # Check old format
    if 'ip_port_stats' in existing_admin:
        print("[INFO] Converting old format to new format...")
        return new_public, new_admin
    
    existing_ips = {r['ip']: r for r in existing_admin.get('results', [])}
    
    for new_result in new_admin.get('results', []):
        ip = new_result['ip']
        
        if ip in existing_ips:
            old = existing_ips[ip]
            
            all_scanners = set(old.get('scanners', []) + new_result.get('scanners', []))
            
            old_ports = {p['port']: p for p in old.get('ports', [])}
            for new_port in new_result.get('ports', []):
                port_num = new_port['port']
                if port_num in old_ports:
                    old_ports[port_num]['count'] += new_port['count']
                    old_scanners = set(old_ports[port_num].get('scanners', []))
                    old_scanners.update(new_port.get('scanners', []))
                    old_ports[port_num]['scanners'] = list(old_scanners)
                else:
                    old_ports[port_num] = new_port
            
            existing_ips[ip]['ports'] = list(old_ports.values())
            existing_ips[ip]['port_numbers'] = sorted(old_ports.keys())
            existing_ips[ip]['total_success'] = old.get('total_success', 0) + new_result.get('total_success', 0)
            existing_ips[ip]['scanners'] = list(all_scanners)
            existing_ips[ip]['scanner_count'] = len(all_scanners)
            existing_ips[ip]['last_seen'] = new_result['last_seen']
        else:
            existing_ips[ip] = new_result
    
    merged_results = list(existing_ips.values())
    merged_results.sort(key=lambda x: x['total_success'], reverse=True)
    
    # Recalculate metadata
    total_ips = len(merged_results)
    port_totals = defaultdict(lambda: {'ips': 0})
    all_scanners = set()
    
    for r in merged_results:
        all_scanners.update(r.get('scanners', []))
        for port in r.get('port_numbers', []):
            port_totals[port]['ips'] += 1
    
    port_coverage = {}
    for port, data in port_totals.items():
        port_coverage[str(port)] = {
            'unique_ips': data['ips'],
            'percentage': round((data['ips'] / total_ips * 100), 1) if total_ips > 0 else 0
        }
    
    metadata = {
        'generated': datetime.now().isoformat() + 'Z',
        'total_scans': existing_public['metadata'].get('total_scans', 0) + new_public['metadata'].get('total_scans', 0),
        'total_scanners': len(all_scanners),
        'working_ips': total_ips,
        'fastly_ips': sum(1 for r in merged_results if r.get('is_fastly', True)),
        'non_fastly_ips': sum(1 for r in merged_results if not r.get('is_fastly', True)),
        'port_coverage': port_coverage
    }
    
    public_results = []
    for r in merged_results:
        public_results.append({
            'ip': r['ip'],
            'ports': r.get('port_numbers', []),
            'total_success': r['total_success'],
            'scanner_count': r.get('scanner_count', len(r.get('scanners', []))),
            'last_seen': r['last_seen'],
            'is_fastly': r.get('is_fastly', True)
        })
    
    new_public['metadata'] = metadata
    new_public['results'] = public_results
    new_admin['metadata'] = metadata
    new_admin['results'] = merged_results
    
    return new_public, new_admin

def cleanup_submissions(submissions):
    """Delete processed submission files"""
    deleted_count = 0
    for submission in submissions:
        filepath = submission.get('_filename')
        if filepath and os.path.exists(filepath):
            try:
                os.remove(filepath)
                deleted_count += 1
            except Exception as e:
                print(f"[WARNING] Failed to delete {filepath}: {e}")
    return deleted_count

def save_aggregated_results(public_data, admin_data):
    """Save aggregated results to files"""
    os.makedirs('aggregated', exist_ok=True)
    
    with open(AGGREGATED_FILE, 'w') as f:
        json.dump(public_data, f, indent=2)
    print(f"[OK] Public results saved: {AGGREGATED_FILE}")
    
    with open(ADMIN_FILE, 'w') as f:
        json.dump(admin_data, f, indent=2)
    print(f"[OK] Admin results saved: {ADMIN_FILE}")

def main():
    print("="*50)
    print("Fastly CDN Scanner - Result Aggregator v3.0")
    print("="*50)
    
    print("\n[INFO] Loading existing aggregated data...")
    existing_public, existing_admin = load_existing_aggregated()
    if existing_public:
        print(f"[OK] Found existing data: {existing_public['metadata'].get('working_ips', 0)} IPs")
    
    print("\n[INFO] Loading new submissions...")
    submissions = load_all_submissions()
    print(f"[OK] Loaded {len(submissions)} new submissions")
    
    if not submissions:
        print("[!] No new submissions found")
        if existing_public:
            print(f"[INFO] Existing data unchanged")
        else:
            empty_metadata = {
                'generated': datetime.now().isoformat() + 'Z',
                'total_scans': 0,
                'total_scanners': 0,
                'working_ips': 0,
                'fastly_ips': 0,
                'non_fastly_ips': 0,
                'port_coverage': {}
            }
            save_aggregated_results(
                {'metadata': empty_metadata, 'results': []},
                {'metadata': empty_metadata, 'results': []}
            )
        return
    
    print("\n[INFO] Aggregating results...")
    public_data, admin_data = aggregate_results(submissions)
    print(f"[OK] Found {public_data['metadata']['working_ips']} unique IPs")
    print(f"    - Fastly: {public_data['metadata']['fastly_ips']}")
    print(f"    - Non-Fastly: {public_data['metadata']['non_fastly_ips']}")
    
    print("\n[INFO] Merging with existing data...")
    public_data, admin_data = merge_with_existing(public_data, admin_data, existing_public, existing_admin)
    print(f"[OK] Total IPs after merge: {public_data['metadata']['working_ips']}")
    
    print("\n[INFO] Saving results...")
    save_aggregated_results(public_data, admin_data)
    
    if AUTO_CLEANUP:
        print("\n[INFO] Cleaning up submissions...")
        deleted = cleanup_submissions(submissions)
        print(f"[OK] Deleted {deleted} processed files")
    
    print("\n" + "="*50)
    print("Aggregation complete!")
    print(f"Working IPs: {public_data['metadata']['working_ips']}")
    print(f"Total Scans: {public_data['metadata']['total_scans']}")
    print("="*50)

if __name__ == "__main__":
    main()
