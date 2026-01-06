#!/usr/bin/env python3
"""
Backhaul Premium Bulk Config Generator - Interactive Version
Generates configurations for all transport types with multiple profiles
"""

import json
import os
import secrets
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

class BackhaulBulkGenerator:
    """Generator for Backhaul Premium configurations"""
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.config = self.load_config()
        self.state = self.load_state()
        self.output_dir = Path("output")
        
        # Binary configuration
        binary_config = self.config.get("binary_config", {}).get("premium", {})
        self.binary_path = binary_config.get("path", "/root/backhaul-core")
        self.binary_filename = binary_config.get("filename", "backhaul_premium")
        self.binary_full_path = f"{self.binary_path}/{self.binary_filename}"
        
        # Transport definitions
        self.transports = {
            "tcp": {"mux": False, "tun": False, "ws": False, "accepts_udp": True},
            "tcpmux": {"mux": True, "tun": False, "ws": False, "accepts_udp": False},
            "utcpmux": {"mux": True, "tun": False, "ws": False, "accepts_udp": False},
            "xtcpmux": {"mux": True, "tun": False, "ws": False, "accepts_udp": False},
            "ws": {"mux": False, "tun": False, "ws": True, "accepts_udp": False},
            "wsmux": {"mux": True, "tun": False, "ws": True, "accepts_udp": False},
            "uwsmux": {"mux": True, "tun": False, "ws": True, "accepts_udp": False},
            "xwsmux": {"mux": True, "tun": False, "ws": True, "accepts_udp": False},
            "udp": {"mux": False, "tun": False, "ws": False, "accepts_udp": False},
            "tcptun": {"mux": False, "tun": True, "ws": False, "accepts_udp": False},
            "faketcptun": {"mux": False, "tun": True, "ws": False, "accepts_udp": False},
            "wstun": {"mux": False, "tun": True, "ws": True, "accepts_udp": False},
            "udptun": {"mux": False, "tun": True, "ws": False, "accepts_udp": False},
        }
        
        # Profile definitions
        self.profiles = {
            "speed": {
                "channel_size": 4096,
                "heartbeat": 20,
                "mux_con": 128,
                "connection_pool": 16,
                "aggressive_pool": True,
                "mtu": 1400
            },
            "stable": {
                "channel_size": 2048,
                "heartbeat": 40,
                "mux_con": 64,
                "connection_pool": 8,
                "aggressive_pool": False,
                "mtu": 1400
            },
            "balanced": {
                "channel_size": 2048,
                "heartbeat": 20,
                "mux_con": 64,
                "connection_pool": 8,
                "aggressive_pool": False,
                "mtu": 1400
            }
        }
    
    def load_config(self) -> dict:
        """Load configuration from JSON file"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"[ERROR] Config file not found: {self.config_path}")
            exit(1)
        except json.JSONDecodeError as e:
            print(f"[ERROR] Invalid JSON in config file: {e}")
            exit(1)
    
    def load_state(self) -> dict:
        """Load or initialize state"""
        state_file = Path("state.json")
        if state_file.exists():
            with open(state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        settings = self.config.get("settings", {})
        return {
            "last_tunnel_port": settings.get("tunnel_port_start", 100) - 1,
            "last_web_port": settings.get("web_port_start", 800) - 1,
            "last_iperf_port": settings.get("iperf_iran_port_start", 5001) - 1,
            "last_tun_subnet": 0,
            "tokens": {},
            "generated_configs": [],
            "created_at": datetime.now().isoformat()
        }
    
    def save_state(self):
        """Save current state to file"""
        self.state["updated_at"] = datetime.now().isoformat()
        with open("state.json", 'w', encoding='utf-8') as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False)
    
    def view_state(self):
        """Display current state"""
        print()
        print("=" * 60)
        print("Current State Information")
        print("=" * 60)
        print()
        
        if not Path("state.json").exists():
            print("[INFO] No state file found. Run generator first.")
            return
        
        print(f"Last Tunnel Port:  {self.state['last_tunnel_port']}")
        print(f"Last Web Port:     {self.state['last_web_port']}")
        print(f"Last iperf Port:   {self.state['last_iperf_port']}")
        print(f"Last TUN Subnet:   10.10.{self.state['last_tun_subnet']}.0/24")
        print()
        print(f"Total Connections: {len(self.state['tokens'])}")
        print(f"Total Configs:     {len(self.state['generated_configs'])}")
        print()
        
        if self.state.get('tokens'):
            print("Tokens:")
            for conn, token in self.state['tokens'].items():
                print(f"  {conn}: {token}")
            print()
    
    def generate_token(self) -> str:
        """Generate a random 32-character hex token"""
        return secrets.token_hex(16)
    
    def get_or_create_token(self, iran_name: str, kharej_name: str) -> str:
        """Get existing token or create new one for a connection"""
        key = f"{iran_name}-{kharej_name}"
        if key not in self.state["tokens"]:
            self.state["tokens"][key] = self.generate_token()
        return self.state["tokens"][key]
    
    def get_next_port(self, port_type: str) -> int:
        """Get next available port"""
        excluded = self.config.get("settings", {}).get("excluded_ports", [])
        
        while True:
            self.state[f"last_{port_type}_port"] += 1
            port = self.state[f"last_{port_type}_port"]
            if port not in excluded:
                return port
    
    def get_next_subnet(self) -> str:
        """Get next TUN subnet"""
        self.state["last_tun_subnet"] += 10
        subnet_num = self.state["last_tun_subnet"]
        return f"10.10.{subnet_num}.0/24"
    
    def generate_server_config(self, iran: dict, kharej: dict, transport: str, 
                               profile: str, mux_version: Optional[int], ports: dict,
                               subnet: Optional[str], token: str) -> str:
        """Generate Iran server configuration"""
        
        iran_name = iran["name"]
        iran_ip = iran["ip"]
        tunnel_port = ports["tunnel"]
        web_port = ports["web"]
        
        transport_info = self.transports[transport]
        profile_settings = self.profiles[profile]
        
        # Base config
        config = f"""[server]
