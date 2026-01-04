#!/bin/bash
# Backhaul STANDARD - IRAN Server: tehran-main
# Generated: 2026-01-03 13:37:04

echo "Installing Backhaul services for tehran-main..."


cat > /etc/systemd/system/backhaul-tehran-main-france-ovh-tcp.service << 'EOF'
[Unit]
Description=Backhaul Iran tehran-main -> france-ovh (TCP) Port 106
After=network.target

[Service]
Type=simple
ExecStart=/root/backhaul -c /root/config-france-ovh-tcp.toml
Restart=always
RestartSec=3
LimitNOFILE=1048576

[Install]
WantedBy=multi-user.target
EOF


# Reload systemd daemon
systemctl daemon-reload

# Enable and start backhaul-tehran-main-france-ovh-tcp
systemctl enable backhaul-tehran-main-france-ovh-tcp.service
systemctl start backhaul-tehran-main-france-ovh-tcp.service


echo "✅ All services installed and started!"
echo ""
echo "Check status with:"
echo "  systemctl status backhaul-tehran-main-france-ovh-tcp"
