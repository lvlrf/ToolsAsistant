#!/bin/bash
# Backhaul STANDARD - KHAREJ Server: france-ovh
# Generated: 2026-01-03 13:37:04

echo "Installing Backhaul services for france-ovh..."


cat > /etc/systemd/system/backhaul-france-ovh-tehran-main-tcp.service << 'EOF'
[Unit]
Description=Backhaul Kharej tehran-main <- france-ovh (TCP) Port 106
After=network.target

[Service]
Type=simple
ExecStart=/root/backhaul -c /root/config-tehran-main-tcp.toml
Restart=always
RestartSec=3
LimitNOFILE=1048576

[Install]
WantedBy=multi-user.target
EOF


# Reload systemd daemon
systemctl daemon-reload

# Enable and start backhaul-france-ovh-tehran-main-tcp
systemctl enable backhaul-france-ovh-tehran-main-tcp.service
systemctl start backhaul-france-ovh-tehran-main-tcp.service


echo "✅ All services installed and started!"
echo ""
echo "Check status with:"
echo "  systemctl status backhaul-france-ovh-tehran-main-tcp"