bind_addr = "0.0.0.0:{tunnel_port}"
bind_addrs = []
transport = "{transport}"
"""
        
        # Accept UDP (only for tcp)
        if transport == "tcp":
            config += f"accept_udp = true\n"
        
        config += f"""token = "{token}"
keepalive_period = 20
"""
        
        # Nodelay (not for udp, faketcptun, udptun)
        if transport not in ["udp", "faketcptun", "udptun"]:
            config += "nodelay = true\n"
        else:
            config += "nodelay = false\n"
        
        # Channel size and heartbeat (not for TUN transports)
        if not transport_info["tun"]:
            config += f"""channel_size = {profile_settings['channel_size']}
heartbeat = {profile_settings['heartbeat']}
"""
        
        # Mux settings
        if transport_info["mux"]:
            config += f"""mux_con = {profile_settings['mux_con']}
mux_version = {mux_version}
mux_framesize = 32768
mux_recievebuffer = 4194304
mux_streambuffer = 2000000
"""
        
        # Sniffer and web port
        log_dir = f"iran{tunnel_port}-{transport}"
        if transport_info["mux"]:
            log_dir += f"-v{mux_version}"
        log_dir += f"-{profile}"
        
        config += f"""sniffer = true
web_port = {web_port}
sniffer_log = "{self.binary_path}/{log_dir}/log.json"
log_level = "info"
"""
        
        # Proxy protocol (not for ws, udp, TUN)
        if not (transport_info["ws"] or transport == "udp" or transport_info["tun"]):
            config += "proxy_protocol = false\n"
        
        # TUN settings
        if transport_info["tun"]:
            tun_name = f"iran{tunnel_port}-{transport}"
            if transport_info["mux"]:
                tun_name += f"-v{mux_version}"
            tun_name += f"-{profile}"
            
            config += f"""tun_name = "{tun_name}"
tun_subnet = "{subnet}"
mtu = {profile_settings['mtu']}
"""
        
        # Advanced options
        config += """skip_optz = false
so_rcvbuf = 0
so_sndbuf = 0
mss = 0

