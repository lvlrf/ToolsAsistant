#!/bin/bash

# ============================================================================
# Real-time Monitoring Script
# مانیتورینگ real-time تمام سرویس‌ها و interface ها
# ============================================================================

# رنگ‌ها
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# بررسی root
if [[ $EUID -ne 0 ]]; then
    echo -e "${RED}این اسکریپت باید با root اجرا شود${NC}"
    exit 1
fi

# تابع برای نمایش header
show_header() {
    clear
    echo -e "${CYAN}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║      slipstream Tunnel Real-time Monitoring          ║${NC}"
    echo -e "${CYAN}║             $(date '+%Y-%m-%d %H:%M:%S')                    ║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# تابع برای نمایش وضعیت سرویس
show_service_status() {
    echo -e "${BLUE}═══ Service Status ═══${NC}"
    
    services=("slipstream-client" "wg-quick@wg0" "danted")
    
    for service in "${services[@]}"; do
        if systemctl is-active --quiet $service; then
            echo -e "  $service: ${GREEN}●${NC} Running"
        else
            echo -e "  $service: ${RED}●${NC} Stopped"
        fi
    done
    echo ""
}

# تابع برای نمایش interface statistics
show_interface_stats() {
    echo -e "${BLUE}═══ Interface Statistics ═══${NC}"
    
    # tun0
    if ip link show tun0 &>/dev/null; then
        echo -e "${GREEN}tun0 (slipstream tunnel):${NC}"
        ip -s -h link show tun0 | grep -A 2 'RX\|TX' | sed 's/^/  /'
    else
        echo -e "${RED}tun0: DOWN${NC}"
    fi
    
    echo ""
    
    # wg0
    if ip link show wg0 &>/dev/null; then
        echo -e "${GREEN}wg0 (WireGuard):${NC}"
        ip -s -h link show wg0 | grep -A 2 'RX\|TX' | sed 's/^/  /'
        
        # WireGuard peers
        PEER_COUNT=$(wg show wg0 peers 2>/dev/null | wc -l)
        echo -e "  Active peers: $PEER_COUNT"
    else
        echo -e "${RED}wg0: DOWN${NC}"
    fi
    
    echo ""
}

# تابع برای نمایش bandwidth real-time
show_bandwidth() {
    echo -e "${BLUE}═══ Bandwidth (last 1 sec) ═══${NC}"
    
    # استفاده از ifstat اگر نصب است
    if command -v ifstat &> /dev/null; then
        ifstat -i tun0,wg0 1 1 | tail -n 1
    else
        echo -e "${YELLOW}ifstat not installed. Run: apt install ifstat${NC}"
    fi
    
    echo ""
}

# تابع برای نمایش active connections
show_connections() {
    echo -e "${BLUE}═══ Active Connections ═══${NC}"
    
    # slipstream connections
    TUNNEL_CONN=$(netstat -an 2>/dev/null | grep '10.0.0' | grep ESTABLISHED | wc -l)
    echo -e "  Tunnel connections: $TUNNEL_CONN"
    
    # WireGuard connections
    WG_CONN=$(wg show wg0 2>/dev/null | grep -c 'peer:')
    echo -e "  WireGuard peers: $WG_CONN"
    
    # SOCKS5 connections
    SOCKS_CONN=$(netstat -an 2>/dev/null | grep ':1080' | grep ESTABLISHED | wc -l)
    echo -e "  SOCKS5 connections: $SOCKS_CONN"
    
    echo ""
}

# تابع برای نمایش system resources
show_resources() {
    echo -e "${BLUE}═══ System Resources ═══${NC}"
    
    # CPU
    CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    echo -e "  CPU Usage: ${CPU_USAGE}%"
    
    # Memory
    MEM_USED=$(free -h | awk 'NR==2 {print $3}')
    MEM_TOTAL=$(free -h | awk 'NR==2 {print $2}')
    echo -e "  Memory: ${MEM_USED} / ${MEM_TOTAL}"
    
    # Disk
    DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}')
    echo -e "  Disk Usage: ${DISK_USAGE}"
    
    # Load average
    LOAD=$(uptime | awk -F'load average:' '{print $2}' | xargs)
    echo -e "  Load Average: ${LOAD}"
    
    echo ""
}

# تابع برای نمایش recent logs
show_recent_logs() {
    echo -e "${BLUE}═══ Recent Log Entries ═══${NC}"
    
    echo -e "${CYAN}slipstream-client:${NC}"
    journalctl -u slipstream-client -n 2 --no-pager 2>/dev/null | tail -n 2 | sed 's/^/  /'
    
    echo ""
    echo -e "${CYAN}danted:${NC}"
    journalctl -u danted -n 2 --no-pager 2>/dev/null | tail -n 2 | sed 's/^/  /'
    
    echo ""
}

# تابع برای نمایش top processes
show_top_processes() {
    echo -e "${BLUE}═══ Top Network Processes ═══${NC}"
    
    ps aux | awk 'NR==1 || /slipstream|danted|wireguard/' | head -n 6 | sed 's/^/  /'
    
    echo ""
}

# ============================================================================
# حلقه اصلی مانیتورینگ
# ============================================================================

# نصب ابزارهای مورد نیاز اگر نصب نیستن
if ! command -v ifstat &> /dev/null; then
    echo "Installing ifstat..."
    apt-get install -y ifstat > /dev/null 2>&1
fi

# متغیر برای refresh rate
REFRESH_RATE=2

echo -e "${GREEN}Starting monitor... (Press Ctrl+C to exit)${NC}"
echo -e "${YELLOW}Refresh rate: ${REFRESH_RATE} seconds${NC}"
sleep 2

# حلقه بی‌نهایت
while true; do
    show_header
    show_service_status
    show_interface_stats
    show_bandwidth
    show_connections
    show_resources
    show_recent_logs
    show_top_processes
    
    echo -e "${CYAN}══════════════════════════════════════════════════${NC}"
    echo -e "${YELLOW}Refreshing in ${REFRESH_RATE}s... (Ctrl+C to exit)${NC}"
    
    sleep $REFRESH_RATE
done
