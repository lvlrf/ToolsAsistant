#!/bin/bash

# ============================================================================
# slipstream DNS Tunnel - Server Installation Script
# سرور: خارج از ایران
# نصب و راه‌اندازی خودکار slipstream server
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
    print_header "slipstream Server Installation"
    
    check_root
    
    # مرحله 1: بررسی سیستم
    print_info "مرحله 1/7: بررسی سیستم..."
    check_system
    
    # مرحله 2: نصب dependencies
    print_info "مرحله 2/7: نصب dependencies..."
    install_dependencies
    
    # مرحله 3: Build کردن slipstream
    print_info "مرحله 3/7: Build کردن slipstream..."
    build_slipstream
    
    # مرحله 4: تنظیم config
    print_info "مرحله 4/7: تنظیم configuration..."
    setup_config
    
    # مرحله 5: تنظیم systemd service
    print_info "مرحله 5/7: تنظیم systemd service..."
    setup_service
    
    # مرحله 6: تنظیم firewall
    print_info "مرحله 6/7: تنظیم firewall..."
    setup_firewall
    
    # مرحله 7: اعمال kernel tuning
    print_info "مرحله 7/7: اعمال kernel tuning..."
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
    
    # بررسی RAM
    TOTAL_RAM=$(free -g | awk '/^Mem:/{print $2}')
    print_success "Total RAM: ${TOTAL_RAM}GB"
    
    if [ "$TOTAL_RAM" -lt 2 ]; then
        print_warning "توصیه میشه حداقل 2GB RAM داشته باشی"
    fi
    
    # بررسی disk space
    DISK_FREE=$(df -h / | awk 'NR==2 {print $4}')
    print_success "Free disk space: $DISK_FREE"
}

# ============================================================================
# مرحله 2: نصب Dependencies
# ============================================================================

install_dependencies() {
    print_info "به‌روزرسانی package list..."
    apt-get update -qq
    
    print_info "نصب build dependencies..."
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
        iptables-persistent
    
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
    
    # بررسی نصب
    if command -v slipstream &> /dev/null; then
        SLIPSTREAM_VER=$(slipstream --version 2>&1 | head -n1)
        print_success "slipstream version: $SLIPSTREAM_VER"
    else
        print_error "خطا در نصب slipstream"
        exit 1
    fi
}

# ============================================================================
# مرحله 4: تنظیم Configuration
# ============================================================================

setup_config() {
    # ایجاد directory
    mkdir -p /etc/slipstream
    mkdir -p /var/log
    
    # کپی config
    if [ -f "../configs/server.conf" ]; then
        cp ../configs/server.conf /etc/slipstream/
        print_success "Config file کپی شد"
    else
        print_error "Config file پیدا نشد!"
        exit 1
    fi
    
    # Generate private key
    print_info "Generate کردن private key..."
    PRIV_KEY=$(openssl rand -hex 32)
    
    # جایگزینی در config
    sed -i "s/REPLACE_WITH_YOUR_PRIVATE_KEY_HEX_64_CHARS/$PRIV_KEY/g" /etc/slipstream/server.conf
    
    print_success "Private key generate شد"
    print_warning "Private Key: $PRIV_KEY"
    print_warning "این کلید رو ذخیره کن! برای client config لازمه"
    
    # سوال برای domain
    read -p "دامنه DNS شما (مثل t.irihost.com): " DOMAIN
    sed -i "s/t.irihost.com/$DOMAIN/g" /etc/slipstream/server.conf
    
    print_success "Configuration تنظیم شد"
}

# ============================================================================
# مرحله 5: تنظیم Systemd Service
# ============================================================================

setup_service() {
    # کپی service file
    if [ -f "../configs/slipstream-server.service" ]; then
        cp ../configs/slipstream-server.service /etc/systemd/system/
        print_success "Service file کپی شد"
    else
        print_error "Service file پیدا نشد!"
        exit 1
    fi
    
    # Reload systemd
    systemctl daemon-reload
    
    # Enable service
    systemctl enable slipstream-server
    print_success "Service enabled شد"
}

# ============================================================================
# مرحله 6: تنظیم Firewall
# ============================================================================

setup_firewall() {
    # بررسی اینکه ufw نصب است
    if command -v ufw &> /dev/null; then
        print_info "تنظیم UFW firewall..."
        ufw allow 53/udp comment 'slipstream DNS tunnel'
        print_success "UFW rule اضافه شد"
    fi
    
    # iptables rule (به عنوان backup)
    print_info "تنظیم iptables..."
    iptables -A INPUT -p udp --dport 53 -j ACCEPT
    
    # ذخیره iptables rules
    if command -v netfilter-persistent &> /dev/null; then
        netfilter-persistent save
        print_success "iptables rules ذخیره شدند"
    fi
}

# ============================================================================
# مرحله 7: اعمال Kernel Tuning
# ============================================================================

apply_tuning() {
    # کپی tuning file
    if [ -f "../configs/99-tunnel-tuning.conf" ]; then
        cp ../configs/99-tunnel-tuning.conf /etc/sysctl.d/
        print_success "Tuning file کپی شد"
    fi
    
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
    print_success "slipstream server آماده است"
    echo ""
    
    print_info "دستورات بعدی:"
    echo ""
    echo "1. شروع سرویس:"
    echo "   systemctl start slipstream-server"
    echo ""
    echo "2. بررسی status:"
    echo "   systemctl status slipstream-server"
    echo ""
    echo "3. دیدن logs:"
    echo "   journalctl -u slipstream-server -f"
    echo ""
    echo "4. تنظیم DNS:"
    echo "   - یک NS record بساز که به این سرور point کنه"
    echo "   - مثال: t.irihost.com NS ns1.irihost.com"
    echo "   - ns1.irihost.com A $(curl -s ifconfig.me)"
    echo ""
    
    print_warning "نکات مهم:"
    echo "- فایل /etc/slipstream/server.conf رو بررسی کن"
    echo "- Private key رو برای client config ذخیره کن"
    echo "- بعد از تنظیم DNS، حداقل 5 دقیقه صبر کن برای propagation"
    echo ""
    
    print_info "برای تست DNS:"
    echo "   dig @8.8.8.8 $(grep domain /etc/slipstream/server.conf | awk '{print $3}' | tr -d '\"')"
    echo ""
}

# ============================================================================
# اجرای اسکریپت
# ============================================================================

main "$@"
