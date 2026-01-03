#!/bin/bash
# Backhaul STANDARD - KHAREJ Server: germany-hetzner
# Generated: 2026-01-03 13:37:04

echo "Installing Backhaul services for germany-hetzner..."


cat > /etc/systemd/system/backhaul-germany-hetzner-shiraz-backup-ws.service << 'EOF'
[Unit]
Description=Backhaul Kharej shiraz-backup <- germany-hetzner (WS) Port 109
After=network.target

[Service]
Type=simple
ExecStart=/root/backhaul -c /root/config-shiraz-backup-ws.toml
Restart=always
RestartSec=3
LimitNOFILE=1048576

[Install]
WantedBy=multi-user.target
EOF


cat > /etc/systemd/system/backhaul-germany-hetzner-shiraz-backup-wsmux.service << 'EOF'
[Unit]
Description=Backhaul Kharej shiraz-backup <- germany-hetzner (WSMUX) Port 110
After=network.target

[Service]
Type=simple
ExecStart=/root/backhaul -c /root/config-shiraz-backup-wsmux.toml
Restart=always
RestartSec=3
LimitNOFILE=1048576

[Install]
WantedBy=multi-user.target
EOF


# Reload systemd daemon
systemctl daemon-reload

# Enable and start backhaul-germany-hetzner-shiraz-backup-ws
systemctl enable backhaul-germany-hetzner-shiraz-backup-ws.service
systemctl start backhaul-germany-hetzner-shiraz-backup-ws.service

# Enable and start backhaul-germany-hetzner-shiraz-backup-wsmux
systemctl enable backhaul-germany-hetzner-shiraz-backup-wsmux.service
systemctl start backhaul-germany-hetzner-shiraz-backup-wsmux.service


echo "✅ All services installed and started!"
echo ""
echo "Check status with:"
echo "  systemctl status backhaul-germany-hetzner-shiraz-backup-ws"
echo "  systemctl status backhaul-germany-hetzner-shiraz-backup-wsmux"
