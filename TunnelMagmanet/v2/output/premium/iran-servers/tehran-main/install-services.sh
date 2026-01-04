#!/bin/bash
# Backhaul PREMIUM - IRAN Server: tehran-main
# Generated: 2026-01-03 13:37:04

echo "Installing Backhaul services for tehran-main..."


cat > /etc/systemd/system/backhaul-tehran-main-france-ovh-tcpmux.service << 'EOF'
[Unit]
Description=Backhaul Iran tehran-main -> france-ovh (TCPMUX) Port 107
After=network.target

[Service]
Type=simple
ExecStart=/root/backhaul-core/backhaul_premium -c /root/config-france-ovh-tcpmux.toml
Restart=always
RestartSec=3
LimitNOFILE=1048576

[Install]
WantedBy=multi-user.target
EOF


cat > /etc/systemd/system/backhaul-tehran-main-france-ovh-uwsmux.service << 'EOF'
[Unit]
Description=Backhaul Iran tehran-main -> france-ovh (UWSMUX) Port 108
After=network.target

[Service]
Type=simple
ExecStart=/root/backhaul-core/backhaul_premium -c /root/config-france-ovh-uwsmux.toml
Restart=always
RestartSec=3
LimitNOFILE=1048576

[Install]
WantedBy=multi-user.target
EOF


# Reload systemd daemon
systemctl daemon-reload

# Enable and start backhaul-tehran-main-france-ovh-tcpmux
systemctl enable backhaul-tehran-main-france-ovh-tcpmux.service
systemctl start backhaul-tehran-main-france-ovh-tcpmux.service

# Enable and start backhaul-tehran-main-france-ovh-uwsmux
systemctl enable backhaul-tehran-main-france-ovh-uwsmux.service
systemctl start backhaul-tehran-main-france-ovh-uwsmux.service


echo "✅ All services installed and started!"
echo ""
echo "Check status with:"
echo "  systemctl status backhaul-tehran-main-france-ovh-tcpmux"
echo "  systemctl status backhaul-tehran-main-france-ovh-uwsmux"
