# Dashboard Usage Guide

Complete guide for using the Tunnel Management Dashboard

---

## 🚀 Getting Started

### Generate Dashboard

```bash
python3 generator.py

# Choose option [2] or [4]:
[2] Configs + Dashboard
[4] Everything (Configs + Dashboard + Optimization)
```

### Open Dashboard

1. Locate `dashboard.html` in project root
2. Double-click to open in browser
3. Or: `python3 -m http.server 8000` then visit `http://localhost:8000/dashboard.html`

---

## 📊 Dashboard Features

### Header

```
🚀 Tunnel Management Dashboard    [📚 Transport Guide]
```

- **Title:** Shows you're in the tunnel management interface
- **Transport Guide:** Click to view detailed transport information

---

### Quick Actions

Located at top, applies to all configurations:

#### 📦 Extract & Chmod Binary
**Command:** 
```bash
cd /root/backhaul-core && tar -xzf backhaul_premium.tar.gz && chmod +x backhaul_premium
```
**When to use:** First time setup, before installing services

#### 🔄 Restart All Services
**Command:**
```bash
cd /root/backhaul-core && bash restart-services.sh
```
**When to use:** After config changes, troubleshooting

#### ⏸️ Stop All Services
**Command:**
```bash
cd /root/backhaul-core && bash stop-services.sh
```
**When to use:** Maintenance, stopping all tunnels

#### 🗑️ Remove All Services
**Command:**
```bash
cd /root/backhaul-core && bash remove-services.sh
```
**When to use:** Complete removal, fresh start

---

### Filters

**Search Box:**
- Search by server name, port number, transport type
- Real-time filtering as you type

**Server Filter:**
- Show configs for specific server
- Dropdown lists all servers (Iran + Kharej)

**Transport Filter:**
- Filter by transport type (TCP, TCPMUX, WS, etc.)
- Useful for comparing same transport across profiles

**Profile Filter:**
- Show only Speed, Stable, or Balanced configs
- Compare performance characteristics

---

### Config Cards

Each card represents one tunnel configuration:

#### Card Header
```
backhaul-iran100-tcp-speed
Asiatech-Unlimite34 (Iran) → Marzban-DE-Hetzner (Kharej)
TCP    SPEED
```

- **Service name:** Full systemd service name
- **Connection:** Shows Iran → Kharej relationship
- **Transport & Profile:** Quick identification

#### Config Information
```
Tunnel Port: 100
Web Port: 800
iperf Port: 5001
Subnet: 10.10.10.0/24  (TUN transports only)
```

- **Tunnel Port:** Main connection port
- **Web Port:** Web interface access port
- **iperf Port:** Speed testing port
- **Subnet:** Virtual network (TUN transports)

#### Action Buttons

**🌐 Web Panel Buttons:**
- **Web Asiatech-Unlimite34:** Opens `http://1.2.3.4:800`
- **Web Marzban-DE-Hetzner:** Opens `http://5.6.7.8:800`
- Opens in new tab automatically
- IPs read from config.json

**📊 Status Buttons:**
```bash
systemctl status backhaul-iran100-tcp-speed.service
systemctl status backhaul-kharej100-tcp-speed.service
```
- Check if service is running
- View service health

**▶️ Start Buttons:**
```bash
systemctl start backhaul-iran100-tcp-speed.service
systemctl start backhaul-kharej100-tcp-speed.service
```
- Start stopped service
- Use after stop or reboot

**⏸️ Stop Buttons:**
```bash
systemctl stop backhaul-iran100-tcp-speed.service
systemctl stop backhaul-kharej100-tcp-speed.service
```
- Stop running service
- Use for maintenance

**🔄 Restart Buttons:**
```bash
systemctl restart backhaul-iran100-tcp-speed.service
systemctl restart backhaul-kharej100-tcp-speed.service
```
- Restart service
- Apply config changes

**📜 Logs Buttons:**
```bash
journalctl -u backhaul-iran100-tcp-speed.service -f
journalctl -u backhaul-kharej100-tcp-speed.service -f
```
- View real-time logs
- `-f` flag follows log output
- Press Ctrl+C to exit

---

### Transport Guide Modal

Click **📚 Transport Guide** button to open detailed guide.

**Content includes:**
- All 13 transport types explained
- Best use cases for each
- Performance characteristics
- Quick selection guide

**Example entries:**

**TCP Transport:**
- Best for: High speed downloads
- Features: Fastest speed, UDP over TCP
- Note: High connection count

