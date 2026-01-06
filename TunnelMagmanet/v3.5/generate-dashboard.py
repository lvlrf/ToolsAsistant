#!/usr/bin/env python3
"""
Generate standalone HTML dashboard with embedded state data
"""

import json
import sys
from pathlib import Path

def generate_dashboard():
    """Generate standalone dashboard.html"""
    
    # Load state.json
    state_file = Path("state.json")
    if not state_file.exists():
        print("[ERROR] state.json not found!")
        print("Please run generator.py first to create configurations.")
        sys.exit(1)
    
    with open(state_file, 'r', encoding='utf-8') as f:
        state_data = json.load(f)
    
    # Read dashboard template
    dashboard_template = Path("dashboard.html")
    if not dashboard_template.exists():
        print("[ERROR] dashboard.html template not found!")
        sys.exit(1)
    
    with open(dashboard_template, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Embed state data into HTML
    state_json = json.dumps(state_data, ensure_ascii=False, indent=2)
    
    # Replace the fetch call with embedded data
    embedded_html = html_content.replace(
        'async function loadState() {\n            try {\n                const response = await fetch(\'state.json\');\n                if (!response.ok) {\n                    throw new Error(\'state.json not found\');\n                }\n                stateData = await response.json();',
        f'async function loadState() {{\n            try {{\n                // Embedded state data\n                stateData = {state_json};'
    )
    
    # Write standalone dashboard
    output_file = Path("dashboard-standalone.html")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(embedded_html)
    
    print()
    print("=" * 60)
    print("✅ Dashboard Generated Successfully!")
    print("=" * 60)
    print()
    print(f"📊 File: {output_file.absolute()}")
    print(f"📈 Total Configs: {len(state_data.get('generated_configs', []))}")
    print()
    print("🌐 Usage:")
    print("   1. باز کردن در مرورگر:")
    print(f"      - دابل کلیک روی: {output_file.name}")
    print("   2. یا copy کردن به سرور و باز کردن با:")
    print("      - python3 -m http.server 8000")
    print("      - سپس: http://localhost:8000/dashboard-standalone.html")
    print()
    print("=" * 60)

if __name__ == "__main__":
    try:
        generate_dashboard()
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
