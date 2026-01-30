#!/usr/bin/env python3
"""
Fastly CDN Scanner - Result Aggregator
Version: 1.0
Developed by: DrConnect
Channel: https://t.me/drconnect

Description:
Aggregates scan results from submissions directory and generates
statistics for the dashboard.
"""

import json
import os
from collections import defaultdict
from datetime import datetime

# Configuration
SUBMISSIONS_DIR = 'submissions'
AGGREGATED_FILE = 'aggregated/results.json'
ADMIN_FILE = 'aggregated/admin_results.json'

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
                    submissions.append(data)
            except Exception as e:
                print(f"[ERROR] Failed to load {filename}: {e}")
    
    return submissions

def aggregate_results(submissions):
    """Aggregate results from all submissions"""
    
    # Public aggregation (without user IPs)
    ip_port_stats = defaultdict(lambda: {
        'success_count': 0,
        'total_tests': 0,
        'success_rate': 0.0,
        'ports': set(),
        'last_seen': None
    })
    
    # Admin aggregation (with user IPs)
    admin_data = {
        'submissions': [],
        'ip_port_stats': {}
    }
    
    total_submissions = len(submissions)
    total_tests = 0
    
    for submission in submissions:
        total_tests += 1
        
        # Extract submission metadata
        submission_meta = {
            'public_ip': submission.get('public_ip', 'Unknown'),
            'timestamp': submission.get('timestamp', submission.get('received_at', 'Unknown')),
            'total_successful': submission.get('total_successful', 0),
            'scan_duration': submission.get('scan_duration', 0)
        }
        
        admin_data['submissions'].append(submission_meta)
        
        # Process results
        for result in submission.get('results', []):
            ip = result.get('ip')
            port = result.get('port')
            
            if not ip or not port:
                continue
            
            key = f"{ip}:{port}"
            
            # Update public stats
            ip_port_stats[key]['success_count'] += 1
            ip_port_stats[key]['total_tests'] += 1
            ip_port_stats[key]['ports'].add(port)
            ip_port_stats[key]['last_seen'] = submission.get('received_at', datetime.now().isoformat() + 'Z')
            
            # Update admin stats
            if key not in admin_data['ip_port_stats']:
                admin_data['ip_port_stats'][key] = {
                    'ip': ip,
                    'port': port,
                    'success_count': 0,
                    'tested_by': []
                }
            
            admin_data['ip_port_stats'][key]['success_count'] += 1
            
            # Add scanner IP only if unique
            scanner_ip = submission.get('public_ip', 'Unknown')
            if scanner_ip not in admin_data['ip_port_stats'][key]['tested_by']:
                admin_data['ip_port_stats'][key]['tested_by'].append(scanner_ip)
    
    # Calculate success rates and convert sets to lists
    public_results = []
    for key, stats in ip_port_stats.items():
        ip, port = key.split(':')
        stats['success_rate'] = (stats['success_count'] / stats['total_tests'] * 100) if stats['total_tests'] > 0 else 0
        stats['ports'] = list(stats['ports'])
        
        public_results.append({
            'ip': ip,
            'port': int(port),
            'success_count': stats['success_count'],
            'success_rate': round(stats['success_rate'], 2),
            'last_seen': stats['last_seen']
        })
    
    # Sort by success count (descending)
    public_results.sort(key=lambda x: x['success_count'], reverse=True)
    
    # Prepare public output
    public_output = {
        'metadata': {
            'generated': datetime.now().isoformat() + 'Z',
            'total_submissions': total_submissions,
            'total_tests': total_tests,
            'total_unique_ips': len(public_results)
        },
        'results': public_results
    }
    
    # Prepare admin output
    admin_output = {
        'metadata': {
            'generated': datetime.now().isoformat() + 'Z',
            'total_submissions': total_submissions,
            'total_tests': total_tests
        },
        'submissions': admin_data['submissions'],
        'ip_port_stats': admin_data['ip_port_stats']
    }
    
    return public_output, admin_output

def save_aggregated_results(public_data, admin_data):
    """Save aggregated results to files"""
    
    # Create aggregated directory
    os.makedirs('aggregated', exist_ok=True)
    
    # Save public results
    with open(AGGREGATED_FILE, 'w') as f:
        json.dump(public_data, f, indent=2)
    
    print(f"[OK] Public results saved: {AGGREGATED_FILE}")
    
    # Save admin results
    with open(ADMIN_FILE, 'w') as f:
        json.dump(admin_data, f, indent=2)
    
    print(f"[OK] Admin results saved: {ADMIN_FILE}")

def main():
    print("="*50)
    print("Fastly CDN Scanner - Result Aggregator")
    print("="*50)
    
    print("\n[INFO] Loading submissions...")
    submissions = load_all_submissions()
    print(f"[OK] Loaded {len(submissions)} submissions")
    
    if not submissions:
        print("[!] No submissions found")
        print("[INFO] Creating empty result files...")
        
        # Create empty results
        public_data = {
            'metadata': {
                'generated': datetime.now().isoformat() + 'Z',
                'total_submissions': 0,
                'total_tests': 0,
                'total_unique_ips': 0
            },
            'results': []
        }
        
        admin_data = {
            'metadata': {
                'generated': datetime.now().isoformat() + 'Z',
                'total_submissions': 0,
                'total_tests': 0
            },
            'submissions': [],
            'ip_port_stats': {}
        }
        
        save_aggregated_results(public_data, admin_data)
        print("\n[OK] Empty result files created")
        return
    
    print("\n[INFO] Aggregating results...")
    public_data, admin_data = aggregate_results(submissions)
    
    print(f"[OK] Found {public_data['metadata']['total_unique_ips']} unique IP:port combinations")
    
    print("\n[INFO] Saving aggregated results...")
    save_aggregated_results(public_data, admin_data)
    
    print("\n" + "="*50)
    print("Aggregation complete!")
    print("="*50)

if __name__ == "__main__":
    main()
