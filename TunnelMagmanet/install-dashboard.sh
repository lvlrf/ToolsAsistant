#!/bin/bash
# @lvlRF Dashboard Service Installer

set -e

echo "=========================================="
echo "@lvlRF Dashboard Service Installer"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root (sudo)"
    exit 1
fi

# Install Flask if not installed
echo "📦 Installing dependencies..."
pip3 install flask --break-system-packages 2>/dev/null || pip3 install flask

# Set executable permission
chmod +x dashboard.py

# Create systemd service
echo "📝 Creating systemd service..."
cat > /etc/systemd/system/lvlrf-dashboard.service << 'EOF'
[Unit]
Description=@lvlRF Tunnel Management Dashboard
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/backhaul-core
ExecStart=/usr/bin/python3 /root/backhaul-core/dashboard.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
echo "🔄 Reloading systemd..."
systemctl daemon-reload

# Enable and start service
echo "▶️  Starting service..."
systemctl enable lvlrf-dashboard.service
systemctl start lvlrf-dashboard.service

echo ""
echo "=========================================="
echo "✅ Dashboard installed successfully!"
echo "=========================================="
echo ""
echo "Access: http://YOUR_SERVER_IP:8000"
echo ""
echo "Commands:"
echo "  Status:  systemctl status lvlrf-dashboard"
echo "  Stop:    systemctl stop lvlrf-dashboard"
echo "  Start:   systemctl start lvlrf-dashboard"
echo "  Restart: systemctl restart lvlrf-dashboard"
echo "  Logs:    journalctl -u lvlrf-dashboard -f"
echo ""
echo "⚠️  Don't forget to:"
echo "  1. Change PASSWORD in dashboard.py"
echo "  2. Open port 8000 in firewall"
echo "  3. Access via: http://SERVER_IP:8000"
echo ""
