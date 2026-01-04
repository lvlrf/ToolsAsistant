#!/bin/bash
# Backhaul STANDARD - IRAN Server: shiraz-backup
# Generated: 2026-01-03 13:37:04

echo "Installing Backhaul services for shiraz-backup..."


cat > /etc/systemd/system/backhaul-shiraz-backup-germany-hetzner-ws.service << 'EOF'
[Unit]
Description=Backhaul Iran shiraz-backup -> germany-hetzner (WS) Port 109
After=network.target

[Service]
Type=simple
ExecStart=/root/backhaul -c /root/config-germany-hetzner-ws.toml
Restart=always
RestartSec=3
LimitNOFILE=1048576

[Install]
WantedBy=multi-user.target
EOF


cat > /etc/systemd/system/backhaul-shiraz-backup-germany-hetzner-wsmux.service << 'EOF'
[Unit]
Description=Backhaul Iran shiraz-backup -> germany-hetzner (WSMUX) Port 110
After=network.target

[Service]
Type=simple
ExecStart=/root/backhaul -c /root/config-germany-hetzner-wsmux.toml
Restart=always
RestartSec=3
LimitNOFILE=1048576

[Install]
WantedBy=multi-user.target
EOF


# Reload systemd daemon
systemctl daemon-reload

# Enable and start backhaul-shiraz-backup-germany-hetzner-ws
systemctl enable backhaul-shiraz-backup-germany-hetzner-ws.service
systemctl start backhaul-shiraz-backup-germany-hetzner-ws.service

# Enable and start backhaul-shiraz-backup-germany-hetzner-wsmux
systemctl enable backhaul-shiraz-backup-germany-hetzner-wsmux.service
systemctl start backhaul-shiraz-backup-germany-hetzner-wsmux.service


echo "✅ All services installed and started!"
echo ""
echo "Check status with:"
echo "  systemctl status backhaul-shiraz-backup-germany-hetzner-ws"
echo "  systemctl status backhaul-shiraz-backup-germany-hetzner-wsmux"
