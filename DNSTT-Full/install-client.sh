#!/bin/bash

# ============================================================================
# slipstream DNS Tunnel - Client Installation Script
# سرور: ایران
# نصب و راه‌اندازی خودکار slipstream client + WireGuard + SOCKS5
# ============================================================================

set -e  # Exit on error

# رنگ‌ها برای output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================================
# توابع کمکی
# ============================================================================

print_header() {
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "این اسکریپت باید با root اجرا شود"
        exit 1
    fi
}

# ============================================================================
# Main Installation
# ============================================================================

main() {
    print_header "slipstream Client Installation"
    
    check_root
    
    # مرحله 1: بررسی سیستم
    print_info "مرحله 1/10: بررسی سیستم..."
    check_system
    
    # مرحله 2: نصب dependencies
    print_info "مرحله 2/10: نصب dependencies..."
    install_dependencies
    
    # مرحله 3: Build کردن slipstream
    print_info "مرحله 3/10: Build کردن slipstream..."
    build_slipstream
    
    # مرحله 4: تنظیم slipstream config
    print_info "مرحله 4/10: تنظیم slipstream configuration..."
    setup_slipstream_config
    
    # مرحله 5: تنظیم slipstream service
    print_info "مرحله 5/10: تنظیم slipstream service..."
    setup_slipstream_service
    
    # مرحله 6: نصب و تنظیم WireGuard
    print_info "مرحله 6/10: نصب و تنظیم WireGuard..."
    setup_wireguard
    
    # مرحله 7: نصب و تنظیم SOCKS5
    print_info "مرحله 7/10: نصب و تنظیم SOCKS5..."
    setup_socks5
    
    # مرحله 8: تنظیم routing و iptables
    print_info "مرحله 8/10: تنظیم routing و iptables..."
    setup_routing
    
    # مرحله 9: تنظیم firewall
    print_info "مرحله 9/10: تنظیم firewall..."
    setup_firewall
    
    # مرحله 10: اعمال kernel tuning
    print_info "مرحله 10/10: اعمال kernel tuning..."
    apply_tuning
    
    # خلاصه و راهنمای نهایی
    print_final_instructions
}

# ============================================================================
# مرحله 1: بررسی سیستم
# ============================================================================

check_system() {
    # بررسی OS
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
        print_success "OS: $OS $VER"
    else
        print_error "Unable to detect OS"
        exit 1
    fi
    
    # بررسی architecture
    ARCH=$(uname -m)
    print_success "Architecture: $ARCH"
    
    # بررسی kernel version
    KERNEL=$(uname -r)
    print_success "Kernel: $KERNEL"
    
    # بررسی TUN module
    if lsmod | grep -q tun; then
        print_success "TUN module loaded"
    else
        print_warning "Loading TUN module..."
        modprobe tun
    fi
    
    # بررسی RAM
    TOTAL_RAM=$(free -g | awk '/^Mem:/{print $2}')
    print_success "Total RAM: ${TOTAL_RAM}GB"
    
    if [ "$TOTAL_RAM" -lt 4 ]; then
        print_warning "با 500 resolver، توصیه میشه حداقل 4GB RAM داشته باشی"
    fi
}

# ============================================================================
# مرحله 2: نصب Dependencies
# ============================================================================

install_dependencies() {
    print_info "به‌روزرسانی package list..."
    apt-get update -qq
    
    print_info "نصب dependencies..."
    apt-get install -y \
        build-essential \
        git \
        meson \
        ninja-build \
        pkg-config \
        libssl-dev \
        python3 \
        python3-pip \
        curl \
        wget \
        net-tools \
        iptables \
        iptables-persistent \
        wireguard \
        wireguard-tools \
        dante-server \
        qrencode \
        dnsutils \
        iftop \
        nethogs \
        vnstat
    
    print_success "Dependencies نصب شدند"
}

# ============================================================================
# مرحله 3: Build کردن slipstream
# ============================================================================

build_slipstream() {
    cd /opt
    
    # حذف نسخه قبلی اگر وجود داره
    if [ -d "slipstream" ]; then
        print_warning "حذف نسخه قبلی..."
        rm -rf slipstream
    fi
    
    # Clone کردن repository
    print_info "Clone کردن slipstream repository..."
    git clone --recursive https://github.com/EndPositive/slipstream.git
    cd slipstream
    
    # Build
    print_info "Build کردن slipstream (ممکنه چند دقیقه طول بکشه)..."
    meson setup builddir
    meson compile -C builddir
    
    # Install binary
    print_info "نصب binary..."
    cp builddir/slipstream /usr/local/bin/
    chmod +x /usr/local/bin/slipstream
    
    print_success "slipstream build و نصب شد"
}

