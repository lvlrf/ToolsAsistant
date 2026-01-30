#!/bin/bash

# ============================================================================
# Automatic Troubleshooting Script
# عیب‌یابی خودکار مشکلات رایج
# ============================================================================

# رنگ‌ها
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Counter برای مشکلات
ISSUES_FOUND=0

print_header() {
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================${NC}"
}

print_check() {
    echo -e "${CYAN}🔍 $1${NC}"
}

print_ok() {
    echo -e "${GREEN}  ✓ $1${NC}"
}

print_issue() {
    echo -e "${RED}  ✗ $1${NC}"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
}

print_warning() {
    echo -e "${YELLOW}  ⚠ $1${NC}"
}

print_fix() {
    echo -e "${GREEN}  → $1${NC}"
}

# بررسی root
if [[ $EUID -ne 0 ]]; then
    echo -e "${RED}این اسکریپت باید با root اجرا شود${NC}"
    exit 1
fi

clear
print_header "Automatic Troubleshooting"
echo ""

# ============================================================================
# بررسی 1: Services Status
# ============================================================================

print_check "Checking services status..."
echo ""

# slipstream-client
if systemctl is-active --quiet slipstream-client; then
    print_ok "slipstream-client is running"
else
    print_issue "slipstream-client is NOT running"
    print_fix "systemctl start slipstream-client"
    print_fix "journalctl -u slipstream-client -n 50"
fi

# wg-quick@wg0
if systemctl is-active --quiet wg-quick@wg0; then
    print_ok "WireGuard is running"
else
    print_issue "WireGuard is NOT running"
    print_fix "systemctl start wg-quick@wg0"
    print_fix "journalctl -u wg-quick@wg0 -n 50"
fi

# danted
if systemctl is-active --quiet danted; then
    print_ok "SOCKS5 (danted) is running"
else
    print_issue "SOCKS5 (danted) is NOT running"
    print_fix "systemctl start danted"
    print_fix "journalctl -u danted -n 50"
fi

echo ""

# ============================================================================
# بررسی 2: Network Interfaces
# ============================================================================

print_check "Checking network interfaces..."
echo ""

# tun0
if ip link show tun0 &>/dev/null; then
    if ip addr show tun0 | grep -q '10.0.0.2'; then
        print_ok "tun0 is UP with correct IP"
    else
        print_issue "tun0 is UP but IP is wrong"
        print_fix "Check /etc/slipstream/client.conf"
        print_fix "Restart slipstream-client"
    fi
else
    print_issue "tun0 interface NOT found"
    print_fix "Check if slipstream-client is running"
    print_fix "Check TUN kernel module: lsmod | grep tun"
    print_fix "Load TUN module: modprobe tun"
fi

# wg0
if ip link show wg0 &>/dev/null; then
    if ip addr show wg0 | grep -q '10.8.0.1'; then
        print_ok "wg0 is UP with correct IP"
    else
        print_issue "wg0 is UP but IP is wrong"
    fi
else
    print_issue "wg0 interface NOT found"
    print_fix "Check if WireGuard is running"
fi

echo ""

# ============================================================================
# بررسی 3: DNS Connectivity
# ============================================================================

print_check "Checking DNS connectivity..."
echo ""

# Ping به gateway
if ping -c 2 -W 2 10.0.0.1 &>/dev/null; then
    print_ok "Can ping tunnel gateway (10.0.0.1)"
else
    print_issue "Cannot ping tunnel gateway"
    print_fix "Check slipstream-client service"
    print_fix "Check /etc/slipstream/client.conf"
fi

# DNS resolution
DOMAIN=$(grep server_domain /etc/slipstream/client.conf 2>/dev/null | awk '{print $3}' | tr -d '"' | tr -d ',' || echo "unknown")
if [ "$DOMAIN" != "unknown" ]; then
    if dig +short @8.8.8.8 $DOMAIN NS &>/dev/null; then
        print_ok "DNS records exist for $DOMAIN"
    else
        print_issue "DNS records NOT found for $DOMAIN"
        print_fix "Check DNS configuration"
        print_fix "Run: ./scripts/setup-dns.sh"
    fi
fi

echo ""

# ============================================================================
# بررسی 4: Configuration Files
# ============================================================================

print_check "Checking configuration files..."
echo ""

CONFIG_FILES=(
    "/etc/slipstream/client.conf"
    "/etc/slipstream/resolvers.txt"
    "/etc/wireguard/wg0.conf"
    "/etc/danted.conf"
)

for conf in "${CONFIG_FILES[@]}"; do
    if [ -f "$conf" ]; then
        print_ok "Found: $conf"
    else
        print_issue "Missing: $conf"
    fi
done

# بررسی تعداد resolvers
if [ -f "/etc/slipstream/resolvers.txt" ]; then
    RESOLVER_COUNT=$(grep -v '^#' /etc/slipstream/resolvers.txt | grep -v '^$' | wc -l)
    if [ "$RESOLVER_COUNT" -lt 10 ]; then
        print_issue "Only $RESOLVER_COUNT resolvers found (توصیه: حداقل 100)"
        print_fix "Add more resolvers to /etc/slipstream/resolvers.txt"
    else
        print_ok "$RESOLVER_COUNT resolvers configured"
    fi
fi

echo ""

# ============================================================================
# بررسی 5: Firewall Rules
# ============================================================================

