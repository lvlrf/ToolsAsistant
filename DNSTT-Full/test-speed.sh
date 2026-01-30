#!/bin/bash

# ============================================================================
# Speed Test Script for slipstream DNS Tunnel
# تست سرعت و پهنای باند tunnel
# ============================================================================

# رنگ‌ها
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# بررسی root
if [[ $EUID -ne 0 ]]; then
    print_error "این اسکریپت باید با root اجرا شود"
    exit 1
fi

clear
print_header "slipstream Tunnel Speed Test"

# ============================================================================
# تست 1: Ping Test
# ============================================================================

print_info "Test 1: Ping Test (Latency)"
echo ""

# Ping به gateway
print_info "Ping به tunnel gateway (10.0.0.1)..."
if ping -c 5 -W 2 10.0.0.1 > /tmp/ping_gateway.txt 2>&1; then
    AVG_RTT=$(grep 'rtt' /tmp/ping_gateway.txt | awk -F'/' '{print $5}')
    print_success "Average RTT: ${AVG_RTT}ms"
else
    print_error "Ping به gateway failed!"
    cat /tmp/ping_gateway.txt
fi

echo ""

# Ping به external (Google DNS)
print_info "Ping به external (8.8.8.8) از طریق tunnel..."
if ping -c 5 -W 2 -I tun0 8.8.8.8 > /tmp/ping_external.txt 2>&1; then
    AVG_RTT_EXT=$(grep 'rtt' /tmp/ping_external.txt | awk -F'/' '{print $5}')
    print_success "Average RTT to 8.8.8.8: ${AVG_RTT_EXT}ms"
else
    print_error "Ping به external failed!"
fi

echo ""

# ============================================================================
# تست 2: DNS Query Test
# ============================================================================

print_info "Test 2: DNS Query Speed"
echo ""

print_info "تست سرعت DNS query از طریق tunnel..."
START=$(date +%s.%N)
for i in {1..10}; do
    dig @10.0.0.1 google.com +short > /dev/null 2>&1
done
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
AVG=$(echo "scale=3; $DIFF / 10" | bc)
print_success "Average DNS query time: ${AVG}s (10 queries)"

echo ""

# ============================================================================
# تست 3: Bandwidth Test (iperf3)
# ============================================================================

print_info "Test 3: Bandwidth Test"
echo ""

# چک کن iperf3 نصب است
if ! command -v iperf3 &> /dev/null; then
    print_info "نصب iperf3..."
    apt-get install -y iperf3 > /dev/null 2>&1
fi

print_info "برای تست bandwidth، روی سرور خارج iperf3 server راه بیندازید:"
echo "  iperf3 -s"
echo ""

read -p "IP سرور iperf (یا Enter برای skip): " IPERF_SERVER

if [ ! -z "$IPERF_SERVER" ]; then
    print_info "Running iperf3 client..."
    iperf3 -c $IPERF_SERVER -t 30 -i 5 -B 10.0.0.2
else
    print_info "Bandwidth test skipped"
fi

echo ""

# ============================================================================
# تست 4: HTTP Download Speed
# ============================================================================

print_info "Test 4: HTTP Download Speed"
echo ""

print_info "دانلود یک فایل نمونه از طریق tunnel..."
curl -o /tmp/testfile -s -w "\nDownload Speed: %{speed_download} bytes/sec\nTotal Time: %{time_total}s\n" \
    --interface tun0 http://speedtest.tele2.net/1MB.zip

FILE_SIZE=$(stat -f%z /tmp/testfile 2>/dev/null || stat -c%s /tmp/testfile)
print_success "Downloaded: $(echo "scale=2; $FILE_SIZE / 1024 / 1024" | bc)MB"
rm -f /tmp/testfile

echo ""

# ============================================================================
# تست 5: Interface Statistics
# ============================================================================

print_info "Test 5: Interface Statistics"
echo ""

print_info "آمار interface tun0:"
ip -s link show tun0 | grep -A 1 'RX\|TX'

echo ""

# ============================================================================
# تست 6: Active Connections
# ============================================================================

print_info "Test 6: Active Connections"
echo ""

print_info "تعداد connection های فعال:"
CONN_COUNT=$(netstat -an | grep ESTABLISHED | grep '10.0.0' | wc -l)
print_success "Active connections: $CONN_COUNT"

echo ""

# ============================================================================
# تست 7: Resolver Statistics (اگر slipstream log میده)
# ============================================================================

print_info "Test 7: Resolver Statistics"
echo ""

if [ -f "/var/log/slipstream-client.log" ]; then
    print_info "آخرین 10 خط از log:"
    tail -n 10 /var/log/slipstream-client.log
else
    print_info "Log file پیدا نشد. برای دیدن logs:"
    echo "  journalctl -u slipstream-client -n 50"
fi

echo ""

# ============================================================================
# خلاصه نتایج
# ============================================================================

print_header "Summary"
echo ""

if [ ! -z "$AVG_RTT" ]; then
    echo "Gateway Latency: ${AVG_RTT}ms"
fi

if [ ! -z "$AVG_RTT_EXT" ]; then
    echo "External Latency: ${AVG_RTT_EXT}ms"
fi

echo "DNS Query Time: ${AVG}s"
echo "Active Connections: $CONN_COUNT"

echo ""
print_info "برای مانیتورینگ real-time:"
echo "  ./monitor.sh"
echo ""
print_info "برای تست عمیق‌تر:"
echo "  - iperf3 برای bandwidth دقیق"
echo "  - speedtest-cli برای تست سرعت اینترنت"
echo "  - mtr برای traceroute دقیق"
echo ""
