#!/bin/bash
set -e

# رنگ‌ها برای خروجی
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   نصب سیستم Sub-Relay                ║${NC}"
echo -e "${GREEN}║   Subscription Relay System            ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""

# چک کردن root access
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}❌ این اسکریپت باید با دسترسی root اجرا شود${NC}"
   echo -e "${YELLOW}لطفاً با sudo اجرا کنید: sudo ./install.sh${NC}"
   exit 1
fi

# مسیر نصب
INSTALL_DIR="/opt/sub-relay"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}📍 مسیر اسکریپت: ${SCRIPT_DIR}${NC}"
echo -e "${BLUE}📍 مسیر نصب: ${INSTALL_DIR}${NC}"
echo ""

# کپی فایل‌ها به /opt
echo -e "${YELLOW}📦 در حال کپی فایل‌ها به ${INSTALL_DIR}...${NC}"
mkdir -p "$INSTALL_DIR"
cp -r "$SCRIPT_DIR"/* "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR"/*.sh

# لود کانفیگ
if [ ! -f "$INSTALL_DIR/config.env" ]; then
    echo -e "${RED}❌ فایل config.env یافت نشد!${NC}"
    echo -e "${YELLOW}لطفاً ابتدا config.env را ویرایش کنید${NC}"
    exit 1
fi

source "$INSTALL_DIR/config.env"
echo -e "${GREEN}✅ فایل config.env لود شد${NC}"
echo ""

# نصب پیش‌نیازها
echo -e "${YELLOW}📦 نصب پیش‌نیازها...${NC}"
apt update -qq
apt install -y haproxy nginx python3 python3-pip python3-venv wireguard-tools curl jq > /dev/null 2>&1
echo -e "${GREEN}✅ پیش‌نیازها نصب شدند${NC}"
echo ""

# ساخت virtual environment برای داشبورد
echo -e "${YELLOW}🐍 ساخت محیط Python برای داشبورد...${NC}"
python3 -m venv "$INSTALL_DIR/dashboard/venv"
source "$INSTALL_DIR/dashboard/venv/bin/activate"
pip install --upgrade pip > /dev/null 2>&1
pip install -r "$INSTALL_DIR/dashboard/requirements.txt" > /dev/null 2>&1
deactivate
echo -e "${GREEN}✅ محیط Python آماده شد${NC}"
echo ""

# نصب Xray (اگر نصب نشده)
if ! command -v xray &> /dev/null; then
    echo -e "${YELLOW}📦 نصب Xray...${NC}"
    bash -c "$(curl -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh)" @ install > /dev/null 2>&1
    echo -e "${GREEN}✅ Xray نصب شد${NC}"
else
    echo -e "${GREEN}✅ Xray از قبل نصب است${NC}"
fi
echo ""

# کپی سرویس‌های systemd
echo -e "${YELLOW}⚙️  کپی سرویس‌های systemd...${NC}"
cp "$INSTALL_DIR/systemd"/*.service /etc/systemd/system/
systemctl daemon-reload
echo -e "${GREEN}✅ سرویس‌ها ثبت شدند${NC}"
echo ""

# فعال‌سازی داشبورد و HAProxy
echo -e "${YELLOW}🚀 فعال‌سازی سرویس‌های اصلی...${NC}"
systemctl enable sub-relay-dashboard
systemctl enable haproxy
echo -e "${GREEN}✅ سرویس‌ها فعال شدند${NC}"
echo ""

# بررسی SSL
echo -e "${YELLOW}🔐 بررسی گواهی SSL...${NC}"
if [ ! -f "$SSL_CERT_PATH" ]; then
    echo -e "${RED}⚠️  گواهی SSL برای ${SUB_DOMAIN} یافت نشد!${NC}"
    echo -e "${YELLOW}برای دریافت گواهی اجرا کنید:${NC}"
    echo -e "  ${BLUE}certbot certonly --standalone -d ${SUB_DOMAIN}${NC}"
    echo ""
else
    echo -e "${GREEN}✅ گواهی SSL موجود است${NC}"
fi
echo ""

# پیام نهایی
echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✅ نصب با موفقیت انجام شد!          ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}📝 مراحل بعدی:${NC}"
echo -e "  1️⃣  فایل config.env را ویرایش کنید:"
echo -e "     ${BLUE}nano $INSTALL_DIR/config.env${NC}"
echo ""
echo -e "  2️⃣  اگر SSL ندارید، دریافت کنید:"
echo -e "     ${BLUE}certbot certonly --standalone -d ${SUB_DOMAIN}${NC}"
echo ""
echo -e "  3️⃣  یکی از مدل‌ها را فعال کنید:"
echo -e "     ${BLUE}$INSTALL_DIR/switch-mode.sh wireguard${NC}"
echo -e "     ${BLUE}$INSTALL_DIR/switch-mode.sh xray${NC}"
echo ""
echo -e "  4️⃣  داشبورد را مشاهده کنید:"
echo -e "     ${BLUE}http://YOUR_SERVER_IP:${DASHBOARD_PORT}${NC}"
echo ""
echo -e "${GREEN}موفق باشید! 🎉${NC}"
