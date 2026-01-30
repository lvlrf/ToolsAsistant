# راهنمای جامع راه‌اندازی DNS Server

## Pi-hole + Unbound + dnscrypt-proxy با Split DNS ایران/خارج

---

## فهرست مطالب

1. [پیش‌نیازها و معماری](#1-پیش‌نیازها-و-معماری)
2. [ستاپ SOCKS5 روی میکروتیک 7](#2-ستاپ-socks5-روی-میکروتیک-7)
3. [نصب Pi-hole با Docker](#3-نصب-pi-hole-با-docker)
4. [نصب و کانفیگ Unbound](#4-نصب-و-کانفیگ-unbound)
5. [نصب dnscrypt-proxy](#5-نصب-dnscrypt-proxy)
6. [لیست دامنه‌های ایرانی](#6-لیست-دامنه‌های-ایرانی)
7. [سرویس‌های DoH/DoT برای کلاینت‌ها](#7-سرویس‌های-dohdot-برای-کلاینت‌ها)
8. [تست و عیب‌یابی](#8-تست-و-عیب‌یابی)
9. [دستورات مفید و نگهداری](#9-دستورات-مفید-و-نگهداری)

---

## 1. پیش‌نیازها و معماری

### 1.1 معماری کلی سیستم

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            سرور اوبونتو                                 │
│                                                                         │
│   کلاینت‌ها ──▶ ┌──────────┐    ┌──────────┐    ┌─────────────────┐     │
│                │ Pi-hole  │───▶│ Unbound  │───▶│ Split DNS       │     │
│   DNS :53      │ Docker   │    │ :5335    │    │                 │     │
│   DoH :443     │ کش+فیلتر │    │ Recursive│    │ ایران → Shecan  │     │
│   DoT :853     └──────────┘    └──────────┘    │ خارج → dnscrpt  │     │
│                                               └────────┬────────┘     │
│                                                        │              │
│                                               ┌────────▼────────┐     │
│                                               │ dnscrypt-proxy  │     │
│                                               │ :5353           │     │
│                                               │ SOCKS5 ─────────┼─────┼──▶ میکروتیک
│                                               │ DoH → 1.1.1.1   │     │    SOCKS5 :1080
│                                               └─────────────────┘     │
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │ Nginx Reverse Proxy                                             │   │
│   │ DoH: /dns-query → Pi-hole                                       │   │
│   │ DoT: :853 با stunnel                                            │   │
│   └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.2 جدول پورت‌ها و سرویس‌ها

| سرویس | پورت | پروتکل | توضیح |
|-------|------|--------|-------|
| Pi-hole DNS | 53 | UDP/TCP | DNS اصلی برای کلاینت‌ها |
| Pi-hole Web | 8080 | TCP | پنل مدیریت |
| Unbound | 5335 | UDP/TCP | DNS داخلی با Split |
| dnscrypt-proxy | 5353 | UDP/TCP | DoH از طریق SOCKS5 |
| Nginx DoH | 443 | TCP | DNS over HTTPS |
| stunnel DoT | 853 | TCP | DNS over TLS |
| میکروتیک SOCKS5 | 1080 | TCP | پروکسی خروجی |

### 1.3 پیش‌نیازهای سرور

```bash
# آپدیت سیستم
sudo apt update && sudo apt upgrade -y

# نصب پیش‌نیازها
sudo apt install -y \
    curl \
    wget \
    git \
    nano \
    htop \
    net-tools \
    dnsutils \
    ca-certificates \
    gnupg \
    lsb-release

# نصب Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# نصب Docker Compose
sudo apt install -y docker-compose-plugin

# ری‌استارت برای اعمال گروه docker
# بعد از این دستور باید logout/login کنید
newgrp docker
```

### 1.4 غیرفعال کردن systemd-resolved

```bash
# بررسی وضعیت فعلی
sudo lsof -i :53

# غیرفعال کردن systemd-resolved
sudo systemctl stop systemd-resolved
sudo systemctl disable systemd-resolved

# تنظیم DNS موقت
sudo rm /etc/resolv.conf
echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf
```

---

## 2. ستاپ SOCKS5 روی میکروتیک 7

### 2.1 فعال‌سازی SOCKS5 Server

از طریق **Winbox** یا **Terminal** میکروتیک:

```routeros
# فعال کردن SOCKS5 Server
/ip socks set enabled=yes port=1080 connection-idle-timeout=2m max-connections=200

# محدود کردن دسترسی فقط به IP سرور اوبونتو
/ip socks access
add src-address=YOUR_UBUNTU_IP action=allow comment="Ubuntu DNS Server"
add action=deny comment="Deny all others"
```

### 2.2 تنظیمات فایروال میکروتیک

```routeros
# اجازه دسترسی به پورت SOCKS5 فقط از سرور اوبونتو
/ip firewall filter
add chain=input protocol=tcp dst-port=1080 src-address=YOUR_UBUNTU_IP action=accept comment="SOCKS5 from Ubuntu"
add chain=input protocol=tcp dst-port=1080 action=drop comment="Drop other SOCKS5"
```

### 2.3 تنظیم احراز هویت (اختیاری اما توصیه می‌شود)

```routeros
# ایجاد کاربر برای SOCKS5
/ip socks user
add name=dnsuser password=YOUR_STRONG_PASSWORD
```

### 2.4 بررسی وضعیت

```routeros
# مشاهده وضعیت SOCKS5
/ip socks print

# مشاهده اتصالات فعال
/ip socks connection print
```

### 2.5 تست از سرور اوبونتو

```bash
# تست اتصال SOCKS5 (بدون احراز هویت)
curl --socks5 MIKROTIK_IP:1080 https://ifconfig.me

# تست با احراز هویت
curl --socks5 dnsuser:YOUR_PASSWORD@MIKROTIK_IP:1080 https://ifconfig.me
```

---

## 3. نصب Pi-hole با Docker

### 3.1 ساختار دایرکتوری

```bash
# ایجاد دایرکتوری‌ها
sudo mkdir -p /opt/dns-server/{pihole,unbound,dnscrypt-proxy,nginx,scripts,lists}
cd /opt/dns-server
```

### 3.2 فایل Docker Compose

```bash
nano /opt/dns-server/docker-compose.yml
```

محتوای فایل:

```yaml
version: '3.8'

services:
  pihole:
    container_name: pihole
    image: pihole/pihole:latest
    hostname: pihole
    restart: unless-stopped
    ports:
      - "53:53/tcp"
      - "53:53/udp"
      - "8080:80/tcp"
    environment:
      TZ: 'Asia/Tehran'
      WEBPASSWORD: 'YOUR_PIHOLE_PASSWORD'
      PIHOLE_DNS_: '127.0.0.1#5335'
      DNSSEC: 'false'
      DNS_BOGUS_PRIV: 'true'
      DNS_FQDN_REQUIRED: 'false'
      DNSMASQ_LISTENING: 'all'
    volumes:
      - ./pihole/etc-pihole:/etc/pihole
      - ./pihole/etc-dnsmasq.d:/etc/dnsmasq.d
    networks:
      dns_network:
        ipv4_address: 172.20.0.2
    dns:
      - 127.0.0.1
      - 178.22.122.100
    cap_add:
      - NET_ADMIN

networks:
  dns_network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/24
```

### 3.3 اجرای Pi-hole

```bash
cd /opt/dns-server
docker compose up -d pihole

# بررسی لاگ
docker logs -f pihole
```

### 3.4 دسترسی به پنل مدیریت

```
آدرس: http://YOUR_SERVER_IP:8080/admin
پسورد: YOUR_PIHOLE_PASSWORD
```

---

## 4. نصب و کانفیگ Unbound

### 4.1 نصب Unbound

```bash
sudo apt install -y unbound
```

### 4.2 دانلود Root Hints

```bash
sudo wget -O /var/lib/unbound/root.hints https://www.internic.net/domain/named.cache
sudo chown unbound:unbound /var/lib/unbound/root.hints
```

### 4.3 کانفیگ اصلی Unbound

```bash
sudo nano /etc/unbound/unbound.conf.d/pi-hole.conf
```

محتوای فایل:

```yaml
server:
    # پورت و آدرس
    port: 5335
    interface: 127.0.0.1
    interface: 172.20.0.1
    
    # دسترسی
    access-control: 127.0.0.0/8 allow
    access-control: 172.20.0.0/24 allow
    access-control: 10.0.0.0/8 allow
    access-control: 192.168.0.0/16 allow
    
    # بهینه‌سازی
    num-threads: 2
    msg-cache-slabs: 4
    rrset-cache-slabs: 4
    infra-cache-slabs: 4
    key-cache-slabs: 4
    msg-cache-size: 64m
    rrset-cache-size: 128m
    
    # امنیت
    hide-identity: yes
    hide-version: yes
    harden-glue: yes
    harden-dnssec-stripped: yes
    harden-referral-path: yes
    use-caps-for-id: yes
    
    # کش
    cache-min-ttl: 300
    cache-max-ttl: 86400
    prefetch: yes
    prefetch-key: yes
    
    # لاگ
    verbosity: 1
    logfile: /var/log/unbound/unbound.log
    log-queries: no
    log-replies: no
    
    # Root Hints
    root-hints: /var/lib/unbound/root.hints
    
    # غیرفعال کردن IPv6 (اختیاری)
    do-ip6: no
    prefer-ip6: no
    
    # Private ranges
    private-address: 10.0.0.0/8
    private-address: 172.16.0.0/12
    private-address: 192.168.0.0/16
    private-address: 169.254.0.0/16

# Include Split DNS config
include: /etc/unbound/unbound.conf.d/split-dns.conf
```

### 4.4 کانفیگ Split DNS

```bash
sudo nano /etc/unbound/unbound.conf.d/split-dns.conf
```

محتوای فایل:

```yaml
# ============================================
# Split DNS Configuration
# دامنه‌های ایرانی → DNS ایرانی (مستقیم)
# بقیه دامنه‌ها → dnscrypt-proxy (از طریق SOCKS5)
# ============================================

server:
    # Upstream پیش‌فرض: dnscrypt-proxy روی SOCKS5
    # این برای همه دامنه‌هایی که در forward-zone نیستن

forward-zone:
    name: "."
    forward-addr: 127.0.0.1@5353
    forward-first: yes

# ============================================
# DNS سرورهای ایرانی
# ============================================

# Shecan
# forward-zone:
#     name: "."
#     forward-addr: 178.22.122.100
#     forward-addr: 185.51.200.2

# 403.online
# forward-zone:
#     name: "."
#     forward-addr: 10.202.10.202
#     forward-addr: 10.202.10.102

# Radar Game (برای گیم)
# forward-zone:
#     name: "."
#     forward-addr: 10.202.10.10
#     forward-addr: 10.202.10.11

# Include Iran domains list
include: /etc/unbound/unbound.conf.d/iran-domains.conf
```

### 4.5 ایجاد دایرکتوری لاگ

```bash
sudo mkdir -p /var/log/unbound
sudo chown unbound:unbound /var/log/unbound
```

### 4.6 اجرای Unbound

```bash
# تست کانفیگ
sudo unbound-checkconf

# ری‌استارت سرویس
sudo systemctl restart unbound
sudo systemctl enable unbound

# بررسی وضعیت
sudo systemctl status unbound
```

---

## 5. نصب dnscrypt-proxy

### 5.1 دانلود و نصب

```bash
# دانلود آخرین نسخه
cd /tmp
wget https://github.com/DNSCrypt/dnscrypt-proxy/releases/download/2.1.5/dnscrypt-proxy-linux_x86_64-2.1.5.tar.gz

# استخراج
tar -xzf dnscrypt-proxy-linux_x86_64-2.1.5.tar.gz

# انتقال به محل نصب
sudo mv linux-x86_64 /opt/dnscrypt-proxy
cd /opt/dnscrypt-proxy
```

### 5.2 کانفیگ اصلی

```bash
sudo cp example-dnscrypt-proxy.toml dnscrypt-proxy.toml
sudo nano /opt/dnscrypt-proxy/dnscrypt-proxy.toml
```

محتوای فایل (بخش‌های مهم):

```toml
##############################################
#        dnscrypt-proxy configuration        #
##############################################

# پورت و آدرس
listen_addresses = ['127.0.0.1:5353']

# حداکثر کلاینت
max_clients = 250

# IPv4 only
ipv4_servers = true
ipv6_servers = false

# DoH و DNSCrypt
dnscrypt_servers = false
doh_servers = true

# امنیت
require_dnssec = false
require_nolog = true
require_nofilter = true

# SOCKS5 Proxy - مهم!
force_tcp = true

# تنظیمات پروکسی
[proxy]
# بدون احراز هویت
url = 'socks5://MIKROTIK_IP:1080'

# با احراز هویت (اگر تنظیم کردید)
# url = 'socks5://dnsuser:YOUR_PASSWORD@MIKROTIK_IP:1080'

# کش
[cache]
enabled = true
size = 4096
min_ttl = 600
max_ttl = 86400
neg_min_ttl = 60
neg_max_ttl = 600

# لاگ
[query_log]
file = '/var/log/dnscrypt-proxy/query.log'
format = 'tsv'

# Sources
[sources]
  [sources.'public-resolvers']
  urls = ['https://raw.githubusercontent.com/DNSCrypt/dnscrypt-resolvers/master/v3/public-resolvers.md']
  cache_file = '/opt/dnscrypt-proxy/public-resolvers.md'
  minisign_key = 'RWQf6LRCGA9i53mlYecO4IzT51TGPpvWucNSCh1CBM0QTaLn73Y7GFO3'

# سرورهای انتخابی (DoH)
server_names = ['cloudflare', 'cloudflare-ipv4', 'google', 'quad9-doh-ip4-port443-nofilter-pri']

# Cloudflare و Google DoH
[static]
  [static.'cloudflare']
  stamp = 'sdns://AgcAAAAAAAAABzEuMS4xLjEAEmRucy5jbG91ZGZsYXJlLmNvbQovZG5zLXF1ZXJ5'
  
  [static.'cloudflare-ipv4']
  stamp = 'sdns://AgcAAAAAAAAADDEuMC4wLjEAEmRucy5jbG91ZGZsYXJlLmNvbQovZG5zLXF1ZXJ5'
  
  [static.'google']
  stamp = 'sdns://AgUAAAAAAAAABzguOC44LjigHvYkz_9ea9O63fP92_3qVlRn43cpncfuZnUWbzAMwbmgdoAkR6AZkxo_AEMExT_cbBssN43Evo9zs5_ZyWnftEUgalBisNF41VbxY7E7Gw8ZQ10CWIKRzHVYnf7m6xHI1cMKZG5zLmdvb2dsZQovZG5zLXF1ZXJ5'
  
  [static.'quad9-doh-ip4-port443-nofilter-pri']
  stamp = 'sdns://AgYAAAAAAAAADTkuOS45LjEwOjQ0MyAI5JBHW2R1nhTyH9Qrqk3iY9HsLTNkmKs-4lNiXDTyKAdkbnM5Lm5ldAovZG5zLXF1ZXJ5'
```

### 5.3 ایجاد Systemd Service

```bash
sudo nano /etc/systemd/system/dnscrypt-proxy.service
```

محتوای فایل:

```ini
[Unit]
Description=DNSCrypt Proxy
Documentation=https://github.com/DNSCrypt/dnscrypt-proxy/wiki
After=network.target
Before=nss-lookup.target
Wants=nss-lookup.target

[Service]
Type=simple
ExecStart=/opt/dnscrypt-proxy/dnscrypt-proxy -config /opt/dnscrypt-proxy/dnscrypt-proxy.toml
Restart=always
RestartSec=5
User=root
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
```

### 5.4 ایجاد دایرکتوری لاگ

```bash
sudo mkdir -p /var/log/dnscrypt-proxy
```

### 5.5 اجرای سرویس

```bash
# ری‌لود systemd
sudo systemctl daemon-reload

# فعال‌سازی و اجرا
sudo systemctl enable dnscrypt-proxy
sudo systemctl start dnscrypt-proxy

# بررسی وضعیت
sudo systemctl status dnscrypt-proxy
```

### 5.6 تست dnscrypt-proxy

```bash
# تست مستقیم
dig @127.0.0.1 -p 5353 google.com

# بررسی که از SOCKS5 استفاده می‌کنه
dig @127.0.0.1 -p 5353 whoami.cloudflare.com TXT
```

---

## 6. لیست دامنه‌های ایرانی

### 6.1 اسکریپت دانلود و تبدیل

```bash
sudo nano /opt/dns-server/scripts/update-iran-domains.sh
```

محتوای فایل:

```bash
#!/bin/bash

# ============================================
# Update Iran Domains List for Unbound
# ============================================

set -e

# تنظیمات
IRAN_DOMAINS_URL="https://raw.githubusercontent.com/bootmortis/iran-hosted-domains/main/domains.txt"
OUTPUT_FILE="/etc/unbound/unbound.conf.d/iran-domains.conf"
TEMP_FILE="/tmp/iran-domains.txt"
BACKUP_FILE="/etc/unbound/unbound.conf.d/iran-domains.conf.bak"

# DNS سرور ایرانی (Shecan)
IRAN_DNS="178.22.122.100"
# IRAN_DNS="10.202.10.202"  # 403.online

# لاگ
LOG_FILE="/var/log/unbound/update-domains.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "Starting Iran domains update..."

# دانلود لیست
log "Downloading domains list..."
if ! curl -sS "$IRAN_DOMAINS_URL" -o "$TEMP_FILE"; then
    log "ERROR: Failed to download domains list"
    exit 1
fi

# تعداد دامنه‌ها
DOMAIN_COUNT=$(wc -l < "$TEMP_FILE")
log "Downloaded $DOMAIN_COUNT domains"

# بکاپ فایل قبلی
if [ -f "$OUTPUT_FILE" ]; then
    cp "$OUTPUT_FILE" "$BACKUP_FILE"
    log "Backed up previous config"
fi

# ایجاد فایل کانفیگ جدید
log "Generating Unbound config..."

cat > "$OUTPUT_FILE" << 'HEADER'
# ============================================
# Iran Domains - Auto Generated
# Do not edit manually!
# Generated: TIMESTAMP
# Source: github.com/bootmortis/iran-hosted-domains
# ============================================

HEADER

# جایگزینی timestamp
sed -i "s/TIMESTAMP/$(date '+%Y-%m-%d %H:%M:%S')/" "$OUTPUT_FILE"

# تبدیل هر دامنه به فرمت Unbound
while IFS= read -r domain || [ -n "$domain" ]; do
    # حذف فضای خالی و خطوط خالی
    domain=$(echo "$domain" | tr -d '[:space:]')
    
    if [ -n "$domain" ] && [[ ! "$domain" =~ ^# ]]; then
        cat >> "$OUTPUT_FILE" << EOF
forward-zone:
    name: "$domain"
    forward-addr: $IRAN_DNS
    forward-first: yes

EOF
    fi
done < "$TEMP_FILE"

# پاکسازی
rm -f "$TEMP_FILE"

# تست کانفیگ
log "Testing Unbound config..."
if ! unbound-checkconf > /dev/null 2>&1; then
    log "ERROR: Invalid config, restoring backup..."
    if [ -f "$BACKUP_FILE" ]; then
        mv "$BACKUP_FILE" "$OUTPUT_FILE"
    fi
    exit 1
fi

# ری‌استارت Unbound
log "Restarting Unbound..."
systemctl restart unbound

# بررسی وضعیت
if systemctl is-active --quiet unbound; then
    log "SUCCESS: Unbound restarted with $DOMAIN_COUNT Iran domains"
else
    log "ERROR: Unbound failed to start"
    exit 1
fi

log "Update completed successfully"
```

### 6.2 اجرای اسکریپت

```bash
# اجازه اجرا
sudo chmod +x /opt/dns-server/scripts/update-iran-domains.sh

# اجرای دستی
sudo /opt/dns-server/scripts/update-iran-domains.sh
```

### 6.3 زمان‌بندی آپدیت خودکار (Cron)

```bash
# باز کردن crontab
sudo crontab -e

# اضافه کردن خط زیر (هر روز ساعت 4 صبح)
0 4 * * * /opt/dns-server/scripts/update-iran-domains.sh >> /var/log/unbound/cron.log 2>&1
```

### 6.4 اضافه کردن دامنه‌های سفارشی

```bash
sudo nano /etc/unbound/unbound.conf.d/custom-iran-domains.conf
```

محتوای فایل:

```yaml
# ============================================
# Custom Iran Domains
# دامنه‌هایی که در لیست اصلی نیستن
# ============================================

forward-zone:
    name: "snapp.ir"
    forward-addr: 178.22.122.100
    forward-first: yes

forward-zone:
    name: "tapsi.ir"
    forward-addr: 178.22.122.100
    forward-first: yes

forward-zone:
    name: "divar.ir"
    forward-addr: 178.22.122.100
    forward-first: yes

# اضافه کردن دامنه‌های دیگر...
```

---

## 7. سرویس‌های DoH/DoT برای کلاینت‌ها

### 7.1 نصب Nginx

```bash
sudo apt install -y nginx
```

### 7.2 نصب Certbot برای SSL

```bash
sudo apt install -y certbot python3-certbot-nginx
```

### 7.3 دریافت SSL Certificate

```bash
# جایگزین YOUR_DOMAIN با دامنه خودتون
sudo certbot --nginx -d dns.YOUR_DOMAIN.com
```

### 7.4 کانفیگ Nginx برای DoH

```bash
sudo nano /etc/nginx/sites-available/doh
```

محتوای فایل:

```nginx
# ============================================
# DNS over HTTPS (DoH) Configuration
# ============================================

# Rate limiting
limit_req_zone $binary_remote_addr zone=doh_limit:10m rate=50r/s;

# Upstream برای Pi-hole
upstream pihole_dns {
    server 127.0.0.1:53;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name dns.YOUR_DOMAIN.com;

    # SSL Certificates (Certbot)
    ssl_certificate /etc/letsencrypt/live/dns.YOUR_DOMAIN.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/dns.YOUR_DOMAIN.com/privkey.pem;
    
    # SSL Settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;
    ssl_session_tickets off;

    # Security Headers
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header Strict-Transport-Security "max-age=63072000" always;

    # DoH Endpoint
    location /dns-query {
        limit_req zone=doh_limit burst=100 nodelay;
        
        # فقط POST و GET
        if ($request_method !~ ^(GET|POST)$) {
            return 405;
        }

        # پروکسی به Pi-hole
        proxy_pass http://127.0.0.1:8053;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # تایم‌اوت
        proxy_connect_timeout 5s;
        proxy_send_timeout 10s;
        proxy_read_timeout 10s;
    }

    # Health check
    location /health {
        return 200 'OK';
        add_header Content-Type text/plain;
    }

    # بقیه درخواست‌ها
    location / {
        return 404;
    }

    # لاگ
    access_log /var/log/nginx/doh_access.log;
    error_log /var/log/nginx/doh_error.log;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name dns.YOUR_DOMAIN.com;
    return 301 https://$server_name$request_uri;
}
```

### 7.5 نصب DoH Server (dns-over-https)

برای پردازش واقعی DoH نیاز به یک سرور DoH داریم:

```bash
# دانلود
cd /tmp
wget https://github.com/m13253/dns-over-https/releases/download/v2.3.4/doh-server_2.3.4_linux_amd64.tar.gz

# استخراج
tar -xzf doh-server_2.3.4_linux_amd64.tar.gz

# نصب
sudo mv doh-server /usr/local/bin/
sudo chmod +x /usr/local/bin/doh-server
```

### 7.6 کانفیگ DoH Server

```bash
sudo mkdir -p /etc/dns-over-https
sudo nano /etc/dns-over-https/doh-server.conf
```

محتوای فایل:

```toml
# DNS over HTTPS Server Configuration

listen = [
    "127.0.0.1:8053",
]

# آدرس Pi-hole
[upstream]
upstream_selector = "random"

[[upstream.upstream_ietf]]
url = "udp:127.0.0.1:53"
weight = 100

[other]
verbose = false
log_guessed_client_ip = false
```

### 7.7 Systemd Service برای DoH Server

```bash
sudo nano /etc/systemd/system/doh-server.service
```

محتوای فایل:

```ini
[Unit]
Description=DNS over HTTPS Server
After=network.target
Wants=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/doh-server -conf /etc/dns-over-https/doh-server.conf
Restart=always
RestartSec=5
User=nobody
Group=nogroup

[Install]
WantedBy=multi-user.target
```

### 7.8 نصب و کانفیگ stunnel برای DoT

```bash
sudo apt install -y stunnel4
```

کانفیگ stunnel:

```bash
sudo nano /etc/stunnel/stunnel.conf
```

محتوای فایل:

```ini
; ============================================
; DNS over TLS (DoT) Configuration
; ============================================

setuid = stunnel4
setgid = stunnel4
pid = /var/run/stunnel4/stunnel.pid

[dot]
accept = 853
connect = 127.0.0.1:53
cert = /etc/letsencrypt/live/dns.YOUR_DOMAIN.com/fullchain.pem
key = /etc/letsencrypt/live/dns.YOUR_DOMAIN.com/privkey.pem
```

### 7.9 فعال‌سازی سرویس‌ها

```bash
# فعال کردن stunnel
sudo sed -i 's/ENABLED=0/ENABLED=1/' /etc/default/stunnel4

# فعال‌سازی Nginx site
sudo ln -s /etc/nginx/sites-available/doh /etc/nginx/sites-enabled/

# ری‌لود و ری‌استارت
sudo systemctl daemon-reload
sudo systemctl enable doh-server stunnel4 nginx
sudo systemctl restart doh-server stunnel4 nginx

# تست کانفیگ Nginx
sudo nginx -t
```

### 7.10 تست DoH و DoT

```bash
# تست DoH با curl
curl -H 'accept: application/dns-json' \
  'https://dns.YOUR_DOMAIN.com/dns-query?name=google.com&type=A'

# تست DoT با kdig
sudo apt install -y knot-dnsutils
kdig @dns.YOUR_DOMAIN.com +tls google.com
```

---

## 8. تست و عیب‌یابی

### 8.1 اسکریپت تست جامع

```bash
sudo nano /opt/dns-server/scripts/test-dns.sh
```

محتوای فایل:

```bash
#!/bin/bash

# ============================================
# DNS Server Test Script
# ============================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "============================================"
echo "         DNS Server Test Suite"
echo "============================================"
echo ""

# تست سرویس‌ها
echo -e "${YELLOW}[1/6] Testing Services Status...${NC}"
echo ""

services=("pihole" "unbound" "dnscrypt-proxy" "doh-server" "stunnel4" "nginx")
for svc in "${services[@]}"; do
    if systemctl is-active --quiet "$svc" 2>/dev/null || docker ps --format '{{.Names}}' | grep -q "^$svc$"; then
        echo -e "  ✅ $svc: ${GREEN}Running${NC}"
    else
        echo -e "  ❌ $svc: ${RED}Not Running${NC}"
    fi
done
echo ""

# تست پورت‌ها
echo -e "${YELLOW}[2/6] Testing Ports...${NC}"
echo ""

ports=("53:DNS" "5335:Unbound" "5353:dnscrypt-proxy" "8080:Pi-hole Web" "443:HTTPS" "853:DoT")
for port_info in "${ports[@]}"; do
    port=$(echo "$port_info" | cut -d: -f1)
    name=$(echo "$port_info" | cut -d: -f2)
    if ss -tuln | grep -q ":$port "; then
        echo -e "  ✅ Port $port ($name): ${GREEN}Open${NC}"
    else
        echo -e "  ❌ Port $port ($name): ${RED}Closed${NC}"
    fi
done
echo ""

# تست DNS Resolution
echo -e "${YELLOW}[3/6] Testing DNS Resolution...${NC}"
echo ""

# تست Pi-hole
echo "  Testing Pi-hole (port 53)..."
result=$(dig @127.0.0.1 -p 53 google.com +short +timeout=5 2>/dev/null)
if [ -n "$result" ]; then
    echo -e "  ✅ Pi-hole: ${GREEN}Working${NC} (google.com → $result)"
else
    echo -e "  ❌ Pi-hole: ${RED}Failed${NC}"
fi

# تست Unbound
echo "  Testing Unbound (port 5335)..."
result=$(dig @127.0.0.1 -p 5335 google.com +short +timeout=5 2>/dev/null)
if [ -n "$result" ]; then
    echo -e "  ✅ Unbound: ${GREEN}Working${NC} (google.com → $result)"
else
    echo -e "  ❌ Unbound: ${RED}Failed${NC}"
fi

# تست dnscrypt-proxy
echo "  Testing dnscrypt-proxy (port 5353)..."
result=$(dig @127.0.0.1 -p 5353 google.com +short +timeout=10 2>/dev/null)
if [ -n "$result" ]; then
    echo -e "  ✅ dnscrypt-proxy: ${GREEN}Working${NC} (google.com → $result)"
else
    echo -e "  ❌ dnscrypt-proxy: ${RED}Failed${NC}"
fi
echo ""

# تست Split DNS
echo -e "${YELLOW}[4/6] Testing Split DNS...${NC}"
echo ""

# دامنه ایرانی
echo "  Testing Iranian domain (digikala.com)..."
result=$(dig @127.0.0.1 -p 53 digikala.com +short +timeout=5 2>/dev/null)
if [ -n "$result" ]; then
    echo -e "  ✅ Iran DNS: ${GREEN}Working${NC} (digikala.com → $result)"
else
    echo -e "  ❌ Iran DNS: ${RED}Failed${NC}"
fi

# دامنه خارجی
echo "  Testing Foreign domain (cloudflare.com)..."
result=$(dig @127.0.0.1 -p 53 cloudflare.com +short +timeout=10 2>/dev/null)
if [ -n "$result" ]; then
    echo -e "  ✅ Foreign DNS: ${GREEN}Working${NC} (cloudflare.com → $result)"
else
    echo -e "  ❌ Foreign DNS: ${RED}Failed${NC}"
fi
echo ""

# تست DNS Leak
echo -e "${YELLOW}[5/6] Testing DNS Leak Prevention...${NC}"
echo ""

echo "  Checking resolver identity..."
result=$(dig @127.0.0.1 -p 5353 whoami.cloudflare.com TXT +short +timeout=10 2>/dev/null)
if [ -n "$result" ]; then
    echo -e "  📍 Your DNS exit IP: ${GREEN}$result${NC}"
    echo "  (This should be different from your server's Iran IP)"
else
    echo -e "  ⚠️  Could not determine DNS exit IP"
fi
echo ""

# تست SOCKS5
echo -e "${YELLOW}[6/6] Testing SOCKS5 Proxy...${NC}"
echo ""

SOCKS_PROXY="MIKROTIK_IP:1080"
echo "  Testing SOCKS5 ($SOCKS_PROXY)..."
result=$(curl --socks5 "$SOCKS_PROXY" -s --connect-timeout 10 https://ifconfig.me 2>/dev/null)
if [ -n "$result" ]; then
    echo -e "  ✅ SOCKS5: ${GREEN}Working${NC} (Exit IP: $result)"
else
    echo -e "  ❌ SOCKS5: ${RED}Failed${NC}"
fi
echo ""

echo "============================================"
echo "         Test Complete!"
echo "============================================"
```

### 8.2 اجرای تست

```bash
sudo chmod +x /opt/dns-server/scripts/test-dns.sh
sudo /opt/dns-server/scripts/test-dns.sh
```

### 8.3 بررسی لاگ‌ها

```bash
# Pi-hole
docker logs pihole -f

# Unbound
sudo tail -f /var/log/unbound/unbound.log

# dnscrypt-proxy
sudo tail -f /var/log/dnscrypt-proxy/query.log

# Nginx
sudo tail -f /var/log/nginx/doh_access.log
sudo tail -f /var/log/nginx/doh_error.log
```

### 8.4 مشکلات رایج و راه‌حل

| مشکل | علت احتمالی | راه‌حل |
|------|-------------|--------|
| Port 53 in use | systemd-resolved فعاله | `sudo systemctl disable systemd-resolved` |
| dnscrypt-proxy تایم‌اوت | SOCKS5 کار نمی‌کنه | بررسی اتصال به میکروتیک |
| Split DNS کار نمی‌کنه | فایل iran-domains.conf خالی | اجرای اسکریپت آپدیت |
| DoH کار نمی‌کنه | SSL Certificate | بررسی certbot و تاریخ انقضا |
| Pi-hole UI باز نمیشه | پورت 8080 بسته | بررسی فایروال |

---

## 9. دستورات مفید و نگهداری

### 9.1 دستورات روزانه

```bash
# وضعیت همه سرویس‌ها
sudo systemctl status pihole unbound dnscrypt-proxy doh-server nginx stunnel4

# ری‌استارت همه
sudo systemctl restart unbound dnscrypt-proxy doh-server nginx stunnel4
docker restart pihole

# مشاهده کش Pi-hole
docker exec pihole pihole -c

# پاک کردن کش
docker exec pihole pihole restartdns reload

# آپدیت لیست‌های Pi-hole
docker exec pihole pihole -g
```

### 9.2 اسکریپت نگهداری

```bash
sudo nano /opt/dns-server/scripts/maintenance.sh
```

محتوای فایل:

```bash
#!/bin/bash

# ============================================
# DNS Server Maintenance Script
# ============================================

LOG_FILE="/var/log/dns-maintenance.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "Starting maintenance..."

# آپدیت لیست دامنه‌های ایرانی
log "Updating Iran domains list..."
/opt/dns-server/scripts/update-iran-domains.sh

# آپدیت Pi-hole gravity
log "Updating Pi-hole gravity..."
docker exec pihole pihole -g

# آپدیت Root Hints
log "Updating Root Hints..."
wget -q -O /var/lib/unbound/root.hints https://www.internic.net/domain/named.cache
chown unbound:unbound /var/lib/unbound/root.hints

# پاکسازی لاگ‌های قدیمی (بیشتر از 7 روز)
log "Cleaning old logs..."
find /var/log/unbound -name "*.log" -mtime +7 -delete
find /var/log/dnscrypt-proxy -name "*.log" -mtime +7 -delete
find /var/log/nginx -name "*.log" -mtime +7 -delete

# ری‌استارت سرویس‌ها
log "Restarting services..."
systemctl restart unbound dnscrypt-proxy
docker restart pihole

log "Maintenance completed!"
```

### 9.3 زمان‌بندی نگهداری هفتگی

```bash
# اجازه اجرا
sudo chmod +x /opt/dns-server/scripts/maintenance.sh

# اضافه به crontab (هر یکشنبه ساعت 3 صبح)
sudo crontab -e

# اضافه کردن:
0 3 * * 0 /opt/dns-server/scripts/maintenance.sh >> /var/log/dns-maintenance.log 2>&1
```

### 9.4 بکاپ کانفیگ‌ها

```bash
sudo nano /opt/dns-server/scripts/backup.sh
```

محتوای فایل:

```bash
#!/bin/bash

BACKUP_DIR="/opt/dns-server/backups"
DATE=$(date '+%Y%m%d_%H%M%S')
BACKUP_FILE="$BACKUP_DIR/dns-server-backup-$DATE.tar.gz"

mkdir -p "$BACKUP_DIR"

tar -czf "$BACKUP_FILE" \
    /opt/dns-server/docker-compose.yml \
    /opt/dns-server/pihole \
    /etc/unbound/unbound.conf.d \
    /opt/dnscrypt-proxy/dnscrypt-proxy.toml \
    /etc/dns-over-https \
    /etc/nginx/sites-available/doh \
    /etc/stunnel/stunnel.conf \
    2>/dev/null

# حذف بکاپ‌های قدیمی‌تر از 30 روز
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete

echo "Backup created: $BACKUP_FILE"
```

### 9.5 مانیتورینگ با Prometheus (اختیاری)

```bash
# اضافه کردن exporter به docker-compose.yml
# این بخش رو بعداً اگه خواستی میتونیم اضافه کنیم
```

---

## نکات پایانی

### امنیت

- پسوردهای قوی برای Pi-hole و SOCKS5 استفاده کنید
- فایروال رو فقط برای IP های مجاز باز کنید
- SSL Certificate رو قبل از انقضا تمدید کنید
- لاگ‌ها رو مرتب بررسی کنید

### بهینه‌سازی

- مقدار کش رو بر اساس RAM سرور تنظیم کنید
- `prefetch` در Unbound سرعت رو بهتر می‌کنه
- برای سرورهای پرترافیک `num-threads` رو افزایش بدید

### آدرس DoH/DoT برای کلاینت‌ها

```
DoH: https://dns.YOUR_DOMAIN.com/dns-query
DoT: dns.YOUR_DOMAIN.com:853
DNS: YOUR_SERVER_IP:53
```

---

## ارتباط و پشتیبانی

📱 Telegram: @lvlrf

---

*آخرین بروزرسانی: ژانویه 2025*
