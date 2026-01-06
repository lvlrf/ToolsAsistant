# Backhaul Premium Bulk Config Generator v2.0

Complete automated tool for generating tunnel configurations with **Live Web Dashboard**

---

## ✨ Key Features

### 🎯 Full Transport Support
- ✅ **13 transport types:** tcp, tcpmux, utcpmux, xtcpmux, ws, wsmux, uwsmux, xwsmux, udp, tcptun, faketcptun, wstun, udptun
- ✅ **Mux Versions:** v1 and v2 for all mux transports
- ✅ **TUN Support:** Automatic subnet management

### 🚀 Three Optimization Profiles
- **Speed:** Maximum bandwidth and speed
- **Stable:** Stability in unstable networks
- **Balanced:** Balance between speed and stability

### 📊 Live Web Dashboard ⭐ NEW!
- **Real-time status** of all services
- **Direct control:** Start/Stop/Restart from web
- **Edit ports** with auto-restart
- **View logs** in real-time
- **Test speed** with step-by-step guide
- **Dark mode** support
- **Auto-refresh** every 3 seconds
- **Remote access** via IP or domain
- **Secure login** with password protection

### 🛠 Complete Tools
- Service management scripts (install, stop, restart, remove)
- Server optimization scripts (Iran & Kharej)
- Interactive menu system

---

## 🚀 Quick Start

### 1. Generate Configs

```bash
python3 generator.py
# Choose [4] Everything
```

### 2. Setup Dashboard (Optional but Recommended!)

```bash
# Upload to server
scp dashboard.py install-dashboard.sh root@SERVER:/root/backhaul-core/

# Change password
nano dashboard.py  # Line 12: DASHBOARD_PASSWORD

# Install
bash install-dashboard.sh

# Access
http://YOUR_SERVER_IP:8000
```

### 3. Upload Configs

```bash
# Upload binary and configs
scp backhaul_premium.tar.gz root@SERVER:/root/backhaul-core/
scp output/Iran/Tehran-Main/* root@SERVER:/root/backhaul-core/
```

### 4. Install Services

**Option A: Via Dashboard (Recommended)**
```
http://YOUR_SERVER_IP:8000
→ Extract Binary button
→ Install button for each config
```

**Option B: Via Scripts**
```bash
cd /root/backhaul-core
bash install-services.sh
```

---

## 📊 Dashboard Features

### Live Monitoring
- ✅ Real-time service status (Active/Inactive)
- ✅ Auto-refresh every 3 seconds
- ✅ Filter by status, server, transport
- ✅ Dark/Light theme

### Direct Control
- ✅ Start/Stop/Restart services
- ✅ View real-time logs
- ✅ Edit ports (tunnel, web, iperf)
- ✅ Test speed with iperf3
- ✅ Bulk operations (start/stop all)

### Security
- ✅ Password-protected access
- ✅ Enable/Disable dashboard service
- ✅ Session management (24h)
- ✅ Remote access ready

**See DASHBOARD-README.md for complete guide**

---

## 🚀 Quick Start

### 1. Run Generator

```bash
python3 generator.py
```

**Interactive Menu:**
```
============================================================
Backhaul Premium Bulk Config Generator
============================================================

What would you like to generate?

[1] Configs only
[2] Configs + Dashboard
[3] Configs + Optimization scripts
[4] Everything (Configs + Dashboard + Optimization)
[5] View current state
[0] Exit

Enter choice (0-5): 
```

### 2. Choose Option

- **Option 1:** Generate only configuration files
- **Option 2:** Generate configs + HTML dashboard
- **Option 3:** Generate configs + optimization scripts
- **Option 4:** Generate everything (recommended)
- **Option 5:** View current state (ports, subnets, tokens)

### 3. Upload to Servers

```bash
# Upload binary
scp backhaul_premium.tar.gz root@SERVER_IP:/root/backhaul-core/

# Upload configs (example for Iran)
scp output/Iran/Tehran-Main/*.toml root@SERVER_IP:/root/backhaul-core/
scp output/Iran/Tehran-Main/*.sh root@SERVER_IP:/root/backhaul-core/
```

