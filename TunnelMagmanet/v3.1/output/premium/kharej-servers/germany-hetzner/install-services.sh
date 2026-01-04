#!/bin/bash
# Backhaul PREMIUM - KHAREJ Server: germany-hetzner
# Generated: 2026-01-03 13:37:04

echo "Installing Backhaul services for germany-hetzner..."


cat > /etc/systemd/system/backhaul-germany-hetzner-shiraz-backup-tcp.service << 'EOF'
[Unit]
Description=Backhaul Kharej shiraz-backup <- germany-hetzner (TCP) Port 111
After=network.target

[Service]
Type=simple
ExecStart=/root/backhaul-core/backhaul_premium -c /root/config-shiraz-backup-tcp.toml
Restart=always
RestartSec=3
LimitNOFILE=1048576

[Install]
WantedBy=multi-user.target
EOF


cat > /etc/systemd/system/backhaul-germany-hetzner-shiraz-backup-udp.service << 'EOF'
[Unit]
Description=Backhaul Kharej shiraz-backup <- germany-hetzner (UDP) Port 112
After=network.target

[Service]
Type=simple
ExecStart=/root/backhaul-core/backhaul_premium -c /root/config-shiraz-backup-udp.toml
Restart=always
RestartSec=3
LimitNOFILE=1048576

[Install]
WantedBy=multi-user.target
EOF


# Reload systemd daemon
systemctl daemon-reload

# Enable and start backhaul-germany-hetzner-shiraz-backup-tcp
systemctl enable backhaul-germany-hetzner-shiraz-backup-tcp.service
systemctl start backhaul-germany-hetzner-shiraz-backup-tcp.service

# Enable and start backhaul-germany-hetzner-shiraz-backup-udp
systemctl enable backhaul-germany-hetzner-shiraz-backup-udp.service
systemctl start backhaul-germany-hetzner-shiraz-backup-udp.service


echo "✅ All services installed and started!"
echo ""
echo "Check status with:"
echo "  systemctl status backhaul-germany-hetzner-shiraz-backup-tcp"
echo "  systemctl status backhaul-germany-hetzner-shiraz-backup-udp"