"""
        
        # Ports for iperf3
        iperf_port = ports["iperf"]
        iperf_kharej_port = self.config.get("settings", {}).get("iperf_kharej_port", 5201)
        
        if not transport_info["tun"]:
            config += f"""ports = [
    "{iperf_port}=127.0.0.1:{iperf_kharej_port}"
]
"""
        else:
            config += "ports = []\n"
        
        return config
    
    def generate_client_config(self, iran: dict, kharej: dict, transport: str,
                               profile: str, mux_version: Optional[int], ports: dict,
                               subnet: Optional[str], token: str) -> str:
        """Generate Kharej client configuration"""
        
        iran_ip = iran["ip"]
        tunnel_port = ports["tunnel"]
        web_port = ports["web"]
        
        transport_info = self.transports[transport]
        profile_settings = self.profiles[profile]
        
        # Base config
        config = f"""[client]
remote_addr = "{iran_ip}:{tunnel_port}"
transport = "{transport}"
token = "{token}"
"""
        
        # Edge IP for WebSocket (commented)
        if transport_info["ws"]:
            config += '#edge_ip = "188.114.96.0"\n'
        
        # Nodelay
        if transport not in ["udp", "faketcptun", "udptun"]:
            config += "nodelay = true\n"
        else:
            config += "nodelay = false\n"
        
        # Connection pool (not for TUN)
        if not transport_info["tun"]:
            config += f"""connection_pool = {profile_settings['connection_pool']}
"""
            # Aggressive pool (only for tcp/tcpmux)
            if transport in ["tcp", "tcpmux"]:
                aggressive = "true" if profile_settings["aggressive_pool"] else "false"
                config += f"aggressive_pool = {aggressive}\n"
        
        config += """retry_interval = 3
dial_timeout = 10
"""
        
        # Mux settings
        if transport_info["mux"]:
            config += f"""mux_con = {profile_settings['mux_con']}
mux_version = {mux_version}
mux_framesize = 32768
mux_recievebuffer = 4194304
mux_streambuffer = 2000000
"""
        
        # Sniffer and web port
        log_dir = f"kharej{tunnel_port}-{transport}"
        if transport_info["mux"]:
            log_dir += f"-v{mux_version}"
        log_dir += f"-{profile}"
        
        config += f"""sniffer = true
web_port = {web_port}
sniffer_log = "{self.binary_path}/{log_dir}/log.json"
log_level = "info"
"""
        
        # TUN settings (must match server)
        if transport_info["tun"]:
            tun_name = f"kharej{tunnel_port}-{transport}"
            if transport_info["mux"]:
                tun_name += f"-v{mux_version}"
            tun_name += f"-{profile}"
            
            config += f"""tun_name = "{tun_name}"
tun_subnet = "{subnet}"
mtu = {profile_settings['mtu']}
"""
        
        # Advanced options
        config += """skip_optz = false
so_rcvbuf = 0
so_sndbuf = 0
mss = 0