### 4. Install Services

```bash
ssh root@SERVER_IP
cd /root/backhaul-core
bash install-services.sh
```

### 5. Open Dashboard

Open `dashboard.html` in your browser to manage all configs!

---

## ⚙️ Configuration

### config.json Structure

```json
{
  "binary_config": {
    "premium": {
      "path": "/root/backhaul-core",
      "filename": "backhaul_premium"
    }
  },

  "settings": {
    "tunnel_port_start": 100,
    "web_port_start": 800,
    "iperf_iran_port_start": 5001,
    "iperf_kharej_port": 5201,
    "excluded_ports": [22, 80, 443, 8080],
    "profiles": ["speed", "stable", "balanced"],
    "token_per_connection": true
  },

  "iran_servers": [
    {"name": "Tehran-Main", "ip": "1.2.3.4"}
  ],

  "kharej_servers": [
    {"name": "Germany-Hetzner", "ip": "5.6.7.8"}
  ],

  "connections": [
    {
      "iran": "Tehran-Main",
      "kharej": "Germany-Hetzner",
      "transports": "all"
    }
  ]
}
```

### Transport Options

**All transports:**
```json
"transports": "all"
```
or
```json
"transports": ["all"]
```

**Specific transports:**
```json
"transports": ["tcp", "tcpmux", "ws", "tcptun"]
```

### Profile Options

**Single profile:**
```json
"profiles": ["balanced"]
```

**All profiles:**
```json
"profiles": ["speed", "stable", "balanced"]
```

---

## 📊 Dashboard Features

### Quick Actions
- **📦 Extract & Chmod Binary:** Extract and set permissions
- **🔄 Restart All Services:** Restart all services
- **⏸️ Stop All Services:** Stop all services
- **🗑️ Remove All Services:** Remove all services

### Per-Config Actions
- **🌐 Web Panel:** Open web interface (auto-detects IP)
- **📊 Status:** Check service status
- **▶️ Start:** Start service
- **⏸️ Stop:** Stop service
- **🔄 Restart:** Restart service
- **📜 Logs:** View real-time logs

### Filters
- Search by name, port, transport
- Filter by server
- Filter by transport type
- Filter by profile

### Transport Guide
- Quick reference for all transports
- Best use cases
- Performance characteristics
- Available in header and footer

---

## 🎯 Optimization Profiles

### Speed Profile
```toml
channel_size = 4096
heartbeat = 20
mux_con = 128
connection_pool = 16
aggressive_pool = true
```
**Best for:** High bandwidth, large downloads, streaming

### Stable Profile
```toml
channel_size = 2048
heartbeat = 40
mux_con = 64
connection_pool = 8
aggressive_pool = false
```
**Best for:** Unstable networks, long-term connections

### Balanced Profile
```toml
channel_size = 2048
heartbeat = 20
mux_con = 64
connection_pool = 8
aggressive_pool = false
```
**Best for:** General use, recommended default

---

## 🔧 Service Management

### Via Dashboard
Click buttons in dashboard to copy commands, then paste in terminal

### Via Scripts

```bash
# Start all services
bash install-services.sh

# Stop all services
bash stop-services.sh

# Restart all services
bash restart-services.sh

# Remove all services
bash remove-services.sh
```

### Individual Service

```bash
# Status
systemctl status backhaul-iran100-tcp-speed.service

# Start
systemctl start backhaul-iran100-tcp-speed.service

# Stop
systemctl stop backhaul-iran100-tcp-speed.service

# Restart
systemctl restart backhaul-iran100-tcp-speed.service

# Logs
journalctl -u backhaul-iran100-tcp-speed.service -f
```

---

## 🌐 Web Interface

Each tunnel has a web interface:

```
http://SERVER_IP:800   # First tunnel
http://SERVER_IP:801   # Second tunnel
http://SERVER_IP:802   # Third tunnel
...
```

