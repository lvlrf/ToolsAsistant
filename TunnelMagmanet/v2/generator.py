#!/usr/bin/env python3
"""
Backhaul Configuration Generator
Supports both Standard and Premium versions simultaneously
Author: Generated for managing multiple Backhaul tunnels
"""

import json
import os
import secrets
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime


class BackhaulGenerator:
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.config = self.load_config()
        self.state = self.load_state()
        self.output_dir = Path("output")
        
        # Binary paths and filenames from config
        binary_config = self.config.get("binary_config", {})
        
        # Standard binary config
        standard_config = binary_config.get("standard", {})
        standard_path = standard_config.get("path", "/root")
        standard_filename = standard_config.get("filename", "backhaul")
        
        # Premium binary config
        premium_config = binary_config.get("premium", {})
        premium_path = premium_config.get("path", "/root/backhaul-core")
        premium_filename = premium_config.get("filename", "backhaul_premium")
        
        # Construct full binary paths
        self.binary_paths = {
            "standard": f"{standard_path}/{standard_filename}",
            "premium": f"{premium_path}/{premium_filename}"
        }
        
        # Also store path and filename separately for config file generation
        self.binary_details = {
            "standard": {
                "path": standard_path,
                "filename": standard_filename,
                "full_path": f"{standard_path}/{standard_filename}"
            },
            "premium": {
                "path": premium_path,
                "filename": premium_filename,
                "full_path": f"{premium_path}/{premium_filename}"
            }
        }
        
        # Supported transports for each version
        self.transports = {
            "standard": ["tcp", "tcpmux", "udp", "ws", "wsmux"],
            "premium": ["tcp", "tcpmux", "utcpmux", "udp", "ws", "wsmux", "uwsmux", "tcptun", "faketcptun"]
        }
        
        # TUN-based transports (need special config)
        self.tun_transports = ["tcptun", "faketcptun"]
        
        # UDP over X transports
        self.udp_over_transports = ["utcpmux", "uwsmux"]
        
        # Multiplexed transports
        self.mux_transports = ["tcpmux", "wsmux", "utcpmux", "uwsmux"]
        
        # WebSocket transports
        self.ws_transports = ["ws", "wsmux", "uwsmux"]
        
    def load_config(self) -> Dict:
        """Load configuration from JSON file"""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def load_state(self) -> Dict:
        """Load or create state file for incremental updates"""
        state_path = "state.json"
        
        if os.path.exists(state_path):
            with open(state_path, 'r') as f:
                return json.load(f)
        
        # Create new state
        settings = self.config.get("settings", {})
        return {
            "last_tunnel_port": settings.get("tunnel_port_start", 100) - 1,
            "last_web_port": settings.get("web_port_start", 800) - 1,
            "last_iperf_port": settings.get("iperf_iran_port_start", 5001) - 1,
            "last_tun_subnet": 0,  # For 10.10.X.0/24
            "token": self.generate_token(),
            "generated_configs": [],
            "created_at": datetime.now().isoformat()
        }
    
    def save_state(self):
        """Save current state to file"""
        self.state["updated_at"] = datetime.now().isoformat()
        with open("state.json", 'w') as f:
            json.dump(self.state, indent=2, fp=f)
    
    def generate_token(self) -> str:
        """Generate a random 32-character hexadecimal token"""
        return secrets.token_hex(16)
    
    def get_next_port(self, port_type: str) -> int:
        """Get next available port and increment"""
        key = f"last_{port_type}_port"
        self.state[key] += 1
        return self.state[key]
    
    def get_next_subnet(self) -> str:
        """Get next TUN subnet for TUN-based transports"""
        self.state["last_tun_subnet"] += 10
        subnet_num = self.state["last_tun_subnet"]
        return f"10.10.{subnet_num}.0/24"
    
    def generate_server_config(self, iran: Dict, kharej: Dict, transport: str, 
                               version: str, ports: Dict) -> Tuple[str, str]:
        """
        Generate server (Iran) configuration
        Returns: (config_content, subnet_for_tun_or_none)
        """
        
        tunnel_port = ports["tunnel"]
        web_port = ports["web"]
        token = self.state["token"]
        is_tun = transport in self.tun_transports
        
        config = f"""[server]
bind_addr = "0.0.0.0:{tunnel_port}"
transport = "{transport}"
"""
        
        # Add accept_udp only for tcp transport
        if transport == "tcp":
            config += "accept_udp = false\n"
        
        config += f"""token = "{token}"
"""
        
        # Keepalive and nodelay (not for UDP, not for TUN)
        if transport != "udp" and not is_tun:
            config += "keepalive_period = 75\n"
        
        if transport not in ["udp"] + self.tun_transports:
            config += "nodelay = true\n"
        
        # Channel size (not for TUN)
        if not is_tun:
            config += "channel_size = 2048\n"
        
        # Heartbeat (not for TUN)
        if not is_tun:
            config += "heartbeat = 40\n"
        
        # Mux settings
        if transport in self.mux_transports:
            config += """mux_con = 8
mux_version = 2
mux_framesize = 32768
mux_recievebuffer = 4194304
mux_streambuffer = 2000000
"""
        
        # TUN settings
        subnet = None
        if is_tun:
            subnet = self.get_next_subnet()
            config += f"""tun_name = "backhaul{tunnel_port}"
tun_subnet = "{subnet}"
mtu = 1500
"""
        
        # Sniffer and web interface
        config += f"""sniffer = true
web_port = {web_port}
sniffer_log = "/root/backhaul-{tunnel_port}.json"
log_level = "info"
"""
        
        # Proxy protocol (Premium only, not for ws/udp/tcptun/faketcptun)
        if version == "premium" and transport not in ["ws", "udp", "tcptun", "faketcptun"]:
            config += "proxy_protocol = false\n"
        
        # Ports array (empty for TUN transports)
        if not is_tun:
            config += "\nports = []\n"
        
        return config, subnet
    
    def generate_client_config(self, iran: Dict, kharej: Dict, transport: str,
                              version: str, ports: Dict, subnet: str = None) -> str:
        """Generate client (Kharej) configuration"""
        
        tunnel_port = ports["tunnel"]
        web_port = ports["web"]
        iperf_port = ports["iperf"]
        token = self.state["token"]
        iran_ip = iran["ip"]
        iperf_kharej_port = self.config["settings"]["iperf_kharej_port"]
        is_tun = transport in self.tun_transports
        
        config = f"""[client]
remote_addr = "{iran_ip}:{tunnel_port}"
"""
        
        # Edge IP for WebSocket transports
        if transport in self.ws_transports:
            config += '#edge_ip = "188.114.96.0"\n'
        
        config += f"""transport = "{transport}"
token = "{token}"
"""
        
        # Connection pool (not for TUN)
        if not is_tun:
            config += """connection_pool = 8
aggressive_pool = false
"""
        
        # Keepalive (not for UDP, not for TUN)
        if transport != "udp" and not is_tun:
            config += "keepalive_period = 75\n"
        
        # Nodelay (not for UDP, not for TUN)
        if transport not in ["udp"] + self.tun_transports:
            config += "nodelay = true\n"
        
        # Retry settings (not for TUN)
        if not is_tun:
            config += """retry_interval = 3
dial_timeout = 10
"""
        
        # Mux settings
        if transport in self.mux_transports:
            config += """mux_version = 2
mux_framesize = 32768
mux_recievebuffer = 4194304
mux_streambuffer = 2000000
"""
        
        # TUN settings (must match server)
        if is_tun and subnet:
            config += f"""tun_name = "backhaul{tunnel_port}"
tun_subnet = "{subnet}"
mtu = 1500
"""
        
        # Sniffer and web interface
        config += f"""sniffer = true
web_port = {web_port}
sniffer_log = "/root/backhaul-{tunnel_port}.json"
log_level = "info"
"""
        
        # IP Limit (Premium only, not for ws/udp/tcptun/faketcptun)
        if version == "premium" and transport not in ["ws", "udp", "tcptun", "faketcptun"]:
            config += "ip_limit = false\n"
        
        # Port mapping for iperf3 (not for TUN transports)
        if not is_tun:
            config += f"""
ports = ["{iperf_port}=127.0.0.1:{iperf_kharej_port}"]
"""
        
        return config
    
    def generate_service_file(self, server_type: str, server_name: str, 
                             kharej_name: str, transport: str, version: str,
                             config_path: str, binary_path: str, tunnel_port: int) -> str:
        """Generate systemd service file content"""
        
        if server_type == "iran":
            desc = f"Backhaul Iran {server_name} -> {kharej_name} ({transport.upper()}) Port {tunnel_port}"
            service_name = f"backhaul-{server_name}-{kharej_name}-{transport}"
        else:
            desc = f"Backhaul Kharej {kharej_name} <- {server_name} ({transport.upper()}) Port {tunnel_port}"
            service_name = f"backhaul-{kharej_name}-{server_name}-{transport}"
        
        return f"""[Unit]
Description={desc}
After=network.target

[Service]
Type=simple
ExecStart={binary_path} -c {config_path}
Restart=always
RestartSec=3
LimitNOFILE=1048576

[Install]
WantedBy=multi-user.target
"""
    
    def generate_install_script(self, server_type: str, server_name: str, 
                                version: str, services: List[Dict]) -> str:
        """Generate installation script for copy-paste in terminal"""
        
        script = f"""#!/bin/bash
# Backhaul {version.upper()} - {server_type.upper()} Server: {server_name}
# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

echo "Installing Backhaul services for {server_name}..."

"""
        
        for svc in services:
            service_name = svc["service_name"]
            service_content = svc["service_content"]
            
            # Escape special characters for heredoc
            script += f"""
cat > /etc/systemd/system/{service_name}.service << 'EOF'
{service_content}EOF

"""
        
        script += """
# Reload systemd daemon
systemctl daemon-reload

"""
        
        # Enable and start services
        for svc in services:
            service_name = svc["service_name"]
            script += f"""# Enable and start {service_name}
systemctl enable {service_name}.service
systemctl start {service_name}.service

"""
        
        script += """
echo "✅ All services installed and started!"
echo ""
echo "Check status with:"
"""
        
        for svc in services:
            service_name = svc["service_name"]
            script += f"""echo "  systemctl status {service_name}"
"""
        
        return script
    
    def generate_all_configs(self):
        """Main function to generate all configurations"""
        
        print("🚀 Backhaul Configuration Generator")
        print("=" * 50)
        print(f"Token: {self.state['token']}")
        print("=" * 50)
        print()
        
        # Create output directories
        for version in ["standard", "premium"]:
            for server_type in ["iran-servers", "kharej-servers"]:
                (self.output_dir / version / server_type).mkdir(parents=True, exist_ok=True)
        
        # Port mapping tracking
        port_mappings = []
        
        # Process each connection
        for conn in self.config["connections"]:
            iran_name = conn["iran"]
            kharej_name = conn["kharej"]
            
            # Find server details
            iran = next((s for s in self.config["iran_servers"] if s["name"] == iran_name), None)
            kharej = next((s for s in self.config["kharej_servers"] if s["name"] == kharej_name), None)
            
            if not iran or not kharej:
                print(f"⚠️  Skipping {iran_name} -> {kharej_name}: Server not found")
                continue
            
            # Process Standard version
            self._process_version("standard", iran, kharej, conn.get("standard_transports", []), port_mappings)
            
            # Process Premium version
            self._process_version("premium", iran, kharej, conn.get("premium_transports", []), port_mappings)
        
        # Generate port mapping document
        self._generate_port_mapping_doc(port_mappings)
        
        # Save state
        self.save_state()
        
        print()
        print("✅ All configurations generated successfully!")
        print(f"📁 Output directory: {self.output_dir.absolute()}")
        print(f"💾 State saved to: state.json")
        print()
    
    def _process_version(self, version: str, iran: Dict, kharej: Dict, 
                        transports: List[str], port_mappings: List):
        """Process configurations for a specific version"""
        
        if not transports:
            return
        
        iran_name = iran["name"]
        kharej_name = kharej["name"]
        binary_path = self.binary_paths[version]
        
        # Create server directories
        iran_dir = self.output_dir / version / "iran-servers" / iran_name
        kharej_dir = self.output_dir / version / "kharej-servers" / kharej_name
        iran_dir.mkdir(parents=True, exist_ok=True)
        kharej_dir.mkdir(parents=True, exist_ok=True)
        
        iran_services = []
        kharej_services = []
        
        for transport in transports:
            # Validate transport for version
            if transport not in self.transports[version]:
                print(f"⚠️  Skipping {transport} for {version}: Not supported")
                continue
            
            # Allocate ports
            tunnel_port = self.get_next_port("tunnel")
            web_port = self.get_next_port("web")
            iperf_port = self.get_next_port("iperf")
            
            ports = {
                "tunnel": tunnel_port,
                "web": web_port,
                "iperf": iperf_port
            }
            
            # Generate configs
            server_config, subnet = self.generate_server_config(iran, kharej, transport, version, ports)
            client_config = self.generate_client_config(iran, kharej, transport, version, ports, subnet)
            
            # Save config files
            config_filename = f"config-{kharej_name}-{transport}.toml"
            iran_config_path = iran_dir / config_filename
            kharej_config_path = kharej_dir / f"config-{iran_name}-{transport}.toml"
            
            with open(iran_config_path, 'w') as f:
                f.write(server_config)
            
            with open(kharej_config_path, 'w') as f:
                f.write(client_config)
            
            # Generate service files
            iran_service_name = f"backhaul-{iran_name}-{kharej_name}-{transport}"
            kharej_service_name = f"backhaul-{kharej_name}-{iran_name}-{transport}"
            
            iran_service = self.generate_service_file(
                "iran", iran_name, kharej_name, transport, version,
                f"/root/{config_filename}", binary_path, tunnel_port
            )
            
            kharej_service = self.generate_service_file(
                "kharej", kharej_name, iran_name, transport, version,
                f"/root/config-{iran_name}-{transport}.toml", binary_path, tunnel_port
            )
            
            iran_services.append({
                "service_name": iran_service_name,
                "service_content": iran_service
            })
            
            kharej_services.append({
                "service_name": kharej_service_name,
                "service_content": kharej_service
            })
            
            # Track port mapping
            port_mappings.append({
                "version": version,
                "iran": iran_name,
                "kharej": kharej_name,
                "transport": transport,
                "tunnel_port": tunnel_port,
                "web_port": web_port,
                "iperf_port": iperf_port,
                "subnet": subnet
            })
            
            print(f"✓ Generated {version.upper()}: {iran_name} -> {kharej_name} ({transport}) Port {tunnel_port}")
        
        # Generate install scripts
        if iran_services:
            iran_install = self.generate_install_script("iran", iran_name, version, iran_services)
            with open(iran_dir / "install-services.sh", 'w') as f:
                f.write(iran_install)
            os.chmod(iran_dir / "install-services.sh", 0o755)
        
        if kharej_services:
            kharej_install = self.generate_install_script("kharej", kharej_name, version, kharej_services)
            with open(kharej_dir / "install-services.sh", 'w') as f:
                f.write(kharej_install)
            os.chmod(kharej_dir / "install-services.sh", 0o755)
    
    def _generate_port_mapping_doc(self, port_mappings: List[Dict]):
        """Generate port mapping documentation"""
        
        doc = f"""# Backhaul Port Mapping
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Token: `{self.state['token']}`

---

## Port Assignments

| Version | Iran → Kharej | Transport | Tunnel Port | Web Port | iperf3 Port | TUN Subnet |
|---------|---------------|-----------|-------------|----------|-------------|------------|
"""
        
        for mapping in port_mappings:
            subnet = mapping.get('subnet') or '-'
            doc += f"| {mapping['version'].upper():8} | {mapping['iran']} → {mapping['kharej']} | {mapping['transport']:9} | {mapping['tunnel_port']:11} | {mapping['web_port']:8} | {mapping['iperf_port']:11} | {subnet:10} |\n"
        
        doc += f"""

---

## iperf3 Testing Guide

### On Kharej Servers:
Start iperf3 server on localhost:
```bash
iperf3 -s -B 127.0.0.1 -p {self.config['settings']['iperf_kharej_port']}
```

### On Iran Servers:
Test each tunnel individually:
```bash
"""
        
        for mapping in port_mappings:
            if mapping.get('subnet'):  # Skip TUN-based transports
                continue
            doc += f"iperf3 -c 127.0.0.1 -p {mapping['iperf_port']} -t 10  # {mapping['transport']} to {mapping['kharej']}\n"
        
        doc += f"""```

---

## Web Interface Access

Access the web sniffer interface at:
"""
        
        # Group by server
        iran_servers = {}
        kharej_servers = {}
        
        for mapping in port_mappings:
            if mapping['iran'] not in iran_servers:
                iran_servers[mapping['iran']] = []
            if mapping['kharej'] not in kharej_servers:
                kharej_servers[mapping['kharej']] = []
            
            iran_servers[mapping['iran']].append(mapping)
            kharej_servers[mapping['kharej']].append(mapping)
        
        doc += "\n### Iran Servers:\n"
        for server, mappings in iran_servers.items():
            iran_ip = next(s['ip'] for s in self.config['iran_servers'] if s['name'] == server)
            doc += f"\n**{server}** (`{iran_ip}`):\n"
            for m in mappings:
                doc += f"- {m['transport']}: http://{iran_ip}:{m['web_port']}\n"
        
        doc += "\n### Kharej Servers:\n"
        for server, mappings in kharej_servers.items():
            kharej_ip = next(s['ip'] for s in self.config['kharej_servers'] if s['name'] == server)
            doc += f"\n**{server}** (`{kharej_ip}`):\n"
            for m in mappings:
                doc += f"- {m['transport']}: http://{kharej_ip}:{m['web_port']}\n"
        
        # Save document
        with open(self.output_dir / "port-mapping.md", 'w') as f:
            f.write(doc)


def main():
    try:
        generator = BackhaulGenerator("config.json")
        generator.generate_all_configs()
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print("\n💡 Please create a config.json file first!")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