"""
        
        # Ports for iperf3
        iperf_port = ports["iperf"]
        iperf_kharej_port = self.config.get("settings", {}).get("iperf_kharej_port", 5201)
        
        if not transport_info["tun"]:
            config += f"""ports = [
    "{iperf_port}=127.0.0.1:{iperf_kharej_port}"
]
"""
        else:
            config += "ports = []\n"
        
        return config
    
    def generate_all_configs(self):
        """Main function to generate all configurations"""
        
        print("=" * 60)
        print("Backhaul Premium Bulk Config Generator")
        print("=" * 60)
        print()
        
        # Create output directories
        for location in ["Iran", "Kharej"]:
            (self.output_dir / location).mkdir(parents=True, exist_ok=True)
        
        # Get selected profiles
        selected_profiles = self.config.get("settings", {}).get("profiles", ["balanced"])
        
        total_configs = 0
        
        # Process each connection
        for conn in self.config["connections"]:
            iran_name = conn["iran"]
            kharej_name = conn["kharej"]
            
            # Find server details
            iran = next((s for s in self.config["iran_servers"] if s["name"] == iran_name), None)
            kharej = next((s for s in self.config["kharej_servers"] if s["name"] == kharej_name), None)
            
            if not iran or not kharej:
                print(f"[WARNING] Skipping {iran_name} -> {kharej_name}: Server not found")
                continue
            
            # Get token for this connection
            token = self.get_or_create_token(iran_name, kharej_name)
            
            # Get transports
            transports_config = conn.get("transports", [])
            if transports_config == "all" or transports_config == ["all"]:
                transports_list = list(self.transports.keys())
            else:
                transports_list = transports_config
            
            # Create server directories
            iran_dir = self.output_dir / "Iran" / iran_name
            kharej_dir = self.output_dir / "Kharej" / kharej_name
            iran_dir.mkdir(parents=True, exist_ok=True)
            kharej_dir.mkdir(parents=True, exist_ok=True)
            
            iran_services = []
            kharej_services = []
            
            # Process each transport
            for transport in transports_list:
                if transport not in self.transports:
                    print(f"[WARNING] Unknown transport: {transport}")
                    continue
                
                transport_info = self.transports[transport]
                
                # Determine mux versions
                mux_versions = [1, 2] if transport_info["mux"] else [None]
                
                # Process each mux version
                for mux_version in mux_versions:
                    # Process each profile
                    for profile in selected_profiles:
                        # Allocate ports
                        tunnel_port = self.get_next_port("tunnel")
                        web_port = self.get_next_port("web")
                        iperf_port = self.get_next_port("iperf")
                        
                        ports = {
                            "tunnel": tunnel_port,
                            "web": web_port,
                            "iperf": iperf_port
                        }
                        
                        # Get subnet for TUN transports
                        subnet = self.get_next_subnet() if transport_info["tun"] else None
                        
                        # Generate configs
                        server_config = self.generate_server_config(
                            iran, kharej, transport, profile, mux_version, ports, subnet, token
                        )
                        client_config = self.generate_client_config(
                            iran, kharej, transport, profile, mux_version, ports, subnet, token
                        )
                        
                        # Config file names
                        config_suffix = f"-{transport}"
                        if mux_version:
                            config_suffix += f"-v{mux_version}"
                        config_suffix += f"-{profile}"
                        
                        iran_config_name = f"iran{tunnel_port}{config_suffix}.toml"
                        kharej_config_name = f"kharej{tunnel_port}{config_suffix}.toml"
                        
                        # Save configs
                        iran_config_path = iran_dir / iran_config_name
                        kharej_config_path = kharej_dir / kharej_config_name
                        
                        with open(iran_config_path, 'w', encoding='utf-8') as f:
                            f.write(server_config)
                        
                        with open(kharej_config_path, 'w', encoding='utf-8') as f:
                            f.write(client_config)
                        
                        # Service names
                        service_suffix = config_suffix
                        iran_service_name = f"@lvlRF-Tunnel-iran{tunnel_port}{service_suffix}"
                        kharej_service_name = f"@lvlRF-Tunnel-kharej{tunnel_port}{service_suffix}"
                        
                        # Generate service files
                        iran_service = self.generate_service_file(
                            "iran", iran_name, kharej_name, iran_config_name,
                            iran_service_name, tunnel_port, transport, profile
                        )
                        
                        kharej_service = self.generate_service_file(
                            "kharej", kharej_name, iran_name, kharej_config_name,
                            kharej_service_name, tunnel_port, transport, profile
                        )
                        
                        iran_services.append({
                            "service_name": iran_service_name,
                            "service_content": iran_service
                        })
                        
                        kharej_services.append({
                            "service_name": kharej_service_name,
                            "service_content": kharej_service
                        })
                        
                        # Track in state
                        self.state["generated_configs"].append({
                            "iran": iran_name,
                            "kharej": kharej_name,
                            "transport": transport,
                            "profile": profile,
                            "mux_version": mux_version,
                            "tunnel_port": tunnel_port,
                            "web_port": web_port,
                            "iperf_port": iperf_port,
                            "subnet": subnet,
                            "token": token
                        })
                        
                        total_configs += 1
                        
                        # Print progress
                        transport_desc = transport
                        if mux_version:
                            transport_desc += f"-v{mux_version}"
                        print(f"[OK] {iran_name} -> {kharej_name}: {transport_desc}-{profile} (Port {tunnel_port})")
            
            # Generate management scripts for Iran
            if iran_services:
                self.generate_management_scripts(iran_dir, "iran", iran_name, iran_services)
            
            # Generate management scripts for Kharej
            if kharej_services:
                self.generate_management_scripts(kharej_dir, "kharej", kharej_name, kharej_services)
        
        # Save state
        self.save_state()
        
        print()
        print("=" * 60)
        print(f"[OK] Generated {total_configs} configurations successfully!")
        print(f"Output directory: {self.output_dir.absolute()}")
        print(f"State saved to: state.json")
        print("=" * 60)
        
        return total_configs
    
    def generate_service_file(self, server_type: str, server_name: str,
                             remote_name: str, config_filename: str,
                             service_name: str, tunnel_port: int,
                             transport: str, profile: str) -> str:
        """Generate systemd service file content"""
        
        if server_type == "iran":
            desc = f"Backhaul Iran {server_name} -> {remote_name} ({transport.upper()}-{profile.upper()}) Port {tunnel_port}"
        else:
            desc = f"Backhaul Kharej {server_name} <- {remote_name} ({transport.upper()}-{profile.upper()}) Port {tunnel_port}"
        
        return f"""[Unit]