Dashboard opens these automatically with server IPs from config.json!

---

## 🧪 Speed Testing with iperf3

### On Kharej:
```bash
iperf3 -s -B 127.0.0.1 -p 5201
```

### On Iran:
```bash
# First tunnel
iperf3 -c 127.0.0.1 -p 5001 -t 30

# Second tunnel
iperf3 -c 127.0.0.1 -p 5002 -t 30
```

---

## 📁 Output Structure

```
output/
├── Iran/
│   └── Tehran-Main/
│       ├── iran100-tcp-speed.toml
│       ├── iran101-tcp-stable.toml
│       ├── iran102-tcp-balanced.toml
│       ├── ... (all configs)
│       ├── install-services.sh
│       ├── stop-services.sh
│       ├── restart-services.sh
│       ├── remove-services.sh
│       └── optimize-iran.sh (if option 3 or 4)
│
└── Kharej/
    └── Germany-Hetzner/
        ├── kharej100-tcp-speed.toml
        ├── ... (all configs)
        ├── install-services.sh
        ├── stop-services.sh
        ├── restart-services.sh
        ├── remove-services.sh
        └── optimize-kharej.sh (if option 3 or 4)
```

---

## 🛡️ Server Optimization

**Optional but recommended:**

```bash
# On Iran server
bash optimize-iran.sh

# On Kharej server
bash optimize-kharej.sh
```

**Features:**
- BBR congestion control
- TCP/UDP buffer optimization
- System limits adjustment
- **Automatic backup** before changes
- Reboot required after optimization

---

## ⚠️ Important Notes

### 1. Binary Path
```bash
# Correct
/root/backhaul-core/backhaul_premium
/root/backhaul-core/backhaul_premium.tar.gz

# Incorrect
/root/backhaul_premium
/tmp/backhaul_premium
```

### 2. TUN Subnets
- Must be network address (ending in .0)
- Example: `10.10.10.0/24` ✅
- Not: `10.10.10.1/24` ❌

### 3. Tokens
- One token per connection
- Iran and Kharej use same token
- Stored in state.json

### 4. Service Names
Pattern: `backhaul-{iran/kharej}{port}-{transport}-{profile}`

Examples:
- `backhaul-iran100-tcp-speed`
- `backhaul-iran101-tcpmux-v2-stable`
- `backhaul-kharej100-tcp-speed`

---

## 🐛 Troubleshooting

### Service Failed to Start
```bash
# Check logs
journalctl -u SERVICE_NAME -n 50

# Check binary
ls -la /root/backhaul-core/backhaul_premium

# Extract if needed
cd /root/backhaul-core
tar -xzf backhaul_premium.tar.gz
chmod +x backhaul_premium
```

### Port Already in Use
```bash
# Find process
ss -tlnp | grep PORT

# Kill process
kill -9 PID

# Or add port to excluded_ports in config.json
```

### Dashboard Not Working
- Make sure you ran generator with option 2 or 4
- Open dashboard.html in modern browser (Chrome, Firefox, Edge)
- Check browser console for errors

---

## 📚 Additional Resources

- [TRANSPORTS-GUIDE.md](TRANSPORTS-GUIDE.md) - Detailed transport explanations
- [PROFILES-GUIDE.md](PROFILES-GUIDE.md) - Profile comparison
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues
- [QUICKSTART.md](QUICKSTART.md) - 5-minute setup guide

---

## 🆕 What's New in v2.0

- ✅ Interactive menu system
- ✅ Integrated dashboard generation
- ✅ No separate scripts needed
- ✅ Input validation (yes/no prompts)
- ✅ Cleaner file structure
- ✅ Dashboard with auto IP detection
- ✅ English-only interface
- ✅ Vazir font from CDN
- ✅ Transport guide in dashboard
- ✅ Extract & Chmod quick action
- ✅ Improved service management

---

**Version:** 2.0.0  
**Date:** 2026-01-06  
**Compatible with:** Backhaul Premium v1.3.0+