print_check "Checking firewall rules..."
echo ""

# Check iptables NAT
if iptables -t nat -L POSTROUTING -n | grep -q '10.8.0.0/24'; then
    print_ok "NAT rule exists for WireGuard"
else
    print_issue "NAT rule for WireGuard NOT found"
    print_fix "iptables -t nat -A POSTROUTING -s 10.8.0.0/24 -o tun0 -j MASQUERADE"
fi

# Check IP forwarding
IP_FORWARD=$(sysctl -n net.ipv4.ip_forward)
if [ "$IP_FORWARD" == "1" ]; then
    print_ok "IP forwarding is enabled"
else
    print_issue "IP forwarding is DISABLED"
    print_fix "sysctl -w net.ipv4.ip_forward=1"
    print_fix "echo 'net.ipv4.ip_forward=1' >> /etc/sysctl.conf"
fi

echo ""

# ============================================================================
# بررسی 6: Port Availability
# ============================================================================

print_check "Checking port availability..."
echo ""

PORTS=("51820:udp:WireGuard" "1080:tcp:SOCKS5")

for port_info in "${PORTS[@]}"; do
    IFS=':' read -r port proto service <<< "$port_info"
    
    if [ "$proto" == "udp" ]; then
        if netstat -ulpn 2>/dev/null | grep -q ":$port "; then
            print_ok "$service listening on $proto/$port"
        else
            print_issue "$service NOT listening on $proto/$port"
        fi
    else
        if netstat -tlpn 2>/dev/null | grep -q ":$port "; then
            print_ok "$service listening on $proto/$port"
        else
            print_issue "$service NOT listening on $proto/$port"
        fi
    fi
done

echo ""

# ============================================================================
# بررسی 7: System Resources
# ============================================================================

print_check "Checking system resources..."
echo ""

# Memory
MEM_USAGE=$(free | awk 'NR==2 {printf "%.0f", $3*100/$2}')
if [ "$MEM_USAGE" -gt 90 ]; then
    print_issue "High memory usage: ${MEM_USAGE}%"
    print_fix "Consider adding more RAM or reducing resolver count"
elif [ "$MEM_USAGE" -gt 80 ]; then
    print_warning "Memory usage is high: ${MEM_USAGE}%"
else
    print_ok "Memory usage: ${MEM_USAGE}%"
fi

# Disk space
DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | tr -d '%')
if [ "$DISK_USAGE" -gt 90 ]; then
    print_issue "Low disk space: ${DISK_USAGE}% used"
    print_fix "Free up disk space"
elif [ "$DISK_USAGE" -gt 80 ]; then
    print_warning "Disk space is low: ${DISK_USAGE}% used"
else
    print_ok "Disk space: ${DISK_USAGE}% used"
fi

echo ""

# ============================================================================
# بررسی 8: Kernel Modules
# ============================================================================

print_check "Checking kernel modules..."
echo ""

MODULES=("tun" "wireguard" "tcp_bbr")

for module in "${MODULES[@]}"; do
    if lsmod | grep -q "^$module"; then
        print_ok "$module module loaded"
    else
        print_issue "$module module NOT loaded"
        print_fix "modprobe $module"
    fi
done

echo ""

# ============================================================================
# بررسی 9: Recent Errors in Logs
# ============================================================================

print_check "Checking for recent errors in logs..."
echo ""

SERVICES_TO_CHECK=("slipstream-client" "wg-quick@wg0" "danted")

for service in "${SERVICES_TO_CHECK[@]}"; do
    ERROR_COUNT=$(journalctl -u $service --since "1 hour ago" -p err -q | wc -l)
    
    if [ "$ERROR_COUNT" -gt 0 ]; then
        print_issue "$service has $ERROR_COUNT errors in last hour"
        print_fix "journalctl -u $service -p err -n 10"
    else
        print_ok "$service has no errors in last hour"
    fi
done

echo ""

# ============================================================================
# بررسی 10: Connectivity Test
# ============================================================================

print_check "Testing external connectivity..."
echo ""

# Test via tunnel
if curl -s --max-time 5 --interface tun0 ifconfig.me &>/dev/null; then
    print_ok "Can reach internet via tunnel"
    EXTERNAL_IP=$(curl -s --max-time 5 --interface tun0 ifconfig.me)
    echo -e "${CYAN}     External IP: $EXTERNAL_IP${NC}"
else
    print_issue "Cannot reach internet via tunnel"
    print_fix "Check routing and NAT rules"
fi

echo ""

# ============================================================================
# خلاصه نتایج
# ============================================================================

print_header "Troubleshooting Complete"
echo ""

if [ $ISSUES_FOUND -eq 0 ]; then
    echo -e "${GREEN}✓ No issues found! Everything looks good.${NC}"
else
    echo -e "${RED}✗ Found $ISSUES_FOUND issue(s)${NC}"
    echo -e "${YELLOW}Please review the errors above and apply suggested fixes.${NC}"
fi

echo ""
echo -e "${CYAN}For detailed logs:${NC}"
echo "  journalctl -u slipstream-client -f"
echo "  journalctl -u wg-quick@wg0 -f"
echo "  journalctl -u danted -f"
echo ""
echo -e "${CYAN}For manual testing:${NC}"
echo "  ./scripts/test-speed.sh"
echo "  ./scripts/monitor.sh"
echo ""