Description={desc}
After=network.target

[Service]
Type=simple
WorkingDirectory={self.binary_path}
ExecStart={self.binary_path}/./{self.binary_filename} -c {self.binary_path}/{config_filename}
Restart=always
RestartSec=3
LimitNOFILE=1048576

[Install]
WantedBy=multi-user.target
"""
    
    def generate_management_scripts(self, server_dir: Path, server_type: str,
                                   server_name: str, services: List[Dict]):
        """Generate management scripts for services"""
        
        # install-services.sh
        install_script = f"""#!/bin/bash
# Backhaul Service Installation Script
# Server: {server_name}
# Type: {server_type.upper()}

set -e

echo "Installing Backhaul services for {server_name}..."
echo ""

# Extract binary from compressed file
echo "Extracting binary: {self.binary_filename}.tar.gz"
cd {self.binary_path}
if [ -f "{self.binary_filename}.tar.gz" ]; then
    tar -xzf {self.binary_filename}.tar.gz
    chmod +x {self.binary_filename}
    echo "[OK] Binary extracted"
else
    echo "[WARNING] {self.binary_filename}.tar.gz not found, skipping extraction"
fi
echo ""

"""
        
        for svc in services:
            service_name = svc["service_name"]
            service_content = svc["service_content"]
            
            install_script += f"""
cat > /etc/systemd/system/{service_name}.service << 'EOF'
{service_content}EOF

"""
        
        install_script += """
# Reload systemd daemon
systemctl daemon-reload

"""
        
        for svc in services:
            service_name = svc["service_name"]
            install_script += f"""# Enable and start {service_name}
systemctl enable {service_name}.service
systemctl start {service_name}.service

"""
        
        install_script += """
echo ""
echo "[OK] All services installed and started!"
echo ""
"""
        
        # stop-services.sh
        stop_script = f"""#!/bin/bash
# Stop all Backhaul services for {server_name}

echo "Stopping all Backhaul services..."
echo ""

"""
        for svc in services:
            service_name = svc["service_name"]
            stop_script += f"systemctl stop {service_name}.service\n"
        
        stop_script += """
echo ""
echo "[OK] All services stopped!"
"""
        
        # restart-services.sh
        restart_script = f"""#!/bin/bash
# Restart all Backhaul services for {server_name}

echo "Restarting all Backhaul services..."
echo ""

"""
        for svc in services:
            service_name = svc["service_name"]
            restart_script += f"systemctl restart {service_name}.service\n"
        
        restart_script += """
echo ""
echo "[OK] All services restarted!"
"""
        
        # remove-services.sh
        remove_script = f"""#!/bin/bash
# Remove all Backhaul services for {server_name}

echo "WARNING: This will remove all Backhaul services and optionally config files!"
echo ""

while true; do
    read -p "Are you sure? (yes/no): " confirm
    case $confirm in
        yes) break ;;
        no) echo "Cancelled."; exit 0 ;;
        *) echo "Please enter 'yes' or 'no'." ;;
    esac
done

echo ""
echo "Stopping and removing services..."
echo ""

"""
        for svc in services:
            service_name = svc["service_name"]
            remove_script += f"""systemctl stop {service_name}.service
systemctl disable {service_name}.service
rm -f /etc/systemd/system/{service_name}.service
echo "[OK] Removed {service_name}"

"""
        
        remove_script += """
systemctl daemon-reload

echo ""