**TCPMUX Transport:**
- Best for: General use, datacenter-friendly
- Features: Connection reuse, good speed
- Note: Congestion possible under heavy load

**uTCPMUX Transport:**
- Best for: Multi-user, VPN panels
- Features: Per-user isolation, no interference
- Better than TCPMUX for production

---

## 💡 Usage Scenarios

### Scenario 1: First Time Setup

1. Click **📦 Extract & Chmod Binary**
2. Command copies to clipboard
3. SSH to Iran server
4. Paste and execute
5. SSH to Kharej server
6. Paste and execute again

### Scenario 2: Check Service Status

1. Find config card for specific tunnel
2. Click **📊 Status {ServerName}**
3. Command copies to clipboard
4. SSH to server
5. Paste and execute
6. View service status

### Scenario 3: Restart After Config Change

1. Click **🔄 Restart {ServerName}**
2. Command copies to clipboard
3. SSH to server
4. Paste and execute
5. Service restarts with new config

### Scenario 4: View Real-time Logs

1. Click **📜 Logs {ServerName}**
2. Command copies to clipboard
3. SSH to server
4. Paste and execute
5. Watch logs stream
6. Press Ctrl+C to exit

### Scenario 5: Open Web Interface

1. Click **🌐 Web {ServerName}**
2. New tab opens automatically
3. View tunnel statistics
4. Monitor connections

### Scenario 6: Compare Profiles

1. Use **Profile Filter** dropdown
2. Select "Speed"
3. View all Speed configs
4. Click Web Panel to check performance
5. Switch to "Stable" in filter
6. Compare performance

### Scenario 7: Server Maintenance

1. Select server in **Server Filter**
2. Click **⏸️ Stop** on each config
3. Perform maintenance
4. Click **▶️ Start** to resume

### Scenario 8: Emergency Stop

1. Click **⏸️ Stop All Services**
2. Command copies
3. Paste in each server terminal
4. All tunnels stop immediately

---

## 🎯 Pro Tips

### Tip 1: Use Search
```
Search: "tcp-speed"
Result: Shows only TCP Speed configs
```

### Tip 2: Multiple Filters
```
Server: Tehran-Main
Transport: TCP
Profile: Speed
Result: Exact match
```

### Tip 3: Keyboard Workflow
1. Click button → Command copies
2. Alt+Tab → Switch to terminal
3. Ctrl+Shift+V → Paste
4. Enter → Execute

### Tip 4: Open Multiple Web Panels
- Ctrl+Click on Web Panel buttons
- Opens in new tab without closing dashboard
- Monitor multiple tunnels simultaneously

### Tip 5: Keep Dashboard Open
- Dashboard doesn't need server connection
- Works offline (embedded data)
- Keep open while working in terminal

### Tip 6: Bookmark Dashboard
- Add to browser bookmarks
- Quick access during troubleshooting

---

## 🔍 Troubleshooting

### Dashboard Shows No Configs

**Cause:** generator.py not run yet

**Solution:**
```bash
python3 generator.py
# Choose option [2] or [4]
```

### Web Panel Won't Open

**Cause:** Firewall blocking port

**Solution:**
```bash
# On server
ufw allow {WEB_PORT}/tcp
# Or
iptables -A INPUT -p tcp --dport {WEB_PORT} -j ACCEPT
```

### Commands Not Copying

**Cause:** Browser clipboard permissions

**Solution:**
- Allow clipboard access in browser
- Or manually copy command text

### Wrong IP in Web Panel

**Cause:** Incorrect IP in config.json

**Solution:**
1. Edit config.json
2. Fix server IPs
3. Re-run generator with option [2] or [4]

---

## 📱 Mobile Usage

Dashboard is responsive and works on mobile:

- **Tap** buttons to copy commands
- Use mobile SSH apps (Termius, ConnectBot)
- **Paste** commands in SSH session
- View web panels in mobile browser

---

## 🌐 Browser Compatibility

**Recommended:**
- Chrome 90+
- Firefox 88+
- Edge 90+
- Safari 14+

**Features require:**
- JavaScript enabled
- Clipboard API support
- Modern CSS support

---

## 🎨 Customization

Dashboard uses Vazir font from CDN for Persian support.

If you need offline usage:
1. Download Vazir font
2. Place in `fonts/` directory
3. Update CSS to use local font

---

## 📊 Performance

**Dashboard loads:**
- Instantly (embedded data)
- No network requests needed
- Works completely offline

**Search/Filter:**
- Real-time filtering
- Handles 100+ configs smoothly

---

**Enjoy the dashboard!** 🎉
