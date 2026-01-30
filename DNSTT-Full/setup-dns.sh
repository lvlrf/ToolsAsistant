#!/bin/bash

# ============================================================================
# DNS Setup Guide - Interactive Script
# راهنمای گام‌به‌گام تنظیم DNS برای slipstream tunnel
# ============================================================================

# رنگ‌ها
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================${NC}"
}

print_step() {
    echo -e "${GREEN}▶ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# ============================================================================
# Main
# ============================================================================

clear
print_header "DNS Setup Guide for slipstream Tunnel"

echo ""
print_info "این اسکریپت به شما کمک میکنه DNS رو درست تنظیم کنی"
echo ""

# دریافت اطلاعات
read -p "دامنه اصلی شما (مثل irihost.com): " MAIN_DOMAIN
read -p "Subdomain برای tunnel (مثل t): " SUBDOMAIN
read -p "IP سرور خارج: " SERVER_IP

TUNNEL_DOMAIN="${SUBDOMAIN}.${MAIN_DOMAIN}"
NS_DOMAIN="ns1.${MAIN_DOMAIN}"

echo ""
print_header "خلاصه تنظیمات"
echo ""
echo "دامنه اصلی: $MAIN_DOMAIN"
echo "Tunnel domain: $TUNNEL_DOMAIN"
echo "Nameserver: $NS_DOMAIN"
echo "Server IP: $SERVER_IP"
echo ""

read -p "اطلاعات درست است؟ (y/n): " confirm
if [ "$confirm" != "y" ]; then
    echo "Cancelled."
    exit 0
fi

echo ""
print_header "مراحل تنظیم DNS"
echo ""

print_step "مرحله 1: ورود به DNS Panel"
echo "  - به DNS provider خودت برو (Cloudflare, Namecheap, etc.)"
echo "  - دامنه $MAIN_DOMAIN رو انتخاب کن"
echo ""
read -p "Enter برای ادامه..."

print_step "مرحله 2: افزودن A Record برای Nameserver"
echo ""
echo "  Type:  A"
echo "  Name:  ns1"
echo "  Value: $SERVER_IP"
echo "  TTL:   300 (5 minutes)"
echo ""
echo "مثال visual:"
echo "  ┌────────┬──────┬─────────────┬─────┐"
echo "  │ Type   │ Name │ Value       │ TTL │"
echo "  ├────────┼──────┼─────────────┼─────┤"
echo "  │ A      │ ns1  │ $SERVER_IP  │ 300 │"
echo "  └────────┴──────┴─────────────┴─────┘"
echo ""
read -p "A record رو اضافه کردی؟ (y/n): " confirm_a
if [ "$confirm_a" != "y" ]; then
    print_warning "لطفاً A record رو اضافه کن و دوباره run کن"
    exit 1
fi

print_step "مرحله 3: افزودن NS Record برای Tunnel Domain"
echo ""
echo "  Type:  NS"
echo "  Name:  $SUBDOMAIN"
echo "  Value: $NS_DOMAIN"
echo "  TTL:   300 (5 minutes)"
echo ""
echo "مثال visual:"
echo "  ┌────────┬──────┬─────────────────┬─────┐"
echo "  │ Type   │ Name │ Value           │ TTL │"
echo "  ├────────┼──────┼─────────────────┼─────┤"
echo "  │ NS     │ $SUBDOMAIN    │ $NS_DOMAIN      │ 300 │"
echo "  └────────┴──────┴─────────────────┴─────┘"
echo ""
print_warning "نکته: در بعضی provider ها باید نام کامل رو بنویسی: $TUNNEL_DOMAIN"
echo ""
read -p "NS record رو اضافه کردی؟ (y/n): " confirm_ns
if [ "$confirm_ns" != "y" ]; then
    print_warning "لطفاً NS record رو اضافه کن و دوباره run کن"
    exit 1
fi

print_step "مرحله 4: ذخیره تنظیمات"
echo "  - تغییرات رو Save کن"
echo "  - منتظر بمون تا DNS propagate بشه (5-30 دقیقه)"
echo ""
read -p "Enter برای تست DNS..."

print_step "مرحله 5: تست DNS"
echo ""
echo "در حال تست $TUNNEL_DOMAIN..."
echo ""

# تست A record
print_info "تست A record برای $NS_DOMAIN..."
A_RESULT=$(dig +short @8.8.8.8 $NS_DOMAIN A)
if [ "$A_RESULT" == "$SERVER_IP" ]; then
    echo -e "${GREEN}✓ A record درسته: $A_RESULT${NC}"
else
    echo -e "${RED}✗ A record هنوز propagate نشده یا اشتباه است${NC}"
    echo "  انتظار: $SERVER_IP"
    echo "  دریافتی: $A_RESULT"
    echo ""
    print_warning "صبر کن چند دقیقه و دوباره تست کن"
fi

echo ""

# تست NS record
print_info "تست NS record برای $TUNNEL_DOMAIN..."
NS_RESULT=$(dig +short @8.8.8.8 $TUNNEL_DOMAIN NS)
if echo "$NS_RESULT" | grep -q "$NS_DOMAIN"; then
    echo -e "${GREEN}✓ NS record درسته: $NS_RESULT${NC}"
else
    echo -e "${RED}✗ NS record هنوز propagate نشده یا اشتباه است${NC}"
    echo "  انتظار: $NS_DOMAIN"
    echo "  دریافتی: $NS_RESULT"
    echo ""
    print_warning "صبر کن چند دقیقه و دوباره تست کن"
fi

echo ""
print_header "دستورات تست اضافی"
echo ""
echo "برای تست دستی:"
echo ""
echo "1. تست A record:"
echo "   dig @8.8.8.8 $NS_DOMAIN A"
echo "   nslookup $NS_DOMAIN 8.8.8.8"
echo ""
echo "2. تست NS record:"
echo "   dig @8.8.8.8 $TUNNEL_DOMAIN NS"
echo "   nslookup -type=NS $TUNNEL_DOMAIN 8.8.8.8"
echo ""
echo "3. تست از DNS های مختلف:"
echo "   dig @1.1.1.1 $TUNNEL_DOMAIN NS"
echo "   dig @9.9.9.9 $TUNNEL_DOMAIN NS"
echo ""
echo "4. چک کردن propagation جهانی:"
echo "   https://dnschecker.org (وارد کن: $TUNNEL_DOMAIN, type: NS)"
echo "   https://whatsmydns.net"
echo ""

print_header "مراحل بعدی"
echo ""
echo "اگر DNS propagate شد:"
echo "1. روی سرور خارج، slipstream server رو start کن"
echo "2. روی سرور ایران، slipstream client رو start کن"
echo "3. تست کن connection برقرار میشه"
echo ""

print_info "برای تست مجدد این اسکریپت:"
echo "  ./setup-dns.sh"
echo ""
