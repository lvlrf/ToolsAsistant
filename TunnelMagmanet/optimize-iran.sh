#!/bin/bash
# Backhaul Optimization Script - IRAN Server
# This script optimizes network and system settings for Iran servers

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

BACKUP_DIR="/root/backhaul-core/backup"
SYSCTL_PATH="/etc/sysctl.conf"
PROF_PATH="/etc/profile"

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}Backhaul Iran Server Optimization${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}This script must be run as root${NC}" 
   exit 1
fi

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup existing configurations
echo -e "${YELLOW}Creating backups...${NC}"
if [ -f "$SYSCTL_PATH" ]; then
    cp "$SYSCTL_PATH" "$BACKUP_DIR/sysctl.conf.backup.$(date +%Y%m%d_%H%M%S)"
    echo -e "${GREEN}[OK] Backed up sysctl.conf${NC}"
fi

if [ -f "$PROF_PATH" ]; then
    cp "$PROF_PATH" "$BACKUP_DIR/profile.backup.$(date +%Y%m%d_%H%M%S)"
    echo -e "${GREEN}[OK] Backed up profile${NC}"
fi
echo ""

# Network Optimizations
echo -e "${YELLOW}Applying network optimizations...${NC}"
echo ""

# Remove old backhaul-related settings
sed -i \
    -e '/fs.file-max/d' \
    -e '/net.core.default_qdisc/d' \
    -e '/net.core.netdev_max_backlog/d' \
    -e '/net.core.optmem_max/d' \
    -e '/net.core.somaxconn/d' \
    -e '/net.core.rmem_max/d' \
    -e '/net.core.rmem_default/d' \
    -e '/net.core.wmem_max/d' \
    -e '/net.core.wmem_default/d' \
    -e '/net.ipv4.tcp_rmem/d' \
    -e '/net.ipv4.tcp_wmem/d' \
    -e '/net.ipv4.tcp_congestion_control/d' \
    -e '/net.ipv4.tcp_fastopen/d' \
    -e '/net.ipv4.tcp_fin_timeout/d' \
    -e '/net.ipv4.tcp_keepalive_time/d' \
    -e '/net.ipv4.tcp_keepalive_probes/d' \
    -e '/net.ipv4.tcp_keepalive_intvl/d' \
    -e '/net.ipv4.tcp_max_orphans/d' \
    -e '/net.ipv4.tcp_max_syn_backlog/d' \
    -e '/net.ipv4.tcp_max_tw_buckets/d' \
    -e '/net.ipv4.tcp_mem/d' \
    -e '/net.ipv4.tcp_mtu_probing/d' \
    -e '/net.ipv4.tcp_notsent_lowat/d' \
    -e '/net.ipv4.tcp_retries2/d' \
    -e '/net.ipv4.tcp_sack/d' \
    -e '/net.ipv4.tcp_dsack/d' \
    -e '/net.ipv4.tcp_slow_start_after_idle/d' \
    -e '/net.ipv4.tcp_window_scaling/d' \
    -e '/net.ipv4.tcp_adv_win_scale/d' \
    -e '/net.ipv4.tcp_ecn/d' \
    -e '/net.ipv4.tcp_ecn_fallback/d' \
    -e '/net.ipv4.tcp_syncookies/d' \
    -e '/net.ipv4.udp_mem/d' \
    -e '/net.ipv6.conf.all.disable_ipv6/d' \
    -e '/net.ipv6.conf.default.disable_ipv6/d' \
    -e '/net.ipv6.conf.lo.disable_ipv6/d' \
    -e '/net.unix.max_dgram_qlen/d' \
    -e '/vm.min_free_kbytes/d' \
    -e '/vm.swappiness/d' \
    -e '/vm.vfs_cache_pressure/d' \
    -e '/net.ipv4.conf.default.rp_filter/d' \
    -e '/net.ipv4.conf.all.rp_filter/d' \
    -e '/net.ipv4.conf.all.accept_source_route/d' \
    -e '/net.ipv4.conf.default.accept_source_route/d' \
    -e '/net.ipv4.neigh.default.gc_thresh1/d' \
    -e '/net.ipv4.neigh.default.gc_thresh2/d' \
    -e '/net.ipv4.neigh.default.gc_thresh3/d' \
    -e '/net.ipv4.neigh.default.gc_stale_time/d' \
    -e '/net.ipv4.conf.default.arp_announce/d' \
    -e '/net.ipv4.conf.lo.arp_announce/d' \
    -e '/net.ipv4.conf.all.arp_announce/d' \
    -e '/kernel.panic/d' \
    -e '/vm.dirty_ratio/d' \
    -e '/^#/d' \
    -e '/^$/d' \
    "$SYSCTL_PATH"

# Apply optimizations for Iran (high connection count)
cat <<EOF >> "$SYSCTL_PATH"

# Backhaul Optimizations - Iran Server
# Applied: $(date)

# File System
fs.file-max = 67108864