while true; do
    read -p "Do you want to remove config files as well? (yes/no): " remove_configs
    case $remove_configs in
        yes)
            echo "[INFO] Config files would be removed here"
            break
            ;;
        no)
            break
            ;;
        *)
            echo "Please enter 'yes' or 'no'."
            ;;
    esac
done

echo ""
echo "[OK] All services removed!"
"""
        
        # Write scripts
        scripts = {
            "install-services.sh": install_script,
            "stop-services.sh": stop_script,
            "restart-services.sh": restart_script,
            "remove-services.sh": remove_script
        }
        
        for script_name, script_content in scripts.items():
            script_path = server_dir / script_name
            with open(script_path, 'w', encoding='utf-8', newline='\n') as f:
                f.write(script_content)
            os.chmod(script_path, 0o755)
    
    def generate_dashboard(self):
        """Generate HTML dashboard"""
        print()
        print("Generating Dashboard...")
        
        if not Path("state.json").exists():
            print("[ERROR] state.json not found! Run config generator first.")
            return False
        
        # Read template
        dashboard_template = Path(__file__).parent / "dashboard-template.html"
        if not dashboard_template.exists():
            print("[ERROR] dashboard-template.html not found!")
            return False
        
        with open(dashboard_template, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Embed state and config data
        state_json = json.dumps(self.state, ensure_ascii=False, indent=2)
        config_json = json.dumps(self.config, ensure_ascii=False, indent=2)
        
        # Replace placeholder with embedded data
        html_content = html_content.replace(
            '// STATE_DATA_PLACEHOLDER',
            f'const stateData = {state_json};\nconst configData = {config_json};'
        )
        
        # Write dashboard
        output_file = Path("dashboard.html")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"[OK] Dashboard generated: {output_file.absolute()}")
        return True

def get_valid_input(prompt: str, valid_options: list) -> str:
    """Get valid input from user"""
    while True:
        user_input = input(prompt).strip().lower()
        if user_input in valid_options:
            return user_input
        print(f"Invalid input. Please enter one of: {', '.join(valid_options)}")

def interactive_menu():
    """Interactive menu for generator"""
    print()
    print("=" * 60)
    print("Backhaul Premium Bulk Config Generator")
    print("=" * 60)
    print()
    print("What would you like to generate?")
    print()
    print("[1] Configs only")
    print("[2] Configs + Dashboard")
    print("[3] Configs + Optimization scripts")
    print("[4] Everything (Configs + Dashboard + Optimization)")
    print("[5] View current state")
    print("[0] Exit")
    print()
    
    choice = get_valid_input("Enter choice (0-5): ", ['0', '1', '2', '3', '4', '5'])
    
    if choice == '0':
        print("Goodbye!")
        return
    
    generator = BackhaulBulkGenerator()
    
    if choice == '5':
        generator.view_state()
        return
    
    # Generate configs
    if choice in ['1', '2', '3', '4']:
        generator.generate_all_configs()
    
    # Generate dashboard
    if choice in ['2', '4']:
        generator.generate_dashboard()
    
    # Copy optimization scripts
    if choice in ['3', '4']:
        print()
        print("Copying optimization scripts...")
        import shutil
        
        src_iran = Path(__file__).parent / "optimize-iran.sh"
        src_kharej = Path(__file__).parent / "optimize-kharej.sh"
        
        if src_iran.exists() and src_kharej.exists():
            # Copy to each Iran server dir
            for iran_server in generator.config.get("iran_servers", []):
                dest_dir = generator.output_dir / "Iran" / iran_server["name"]
                if dest_dir.exists():
                    shutil.copy(src_iran, dest_dir / "optimize-iran.sh")
                    os.chmod(dest_dir / "optimize-iran.sh", 0o755)
            
            # Copy to each Kharej server dir
            for kharej_server in generator.config.get("kharej_servers", []):
                dest_dir = generator.output_dir / "Kharej" / kharej_server["name"]
                if dest_dir.exists():
                    shutil.copy(src_kharej, dest_dir / "optimize-kharej.sh")
                    os.chmod(dest_dir / "optimize-kharej.sh", 0o755)
            
            print("[OK] Optimization scripts copied!")
        else:
            print("[WARNING] Optimization scripts not found")

def main():
    try:
        interactive_menu()
    except KeyboardInterrupt:
        print("\n\n[INFO] Interrupted by user")
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