# ============================================================================
# مرحله 4: تنظیم slipstream Config
# ============================================================================

setup_slipstream_config() {
    # ایجاد directory
    mkdir -p /etc/slipstream
    mkdir -p /var/log
    
    # کپی config
    if [ -f "../configs/client.conf" ]; then
        cp ../configs/client.conf /etc/slipstream/
        print_success "Client config کپی شد"
    fi
    
    if [ -f "../configs/resolvers.txt" ]; then
        cp ../configs/resolvers.txt /etc/slipstream/
        print_success "Resolvers file کپی شد"
    else
        print_error "resolvers.txt پیدا نشد!"
        print_warning "لطفاً فایل resolvers.txt با 500 IP ایجاد کن"
    fi
    
    # Generate private key برای client
    print_info "Generate کردن client private key..."
    CLIENT_PRIV_KEY=$(openssl rand -hex 32)
    sed -i "s/REPLACE_WITH_YOUR_PRIVATE_KEY_HEX_64_CHARS/$CLIENT_PRIV_KEY/g" /etc/slipstream/client.conf
    
    # دریافت اطلاعات سرور
    read -p "IP سرور خارج: " SERVER_IP
    read -p "دامنه DNS (مثل t.irihost.com): " DOMAIN
    read -p "Public key سرور (از سرور خارج): " SERVER_PUB_KEY
    
    # جایگزینی در config
    sed -i "s/SERVER_EXTERNAL_IP/$SERVER_IP/g" /etc/slipstream/client.conf
    sed -i "s/t.irihost.com/$DOMAIN/g" /etc/slipstream/client.conf
    sed -i "s/REPLACE_WITH_SERVER_PUBLIC_KEY_HEX/$SERVER_PUB_KEY/g" /etc/slipstream/client.conf
    
    print_success "Configuration تنظیم شد"
    
    # بررسی تعداد resolvers
    RESOLVER_COUNT=$(grep -v '^#' /etc/slipstream/resolvers.txt | grep -v '^$' | wc -l)
    print_info "تعداد resolvers: $RESOLVER_COUNT"
    
    if [ "$RESOLVER_COUNT" -lt 10 ]; then
        print_error "تعداد resolvers خیلی کمه! حداقل 100 توصیه میشه"
    fi
}

# ============================================================================
# مرحله 5: تنظیم slipstream Service
# ============================================================================

setup_slipstream_service() {
    if [ -f "../configs/slipstream-client.service" ]; then
        cp ../configs/slipstream-client.service /etc/systemd/system/
        print_success "Service file کپی شد"
    fi
    
    # Reload systemd
    systemctl daemon-reload
    
    # Enable service (ولی start نمیکنیم فعلاً)
    systemctl enable slipstream-client
    print_success "Service enabled شد"
}

# ============================================================================
# مرحله 6: تنظیم WireGuard
# ============================================================================

setup_wireguard() {
    mkdir -p /etc/wireguard
    
    # کپی config
    if [ -f "../configs/wg0.conf" ]; then
        cp ../configs/wg0.conf /etc/wireguard/
        print_success "WireGuard config کپی شد"
    fi
    
    # Generate keys برای server
    print_info "Generate کردن WireGuard keys..."
    WG_SERVER_PRIV=$(wg genkey)
    WG_SERVER_PUB=$(echo "$WG_SERVER_PRIV" | wg pubkey)
    
    # جایگزینی در config
    sed -i "s/SERVER_PRIVATE_KEY_REPLACE_ME/$WG_SERVER_PRIV/g" /etc/wireguard/wg0.conf
    
    print_success "WireGuard keys generate شدند"
    print_warning "Server Public Key: $WG_SERVER_PUB"
    print_warning "این کلید رو برای ساخت client config نگه دار"
    
    # Set permissions
    chmod 600 /etc/wireguard/wg0.conf
    
    # Enable WireGuard
    systemctl enable wg-quick@wg0
    print_success "WireGuard enabled شد"
}

# ============================================================================
# مرحله 7: تنظیم SOCKS5
# ============================================================================