# Network Core Settings
net.core.default_qdisc = fq_codel
net.core.netdev_max_backlog = 32768
net.core.optmem_max = 262144
net.core.somaxconn = 65536
net.core.rmem_max = 33554432
net.core.rmem_default = 1048576
net.core.wmem_max = 33554432
net.core.wmem_default = 1048576

# TCP Settings
net.ipv4.tcp_rmem = 16384 1048576 33554432
net.ipv4.tcp_wmem = 16384 1048576 33554432
net.ipv4.tcp_congestion_control = bbr
net.ipv4.tcp_fastopen = 3
net.ipv4.tcp_fin_timeout = 25
net.ipv4.tcp_keepalive_time = 1200
net.ipv4.tcp_keepalive_probes = 7
net.ipv4.tcp_keepalive_intvl = 30
net.ipv4.tcp_max_orphans = 819200
net.ipv4.tcp_max_syn_backlog = 20480
net.ipv4.tcp_max_tw_buckets = 1440000
net.ipv4.tcp_mem = 65536 1048576 33554432
net.ipv4.tcp_mtu_probing = 1
net.ipv4.tcp_notsent_lowat = 32768
net.ipv4.tcp_retries2 = 8
net.ipv4.tcp_sack = 1
net.ipv4.tcp_dsack = 1
net.ipv4.tcp_slow_start_after_idle = 0
net.ipv4.tcp_window_scaling = 1
net.ipv4.tcp_adv_win_scale = -2
net.ipv4.tcp_ecn = 1
net.ipv4.tcp_ecn_fallback = 1
net.ipv4.tcp_syncookies = 1

# UDP Settings
net.ipv4.udp_mem = 65536 1048576 33554432

# IPv6
net.ipv6.conf.all.disable_ipv6 = 0
net.ipv6.conf.default.disable_ipv6 = 0
net.ipv6.conf.lo.disable_ipv6 = 0

# Unix Domain Sockets
net.unix.max_dgram_qlen = 256

# Virtual Memory
vm.min_free_kbytes = 65536
vm.swappiness = 10
vm.vfs_cache_pressure = 250
vm.dirty_ratio = 20

# Routing
net.ipv4.conf.default.rp_filter = 2
net.ipv4.conf.all.rp_filter = 2
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.default.accept_source_route = 0

# Neighbor Table
net.ipv4.neigh.default.gc_thresh1 = 512
net.ipv4.neigh.default.gc_thresh2 = 2048
net.ipv4.neigh.default.gc_thresh3 = 16384
net.ipv4.neigh.default.gc_stale_time = 60

# ARP
net.ipv4.conf.default.arp_announce = 2
net.ipv4.conf.lo.arp_announce = 2
net.ipv4.conf.all.arp_announce = 2

# Kernel
kernel.panic = 1
EOF

echo -e "${GREEN}[OK] Network settings configured${NC}"
echo ""

# Apply sysctl settings
echo -e "${YELLOW}Applying sysctl settings...${NC}"
sysctl -p
echo ""

# System Limits Optimizations
echo -e "${YELLOW}Optimizing system limits...${NC}"
echo ""

# Remove old ulimit settings
sed -i \
    -e '/ulimit -c/d' \
    -e '/ulimit -d/d' \
    -e '/ulimit -f/d' \
    -e '/ulimit -i/d' \
    -e '/ulimit -l/d' \
    -e '/ulimit -m/d' \
    -e '/ulimit -n/d' \
    -e '/ulimit -q/d' \
    -e '/ulimit -s/d' \
    -e '/ulimit -t/d' \
    -e '/ulimit -u/d' \
    -e '/ulimit -v/d' \
    -e '/ulimit -x/d' \
    "$PROF_PATH"

# Apply new ulimit settings
cat <<EOF >> "$PROF_PATH"

# Backhaul System Limits
ulimit -c unlimited
ulimit -d unlimited
ulimit -f unlimited
ulimit -i unlimited
ulimit -l unlimited
ulimit -m unlimited
ulimit -n 1048576
ulimit -q unlimited
ulimit -s -H 65536
ulimit -s 32768
ulimit -t unlimited
ulimit -u unlimited
ulimit -v unlimited
ulimit -x unlimited
EOF

echo -e "${GREEN}[OK] System limits configured${NC}"
echo ""

# Enable BBR
echo -e "${YELLOW}Enabling BBR congestion control...${NC}"
modprobe tcp_bbr
echo "tcp_bbr" > /etc/modules-load.d/bbr.conf
echo -e "${GREEN}[OK] BBR enabled${NC}"
echo ""

echo -e "${CYAN}========================================${NC}"
echo -e "${GREEN}Optimization completed successfully!${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""
echo -e "${YELLOW}Backups saved to: ${BACKUP_DIR}${NC}"
echo ""
echo -e "${RED}IMPORTANT: Please reboot the server for all changes to take effect.${NC}"
echo ""

read -p "Do you want to reboot now? (yes/no): " reboot_choice
if [ "$reboot_choice" == "yes" ]; then
    echo -e "${YELLOW}Rebooting in 5 seconds...${NC}"
    sleep 5
    reboot
else
    echo -e "${YELLOW}Please reboot manually later.${NC}"
fi
