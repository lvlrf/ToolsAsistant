#!/bin/bash

# ============================================================================
# WireGuard Client Generator Script
# اضافه کردن کلاینت جدید به WireGuard server
# ============================================================================

set -e

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

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# بررسی root
if [[ $EUID -ne 0 ]]; then
    print_error "این اسکریپت باید با root اجرا شود"
    exit 1
fi

# بررسی WireGuard
if ! command -v wg &> /dev/null; then
    print_error "WireGuard نصب نیست!"
    exit 1
fi

if ! ip link show wg0 &>/dev/null; then
    print_error "Interface wg0 پیدا نشد! WireGuard server running نیست؟"
    exit 1
fi

# ============================================================================
# Main
# ============================================================================

clear
print_header "WireGuard Client Generator"

# دریافت اطلاعات
echo ""
read -p "نام کلاینت (مثل: laptop-ali): " CLIENT_NAME

if [ -z "$CLIENT_NAME" ]; then
    print_error "نام کلاینت نمیتونه خالی باشه"
    exit 1
fi

# حذف فاصله و کاراکترهای خاص
CLIENT_NAME=$(echo "$CLIENT_NAME" | tr -d ' ' | tr '[:upper:]' '[:lower:]')

# تعیین IP بعدی
echo ""
print_info "پیدا کردن IP بعدی..."

# خواندن IP های موجود از wg0.conf
USED_IPS=$(grep 'AllowedIPs' /etc/wireguard/wg0.conf | awk '{print $3}' | cut -d'/' -f1 | cut -d'.' -f4 | sort -n)

# پیدا کردن اولین IP خالی (از 2 تا 254)
NEXT_IP=2
for ip in $USED_IPS; do
    if [ "$ip" -ge "$NEXT_IP" ]; then
        NEXT_IP=$((ip + 1))
    fi
done

if [ "$NEXT_IP" -gt 254 ]; then
    print_error "تمام IP ها استفاده شدن! (حداکثر 253 کلاینت)"
    exit 1
fi

CLIENT_IP="10.8.0.${NEXT_IP}"
print_success "IP کلاینت: $CLIENT_IP"

# ============================================================================
# Generate Keys
# ============================================================================

echo ""
print_info "Generate کردن کلیدها..."

# ساخت directory برای کلیدها
mkdir -p /etc/wireguard/clients

# Generate private key
CLIENT_PRIV_KEY=$(wg genkey)
CLIENT_PUB_KEY=$(echo "$CLIENT_PRIV_KEY" | wg pubkey)

print_success "کلیدها generate شدند"

# ذخیره کلیدها
echo "$CLIENT_PRIV_KEY" > /etc/wireguard/clients/${CLIENT_NAME}.key
echo "$CLIENT_PUB_KEY" > /etc/wireguard/clients/${CLIENT_NAME}.pub
chmod 600 /etc/wireguard/clients/${CLIENT_NAME}.key

# ============================================================================
# Update Server Config
# ============================================================================

echo ""
print_info "اضافه کردن peer به server config..."

# دریافت public key سرور
SERVER_PUB_KEY=$(wg show wg0 public-key)

# دریافت IP سرور
SERVER_IP=$(curl -s ifconfig.me)

# اضافه کردن peer به wg0.conf
cat >> /etc/wireguard/wg0.conf << EOF

# Client: $CLIENT_NAME
[Peer]
PublicKey = $CLIENT_PUB_KEY
AllowedIPs = $CLIENT_IP/32
PersistentKeepalive = 25
EOF

print_success "Peer به server config اضافه شد"

# Reload WireGuard config
print_info "Reload کردن WireGuard..."
wg syncconf wg0 <(wg-quick strip wg0)
print_success "WireGuard reload شد"

# ============================================================================
# Create Client Config File
# ============================================================================

echo ""
print_info "ساخت client config file..."

CLIENT_CONFIG_FILE="/etc/wireguard/clients/${CLIENT_NAME}.conf"

cat > $CLIENT_CONFIG_FILE << EOF
# WireGuard Client Configuration
# Client: $CLIENT_NAME
# Generated: $(date)

[Interface]
PrivateKey = $CLIENT_PRIV_KEY
Address = $CLIENT_IP/24
DNS = 1.1.1.1, 8.8.8.8
MTU = 1280

[Peer]
PublicKey = $SERVER_PUB_KEY
Endpoint = $SERVER_IP:51820
AllowedIPs = 0.0.0.0/0, ::/0
PersistentKeepalive = 25
EOF

chmod 600 $CLIENT_CONFIG_FILE
print_success "Client config ساخته شد: $CLIENT_CONFIG_FILE"

# ============================================================================
# Generate QR Code
# ============================================================================

echo ""
print_info "Generate کردن QR code..."

if command -v qrencode &> /dev/null; then
    QR_FILE="/etc/wireguard/clients/${CLIENT_NAME}-qr.png"
    qrencode -t png -o $QR_FILE < $CLIENT_CONFIG_FILE
    print_success "QR code ذخیره شد: $QR_FILE"
    
    # نمایش QR در terminal
    echo ""
    print_info "QR Code برای اسکن با موبایل:"
    echo ""
    qrencode -t ansiutf8 < $CLIENT_CONFIG_FILE
    echo ""
else
    print_warning "qrencode نصب نیست. برای ساخت QR code:"
    echo "  apt install qrencode"
    echo "  qrencode -t ansiutf8 < $CLIENT_CONFIG_FILE"
fi

# ============================================================================
# خلاصه
# ============================================================================

echo ""
print_header "Client Successfully Added!"
echo ""

print_info "اطلاعات کلاینت:"
echo ""
echo "نام: $CLIENT_NAME"
echo "IP: $CLIENT_IP"
echo "Public Key: $CLIENT_PUB_KEY"
echo ""

print_info "فایل‌های ایجاد شده:"
echo ""
echo "Config: $CLIENT_CONFIG_FILE"
echo "Private Key: /etc/wireguard/clients/${CLIENT_NAME}.key"
echo "Public Key: /etc/wireguard/clients/${CLIENT_NAME}.pub"
if [ -f "/etc/wireguard/clients/${CLIENT_NAME}-qr.png" ]; then
    echo "QR Code: /etc/wireguard/clients/${CLIENT_NAME}-qr.png"
fi
echo ""

print_warning "مراحل بعدی:"
echo ""
echo "1. Config file رو به کلاینت انتقال بده:"
echo "   scp $CLIENT_CONFIG_FILE user@client-ip:~/"
echo ""
echo "2. یا QR code رو برای موبایل/تبلت اسکن کن"
echo ""
echo "3. روی کلاینت، WireGuard رو نصب و config رو import کن"
echo ""
echo "4. تست کن:"
echo "   - از کلاینت: ping 10.8.0.1"
echo "   - از سرور: ping $CLIENT_IP"
echo ""

print_info "برای دیدن تمام peers:"
echo "  wg show wg0"
echo ""

print_info "برای حذف این client:"
echo "  wg set wg0 peer $CLIENT_PUB_KEY remove"
echo "  # و خط مربوطه رو از /etc/wireguard/wg0.conf حذف کن"
echo ""
