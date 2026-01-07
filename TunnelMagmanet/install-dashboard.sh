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

# Detect binary path
BINARY_PATH="/var/lib/@lvlRF-Tunnel"
if [ -f "config.json" ]; then
    DETECTED_PATH=$(grep -oP '(?<="path":\s*")[^"]+' config.json 2>/dev/null | head -1)
    if [ ! -z "$DETECTED_PATH" ]; then
        BINARY_PATH="$DETECTED_PATH"
    fi
fi

# If not in binary path, use current directory
if [ ! -f "dashboard.py" ] && [ -f "$BINARY_PATH/dashboard.py" ]; then
    cd "$BINARY_PATH"
elif [ ! -f "dashboard.py" ]; then
    echo "❌ dashboard.py not found!"
    exit 1
fi

CURRENT_PATH=$(pwd)
echo "📍 Path: $CURRENT_PATH"
echo ""

# Ask for password
echo "🔐 Dashboard Configuration"
echo ""
read -sp "Enter dashboard password: " DASH_PASSWORD
echo ""
read -sp "Confirm password: " DASH_PASSWORD2
echo ""

if [ "$DASH_PASSWORD" != "$DASH_PASSWORD2" ]; then
    echo "❌ Passwords don't match!"
    exit 1
fi

if [ -z "$DASH_PASSWORD" ]; then
    echo "❌ Password cannot be empty!"
    exit 1
fi

echo ""

# Ask for port
read -p "Enter dashboard port [8000]: " DASH_PORT
DASH_PORT=${DASH_PORT:-8000}

# Validate port
if ! [[ "$DASH_PORT" =~ ^[0-9]+$ ]] || [ "$DASH_PORT" -lt 1 ] || [ "$DASH_PORT" -gt 65535 ]; then
    echo "❌ Invalid port number!"
    exit 1
fi

# Check if port is in use
if ss -tulpn 2>/dev/null | grep -q ":$DASH_PORT " || netstat -tuln 2>/dev/null | grep -q ":$DASH_PORT "; then
    echo "❌ Port $DASH_PORT is already in use!"
    echo "Choose a different port."
    exit 1
fi

echo ""
echo "📝 Configuration:"
echo "  Password: ********"
echo "  Port: $DASH_PORT"
echo "  Path: $CURRENT_PATH"
echo ""

# Install Flask
echo "📦 Installing dependencies..."
if python3 -c "import flask" 2>/dev/null; then
    echo "✅ Flask already installed"
else
    pip3 install flask --break-system-packages 2>/dev/null || \
    pip3 install flask 2>/dev/null || \
    apt install -y python3-flask 2>/dev/null || {
        echo "❌ Failed to install Flask"
        exit 1
    }
    echo "✅ Flask installed"
fi

# Update dashboard.py with password and port
echo "⚙️  Updating configuration..."
if [ -f "dashboard.py.bak" ]; then
    rm dashboard.py.bak
fi
cp dashboard.py dashboard.py.bak
sed -i "s/^DASHBOARD_PORT = .*/DASHBOARD_PORT = $DASH_PORT/" dashboard.py
sed -i "s/^DASHBOARD_PASSWORD = .*/DASHBOARD_PASSWORD = \"$DASH_PASSWORD\"/" dashboard.py

# Set executable
chmod +x dashboard.py

# Create systemd service
echo "🔧 Creating systemd service..."
cat > /etc/systemd/system/lvlrf-dashboard.service << EOF
[Unit]
Description=@lvlRF Tunnel Management Dashboard
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$CURRENT_PATH
ExecStart=/usr/bin/python3 $CURRENT_PATH/dashboard.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Reload and start
echo "🔄 Starting service..."
systemctl daemon-reload
systemctl enable lvlrf-dashboard.service
systemctl start lvlrf-dashboard.service

# Wait a moment
sleep 2

# Check status
if systemctl is-active --quiet lvlrf-dashboard.service; then
    echo ""
    echo "=========================================="
    echo "✅ Dashboard installed successfully!"
    echo "=========================================="
    echo ""
    echo "🌐 Access: http://YOUR_SERVER_IP:$DASH_PORT"
    echo "🔑 Password: (the one you entered)"
    echo ""
    echo "Commands:"
    echo "  systemctl status lvlrf-dashboard"
    echo "  systemctl stop lvlrf-dashboard"
    echo "  systemctl restart lvlrf-dashboard"
    echo "  journalctl -u lvlrf-dashboard -f"
    echo ""
    echo "⚠️  Don't forget:"
    echo "  ufw allow $DASH_PORT/tcp"
    echo ""
else
    echo ""
    echo "❌ Service failed to start!"
    echo "Check logs: journalctl -u lvlrf-dashboard -n 50"
    exit 1
fi
