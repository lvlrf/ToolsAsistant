#!/bin/bash
# Backhaul PREMIUM - KHAREJ Server: france-ovh
# Generated: 2026-01-03 13:37:04

echo "Installing Backhaul services for france-ovh..."


cat > /etc/systemd/system/backhaul-france-ovh-tehran-main-tcpmux.service << 'EOF'
[Unit]
Description=Backhaul Kharej tehran-main <- france-ovh (TCPMUX) Port 107
After=network.target

[Service]
Type=simple
ExecStart=/root/backhaul-core/backhaul_premium -c /root/config-tehran-main-tcpmux.toml
Restart=always
RestartSec=3
LimitNOFILE=1048576

[Install]
WantedBy=multi-user.target
EOF


cat > /etc/systemd/system/backhaul-france-ovh-tehran-main-uwsmux.service << 'EOF'
[Unit]
Description=Backhaul Kharej tehran-main <- france-ovh (UWSMUX) Port 108
After=network.target

[Service]
Type=simple
ExecStart=/root/backhaul-core/backhaul_premium -c /root/config-tehran-main-uwsmux.toml
Restart=always
RestartSec=3
LimitNOFILE=1048576

[Install]
WantedBy=multi-user.target
EOF


# Reload systemd daemon
systemctl daemon-reload

# Enable and start backhaul-france-ovh-tehran-main-tcpmux
systemctl enable backhaul-france-ovh-tehran-main-tcpmux.service
systemctl start backhaul-france-ovh-tehran-main-tcpmux.service

# Enable and start backhaul-france-ovh-tehran-main-uwsmux
systemctl enable backhaul-france-ovh-tehran-main-uwsmux.service
systemctl start backhaul-france-ovh-tehran-main-uwsmux.service


echo "✅ All services installed and started!"
echo ""
echo "Check status with:"
echo "  systemctl status backhaul-france-ovh-tehran-main-tcpmux"
echo "  systemctl status backhaul-france-ovh-tehran-main-uwsmux"
