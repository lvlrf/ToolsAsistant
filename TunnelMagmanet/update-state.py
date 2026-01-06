#!/usr/bin/env python3
"""
State Manager for Backhaul Bulk Generator
Allows viewing and updating state.json
"""

import json
import sys
from pathlib import Path
from datetime import datetime

class StateManager:
    """Manage state.json file"""
    
    def __init__(self, state_file="state.json"):
        self.state_file = Path(state_file)
        self.state = self.load_state()
    
    def load_state(self):
        """Load state from file"""
        if not self.state_file.exists():
            print(f"[ERROR] State file not found: {self.state_file}")
            print("Run generator.py first to create initial state.")
            sys.exit(1)
        
        with open(self.state_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def save_state(self):
        """Save state to file"""
        self.state["updated_at"] = datetime.now().isoformat()
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False)
        print(f"[OK] State saved to {self.state_file}")
    
    def show_summary(self):
        """Display state summary"""
        print()
        print("=" * 60)
        print("Backhaul State Summary")
        print("=" * 60)
        print()
        
        print(f"Last Tunnel Port:  {self.state['last_tunnel_port']}")
        print(f"Last Web Port:     {self.state['last_web_port']}")
        print(f"Last iperf Port:   {self.state['last_iperf_port']}")
        print(f"Last TUN Subnet:   10.10.{self.state['last_tun_subnet']}.0/24")
        print()
        
        print(f"Total Connections: {len(self.state['tokens'])}")
        print(f"Total Configs:     {len(self.state['generated_configs'])}")
        print()
        
        if "created_at" in self.state:
            print(f"Created:  {self.state['created_at']}")
        if "updated_at" in self.state:
            print(f"Updated:  {self.state['updated_at']}")
        
        print("=" * 60)
        print()
    
    def show_tokens(self):
        """Display all tokens"""
        print()
        print("=" * 60)
        print("Connection Tokens")
        print("=" * 60)
        print()
        
        if not self.state['tokens']:
            print("[INFO] No tokens generated yet")
        else:
            for connection, token in self.state['tokens'].items():
                print(f"{connection}: {token}")
        
        print()
    
    def show_configs(self, limit=20):
        """Display generated configs"""
        print()
        print("=" * 60)
        print(f"Generated Configurations (showing {min(limit, len(self.state['generated_configs']))}/{len(self.state['generated_configs'])})")
        print("=" * 60)
        print()
        
        configs = self.state['generated_configs'][:limit]
        
        for cfg in configs:
            transport = cfg['transport']
            if cfg.get('mux_version'):
                transport += f"-v{cfg['mux_version']}"
            transport += f"-{cfg['profile']}"
            
            print(f"Port {cfg['tunnel_port']}: {cfg['iran']} -> {cfg['kharej']} ({transport})")
            if cfg.get('subnet'):
                print(f"  Subnet: {cfg['subnet']}")
            print(f"  Web: {cfg['web_port']}, iperf: {cfg['iperf_port']}")
            print()
        
        if len(self.state['generated_configs']) > limit:
            print(f"... and {len(self.state['generated_configs']) - limit} more")
            print()
    
    def update_next_port(self, port_type, new_value):
        """Update next port value"""
        key = f"last_{port_type}_port"
        if key not in self.state:
            print(f"[ERROR] Unknown port type: {port_type}")
            print("Valid types: tunnel, web, iperf")
            return
        
        old_value = self.state[key]
        self.state[key] = new_value
        print(f"[OK] Updated {port_type} port: {old_value} -> {new_value}")
    
    def update_subnet(self, new_value):
        """Update TUN subnet counter"""
        old_value = self.state['last_tun_subnet']
        self.state['last_tun_subnet'] = new_value
        print(f"[OK] Updated TUN subnet: 10.10.{old_value}.0/24 -> 10.10.{new_value}.0/24")
    
    def reset_state(self):
        """Reset state to initial values"""
        print()
        print("[WARNING] This will reset all port counters and subnet counters!")
        print("[WARNING] Tokens and generated config list will be preserved.")
        print()
        confirm = input("Are you sure? (yes/no): ")
        
        if confirm.lower() != 'yes':
            print("Cancelled.")
            return
        
        # Load config to get initial values
        if not Path("config.json").exists():
            print("[ERROR] config.json not found")
            return
        
        with open("config.json", 'r') as f:
            config = json.load(f)
        
        settings = config.get("settings", {})
        
        self.state['last_tunnel_port'] = settings.get("tunnel_port_start", 100) - 1
        self.state['last_web_port'] = settings.get("web_port_start", 800) - 1
        self.state['last_iperf_port'] = settings.get("iperf_iran_port_start", 5001) - 1
        self.state['last_tun_subnet'] = 0
        
        print("[OK] State reset to initial values")
    
    def interactive_menu(self):
        """Interactive menu"""
        while True:
            print()
            print("=" * 60)
            print("Backhaul State Manager")
            print("=" * 60)
            print()
            print("1. Show summary")
            print("2. Show tokens")
            print("3. Show configurations")
            print("4. Update tunnel port")
            print("5. Update web port")
            print("6. Update iperf port")
            print("7. Update TUN subnet")
            print("8. Reset port counters")
            print("0. Exit")
            print()
            
            choice = input("Enter your choice: ").strip()
            
            if choice == '1':
                self.show_summary()
            elif choice == '2':
                self.show_tokens()
            elif choice == '3':
                limit = input("How many configs to show? (default 20): ").strip()
                limit = int(limit) if limit.isdigit() else 20
                self.show_configs(limit)
            elif choice == '4':
                new_value = input("Enter new tunnel port: ").strip()
                if new_value.isdigit():
                    self.update_next_port('tunnel', int(new_value))
                    self.save_state()
                else:
                    print("[ERROR] Invalid port number")
            elif choice == '5':
                new_value = input("Enter new web port: ").strip()
                if new_value.isdigit():
                    self.update_next_port('web', int(new_value))
                    self.save_state()
                else:
                    print("[ERROR] Invalid port number")
            elif choice == '6':
                new_value = input("Enter new iperf port: ").strip()
                if new_value.isdigit():
                    self.update_next_port('iperf', int(new_value))
                    self.save_state()
                else:
                    print("[ERROR] Invalid port number")
            elif choice == '7':
                new_value = input("Enter new subnet number (e.g., 80 for 10.10.80.0/24): ").strip()
                if new_value.isdigit():
                    self.update_subnet(int(new_value))
                    self.save_state()
                else:
                    print("[ERROR] Invalid subnet number")
            elif choice == '8':
                self.reset_state()
                self.save_state()
            elif choice == '0':
                print("Goodbye!")
                break
            else:
                print("[ERROR] Invalid choice")

def main():
    """Main entry point"""
    try:
        manager = StateManager()
        
        if len(sys.argv) > 1:
            command = sys.argv[1]
            
            if command == 'summary':
                manager.show_summary()
            elif command == 'tokens':
                manager.show_tokens()
            elif command == 'configs':
                limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
                manager.show_configs(limit)
            else:
                print(f"[ERROR] Unknown command: {command}")
                print()
                print("Usage:")
                print("  python3 update-state.py              # Interactive mode")
                print("  python3 update-state.py summary      # Show summary")
                print("  python3 update-state.py tokens       # Show tokens")
                print("  python3 update-state.py configs [N]  # Show N configs")
        else:
            manager.interactive_menu()
    
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