setup_socks5() {
    # کپی config
    if [ -f "../configs/danted.conf" ]; then
        cp ../configs/danted.conf /etc/danted.conf
        print_success "SOCKS5 config کپی شد"
    fi
    
    # کپی service file
    if [ -f "../configs/danted.service" ]; then
        cp ../configs/danted.service /etc/systemd/system/
        print_success "SOCKS5 service file کپی شد"
    fi
    
    # Set permissions
    chmod 644 /etc/danted.conf
    
    # Reload systemd
    systemctl daemon-reload
    
    # Enable danted
    systemctl enable danted
    print_success "SOCKS5 enabled شد"
}

# ============================================================================
# مرحله 8: تنظیم Routing
# ============================================================================

setup_routing() {
    # Enable IP forwarding
    print_info "فعال‌سازی IP forwarding..."
    sysctl -w net.ipv4.ip_forward=1
    sysctl -w net.ipv6.conf.all.forwarding=1
    
    # ذخیره permanent
    echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf
    echo "net.ipv6.conf.all.forwarding=1" >> /etc/sysctl.conf
    
    print_success "IP forwarding فعال شد"
}

# ============================================================================
# مرحله 9: تنظیم Firewall
# ============================================================================

setup_firewall() {
    # بررسی ufw
    if command -v ufw &> /dev/null; then
        print_info "تنظیم UFW firewall..."
        ufw allow 51820/udp comment 'WireGuard'
        ufw allow 1080/tcp comment 'SOCKS5'
        print_success "UFW rules اضافه شدند"
    fi
    
    # iptables rules
    print_info "تنظیم iptables..."
    
    # Allow WireGuard
    iptables -A INPUT -p udp --dport 51820 -j ACCEPT
    
    # Allow SOCKS5
    iptables -A INPUT -p tcp --dport 1080 -j ACCEPT
    
    # ذخیره rules
    if command -v netfilter-persistent &> /dev/null; then
        netfilter-persistent save
        print_success "iptables rules ذخیره شدند"
    fi
}

# ============================================================================
# مرحله 10: اعمال Kernel Tuning
# ============================================================================

apply_tuning() {
    # کپی tuning file
    if [ -f "../configs/99-tunnel-tuning.conf" ]; then
        cp ../configs/99-tunnel-tuning.conf /etc/sysctl.d/
        print_success "Tuning file کپی شد"
    fi
    
    # Load BBR module
    print_info "Loading BBR congestion control..."
    modprobe tcp_bbr
    echo "tcp_bbr" >> /etc/modules-load.d/modules.conf
    
    # اعمال تنظیمات
    print_info "اعمال kernel tuning..."
    sysctl --system > /dev/null 2>&1
    
    print_success "Kernel tuning اعمال شد"
}

# ============================================================================
# نمایش دستورالعمل‌های نهایی
# ============================================================================

print_final_instructions() {
    print_header "نصب با موفقیت انجام شد!"
    
    echo ""
    print_success "slipstream client + WireGuard + SOCKS5 آماده هستند"
    echo ""
    
    print_info "دستورات شروع سرویس‌ها:"
    echo ""
    echo "1. شروع slipstream client:"
    echo "   systemctl start slipstream-client"
    echo ""
    echo "2. بررسی tunnel:"
    echo "   ip addr show tun0"
    echo "   ping 10.0.0.1"
    echo ""
    echo "3. شروع WireGuard:"
    echo "   systemctl start wg-quick@wg0"
    echo ""
    echo "4. شروع SOCKS5:"
    echo "   systemctl start danted"
    echo ""
    echo "5. بررسی همه سرویس‌ها:"
    echo "   systemctl status slipstream-client"
    echo "   systemctl status wg-quick@wg0"
    echo "   systemctl status danted"
    echo ""
    
    print_warning "نکات مهم:"
    echo "- قبل از start، مطمئن شو DNS propagate شده (dig @8.8.8.8 DOMAIN)"
    echo "- فایل /etc/slipstream/resolvers.txt رو با 500 IP پر کن"
    echo "- برای ساخت WireGuard client config از add-wg-client.sh استفاده کن"
    echo "- پورت‌های 51820 (WireGuard) و 1080 (SOCKS5) رو باز کن"
    echo ""
    
    print_info "برای تست سرعت:"
    echo "   ./scripts/test-speed.sh"
    echo ""
    
    print_info "برای مانیتورینگ:"
    echo "   ./scripts/monitor.sh"
    echo ""
    
    print_info "برای اضافه کردن کلاینت WireGuard:"
    echo "   ./scripts/add-wg-client.sh"
    echo ""
}

# ============================================================================
# اجرای اسکریپت
# ============================================================================

main "$@"
