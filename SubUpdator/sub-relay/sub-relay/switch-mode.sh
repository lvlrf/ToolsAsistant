#!/bin/bash
set -e

# رنگ‌ها
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

INSTALL_DIR="/opt/sub-relay"

# لود کانفیگ
if [ ! -f "$INSTALL_DIR/config.env" ]; then
    echo -e "${RED}❌ فایل config.env یافت نشد!${NC}"
    exit 1
fi

source "$INSTALL_DIR/config.env"

# گرفتن مدل از آرگومان یا از config
MODE=${1:-$ACTIVE_MODE}

# اعتبارسنجی مدل
if [ "$MODE" != "wireguard" ] && [ "$MODE" != "xray" ]; then
    echo -e "${RED}❌ مدل نامعتبر!${NC}"
    echo -e "${YELLOW}استفاده: $0 [wireguard|xray]${NC}"
    exit 1
fi

echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  تغییر مدل Sub-Relay                  ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}🔄 در حال تغییر به مدل: ${YELLOW}${MODE}${NC}"
echo ""

if [ "$MODE" == "wireguard" ]; then
    echo -e "${YELLOW}📡 فعال‌سازی مدل WireGuard...${NC}"
    
    # کپی کانفیگ WireGuard
    if [ ! -f "$INSTALL_DIR/wireguard/wg-iran.conf" ]; then
        echo -e "${RED}❌ فایل کانفیگ WireGuard یافت نشد!${NC}"
        exit 1
    fi
    
    # جایگزینی متغیرها در کانفیگ WireGuard
    envsubst < "$INSTALL_DIR/wireguard/wg-iran.conf" > /etc/wireguard/wg0.conf
    
    # فعال‌سازی WireGuard
    systemctl enable wg-quick@wg0
    systemctl restart wg-quick@wg0
    echo -e "${GREEN}  ✅ WireGuard فعال شد${NC}"
    
    # کپی کانفیگ HAProxy برای WireGuard
    envsubst < "$INSTALL_DIR/haproxy/haproxy-wireguard.cfg" > /etc/haproxy/haproxy.cfg
    echo -e "${GREEN}  ✅ کانفیگ HAProxy آپدیت شد${NC}"
    
    # غیرفعال کردن Xray و Nginx
    systemctl disable --now xray-client.service 2>/dev/null || true
    systemctl disable --now nginx 2>/dev/null || true
    echo -e "${GREEN}  ✅ Xray و Nginx غیرفعال شدند${NC}"
    
elif [ "$MODE" == "xray" ]; then
    echo -e "${YELLOW}⚡ فعال‌سازی مدل Xray...${NC}"
    
    # غیرفعال کردن WireGuard
    systemctl disable --now wg-quick@wg0 2>/dev/null || true
    echo -e "${GREEN}  ✅ WireGuard غیرفعال شد${NC}"
    
    # کپی و پردازش کانفیگ Xray
    if [ ! -f "$INSTALL_DIR/xray-client/config.json" ]; then
        echo -e "${RED}❌ فایل کانفیگ Xray یافت نشد!${NC}"
        exit 1
    fi
    
    # استخراج hostname از PANEL_URL برای استفاده در config
    PANEL_URL_HOST=$(echo "$PANEL_URL" | sed -e 's|^[^/]*//||' -e 's|/.*$||')
    export PANEL_URL_HOST
    
    envsubst < "$INSTALL_DIR/xray-client/config.json" > /usr/local/etc/xray/config.json
    systemctl enable xray-client.service
    systemctl restart xray-client.service
    echo -e "${GREEN}  ✅ Xray فعال شد${NC}"
    
    # کپی کانفیگ Nginx
    envsubst < "$INSTALL_DIR/nginx/sub-proxy.conf" > /etc/nginx/sites-available/sub-proxy
    ln -sf /etc/nginx/sites-available/sub-proxy /etc/nginx/sites-enabled/
    
    # تست کانفیگ Nginx
    nginx -t > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo -e "${YELLOW}⚠️  کانفیگ Nginx مشکل دارد، در حال بررسی...${NC}"
        nginx -t
    fi
    
    systemctl enable nginx
    systemctl restart nginx
    echo -e "${GREEN}  ✅ Nginx فعال شد${NC}"
    
    # کپی کانفیگ HAProxy برای Xray
    envsubst < "$INSTALL_DIR/haproxy/haproxy-xray.cfg" > /etc/haproxy/haproxy.cfg
    echo -e "${GREEN}  ✅ کانفیگ HAProxy آپدیت شد${NC}"
fi

# ریستارت HAProxy
echo -e "${YELLOW}🔄 ریستارت HAProxy...${NC}"
systemctl restart haproxy
echo -e "${GREEN}  ✅ HAProxy ریستارت شد${NC}"

# آپدیت ACTIVE_MODE در config.env
sed -i "s/^ACTIVE_MODE=.*/ACTIVE_MODE=\"$MODE\"/" "$INSTALL_DIR/config.env"
echo -e "${GREEN}  ✅ config.env آپدیت شد${NC}"

# ریستارت داشبورد
echo -e "${YELLOW}🔄 ریستارت داشبورد...${NC}"
systemctl restart sub-relay-dashboard
echo -e "${GREEN}  ✅ داشبورد ریستارت شد${NC}"

echo ""
echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✅ تغییر مدل با موفقیت انجام شد!     ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📊 مدل فعال: ${YELLOW}${MODE}${NC}"
echo -e "${BLUE}🌐 داشبورد: ${YELLOW}http://YOUR_IP:${DASHBOARD_PORT}${NC}"
echo ""

# نمایش وضعیت سرویس‌ها
echo -e "${YELLOW}📋 وضعیت سرویس‌ها:${NC}"
systemctl is-active --quiet haproxy && echo -e "  ${GREEN}✅ HAProxy: فعال${NC}" || echo -e "  ${RED}❌ HAProxy: غیرفعال${NC}"

if [ "$MODE" == "wireguard" ]; then
    systemctl is-active --quiet wg-quick@wg0 && echo -e "  ${GREEN}✅ WireGuard: فعال${NC}" || echo -e "  ${RED}❌ WireGuard: غیرفعال${NC}"
else
    systemctl is-active --quiet xray-client && echo -e "  ${GREEN}✅ Xray: فعال${NC}" || echo -e "  ${RED}❌ Xray: غیرفعال${NC}"
    systemctl is-active --quiet nginx && echo -e "  ${GREEN}✅ Nginx: فعال${NC}" || echo -e "  ${RED}❌ Nginx: غیرفعال${NC}"
fi

systemctl is-active --quiet sub-relay-dashboard && echo -e "  ${GREEN}✅ Dashboard: فعال${NC}" || echo -e "  ${RED}❌ Dashboard: غیرفعال${NC}"
echo ""
