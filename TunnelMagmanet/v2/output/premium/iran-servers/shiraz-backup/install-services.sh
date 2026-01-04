#!/bin/bash
# Backhaul PREMIUM - IRAN Server: shiraz-backup
# Generated: 2026-01-03 13:37:04

echo "Installing Backhaul services for shiraz-backup..."


cat > /etc/systemd/system/backhaul-shiraz-backup-germany-hetzner-tcp.service << 'EOF'
[Unit]
Description=Backhaul Iran shiraz-backup -> germany-hetzner (TCP) Port 111
After=network.target

[Service]
Type=simple
ExecStart=/root/backhaul-core/backhaul_premium -c /root/config-germany-hetzner-tcp.toml
Restart=always
RestartSec=3
LimitNOFILE=1048576

[Install]
WantedBy=multi-user.target
EOF


cat > /etc/systemd/system/backhaul-shiraz-backup-germany-hetzner-udp.service << 'EOF'
[Unit]
Description=Backhaul Iran shiraz-backup -> germany-hetzner (UDP) Port 112
After=network.target

[Service]
Type=simple
ExecStart=/root/backhaul-core/backhaul_premium -c /root/config-germany-hetzner-udp.toml
Restart=always
RestartSec=3
LimitNOFILE=1048576

[Install]
WantedBy=multi-user.target
EOF


# Reload systemd daemon
systemctl daemon-reload

# Enable and start backhaul-shiraz-backup-germany-hetzner-tcp
systemctl enable backhaul-shiraz-backup-germany-hetzner-tcp.service
systemctl start backhaul-shiraz-backup-germany-hetzner-tcp.service

# Enable and start backhaul-shiraz-backup-germany-hetzner-udp
systemctl enable backhaul-shiraz-backup-germany-hetzner-udp.service
systemctl start backhaul-shiraz-backup-germany-hetzner-udp.service


echo "✅ All services installed and started!"
echo ""
echo "Check status with:"
echo "  systemctl status backhaul-shiraz-backup-germany-hetzner-tcp"
echo "  systemctl status backhaul-shiraz-backup-germany-hetzner-udp"
