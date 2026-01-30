# راهنمای حل مشکلات (Troubleshooting)

این راهنما شامل حل مشکلات رایج در راه‌اندازی و استفاده از DNS Tunnel هست.

---

## 🔍 عیب‌یابی سریع

قبل از هر کاری، اسکریپت خودکار عیب‌یابی رو اجرا کن:

```bash
cd /root/dns-tunnel-megaprompt
./scripts/troubleshoot.sh
```

این اسکریپت اکثر مشکلات رایج رو check میکنه و راهنمایی میده.

---

## 📑 فهرست مشکلات

1. [slipstream Server مشکلات](#1-slipstream-server)
2. [slipstream Client مشکلات](#2-slipstream-client)
3. [WireGuard مشکلات](#3-wireguard)
4. [SOCKS5 مشکلات](#4-socks5)
5. [Network & Routing](#5-network--routing)
6. [Performance مشکلات](#6-performance)

---

## 1. slipstream Server

### مشکل 1.1: Server start نمیشه

**علائم:**
```bash
systemctl status slipstream-server
● slipstream-server.service - failed
```

**چک‌های اولیه:**

```bash
# چک کن binary موجود است
which slipstream
ls -la /usr/local/bin/slipstream

# چک کن config درست است
cat /etc/slipstream/server.conf

# چک کن port 53 آزاد است
netstat -ulpn | grep :53
lsof -i :53
```

**حل‌های ممکن:**

1. **اگر binary پیدا نشد:**
```bash
cd /opt/slipstream
meson compile -C builddir
cp builddir/slipstream /usr/local/bin/
chmod +x /usr/local/bin/slipstream
```

2. **اگر port 53 استفاده میشه:**
```bash
# پیدا کردن process
sudo lsof -i :53

# متوقف کردن systemd-resolved (اگر conflict داره)
systemctl stop systemd-resolved
systemctl disable systemd-resolved

# یا تغییر port در config
```

3. **اگر permission error:**
```bash
chmod 600 /etc/slipstream/server.conf
```

### مشکل 1.2: Server running است ولی query جواب نمیده

**تست:**
```bash
dig @SERVER_IP test.t.irihost.com
```

**چک‌های اولیه:**
```bash
# بررسی logs
journalctl -u slipstream-server -n 50

# چک firewall
ufw status
iptables -L -n | grep 53
```

**حل:**
```bash
# باز کردن port
ufw allow 53/udp
iptables -A INPUT -p udp --dport 53 -j ACCEPT
```

---

## 2. slipstream Client

### مشکل 2.1: Client start نمیشه

**علائم:**
```bash
systemctl status slipstream-client
● slipstream-client.service - failed
```

**چک‌های اولیه:**

```bash
# چک config
cat /etc/slipstream/client.conf

# چک resolvers
head -20 /etc/slipstream/resolvers.txt
wc -l /etc/slipstream/resolvers.txt

# چک TUN module
lsmod | grep tun
```

**حل‌های ممکن:**

1. **TUN module load نیست:**
```bash
modprobe tun
echo "tun" >> /etc/modules-load.d/modules.conf
```

2. **Resolvers کم هستن:**
```bash
# حداقل 10 IP باید باشه
echo "8.8.8.8" >> /etc/slipstream/resolvers.txt
echo "1.1.1.1" >> /etc/slipstream/resolvers.txt
# ...
```

3. **Config اشتباه:**
```bash
# چک server domain و IP
grep server_domain /etc/slipstream/client.conf
grep server_address /etc/slipstream/client.conf
```

### مشکل 2.2: Client running است ولی tunnel up نیست

**تست:**
```bash
ip addr show tun0
ping -c 3 10.0.0.1
```

**اگر tun0 پیدا نشد:**
```bash
# اجرای manual برای دیدن error
/usr/local/bin/slipstream client \
  --config /etc/slipstream/client.conf \
  --resolvers /etc/slipstream/resolvers.txt \
  --debug
```

**اگر ping جواب نمیده:**
```bash
# چک routing
ip route show
route -n

# چک iptables
iptables -t nat -L -n -v
```

### مشکل 2.3: بعضی resolvers timeout میدن

**تشخیص:**
```bash
journalctl -u slipstream-client | grep timeout
```

**حل:**
```bash
# تست manual هر resolver
while read ip; do
    timeout 2 dig @$ip google.com +short && echo "$ip - OK" || echo "$ip - FAIL"
done < /etc/slipstream/resolvers.txt

# حذف resolver های بد از فایل
```

---

## 3. WireGuard

### مشکل 3.1: WireGuard start نمیشه

**چک:**
```bash
systemctl status wg-quick@wg0
journalctl -u wg-quick@wg0 -n 50
```

**حل‌های رایج:**

1. **tun0 موجود نیست:**
```bash
# WireGuard نیاز به tun0 از slipstream داره
# اول slipstream رو start کن
systemctl start slipstream-client
sleep 5
systemctl start wg-quick@wg0
```

2. **Config syntax error:**
```bash
wg-quick up wg0  # اجرای manual برای دیدن error
```

3. **Port conflict:**
```bash
netstat -ulpn | grep 51820
# اگر چیزی پیدا شد، اون process رو stop کن
```

### مشکل 3.2: Client وصل نمیشه

**از سمت سرور:**
```bash
# چک peers
wg show wg0
wg show wg0 peers

# چک listening
netstat -ulpn | grep 51820
```

**از سمت کلاینت:**
```bash
# تست UDP connectivity
nc -zuv SERVER_IP 51820

# چک logs در کلاینت WireGuard
# Windows: C:\Program Files\WireGuard\log.bin
# Linux: journalctl | grep wireguard
```

**حل:**
```bash
# باز کردن firewall
ufw allow 51820/udp

# بررسی NAT
iptables -t nat -L -n -v | grep 10.8.0
```

### مشکل 3.3: Handshake failed

**علائم:**
```
latest handshake: never
```

**حل:**
```bash
# چک کلیدها درست هستن
wg show wg0 | grep "public key"

# مطمئن شو private/public key match میکنن
# در سرور: cat /etc/wireguard/wg0.conf
# در کلاینت: چک config file

# Restart
systemctl restart wg-quick@wg0
```

---

## 4. SOCKS5

### مشکل 4.1: danted start نمیشه

**چک:**
```bash
systemctl status danted
journalctl -u danted -n 50
```

**حل‌های رایج:**

1. **tun0 موجود نیست:**
```bash
# danted نیاز به tun0 داره
systemctl start slipstream-client
sleep 5
systemctl start danted
```

2. **Config syntax error:**
```bash
# تست config
danted -V -f /etc/danted.conf
```

3. **Port 1080 استفاده میشه:**
```bash
netstat -tlpn | grep 1080
# اون process رو stop کن یا port رو تغییر بده
```

### مشکل 4.2: SOCKS5 وصل میشه ولی internet نداره

**تست:**
```bash
curl --socks5 localhost:1080 ifconfig.me
```

**چک routing:**
```bash
# چک NAT
iptables -t nat -L -n -v | grep 10.0.0

# چک IP forwarding
sysctl net.ipv4.ip_forward

# چک tun0 up است
ip addr show tun0
```

**حل:**
```bash
# فعال کردن IP forwarding
sysctl -w net.ipv4.ip_forward=1

# اضافه کردن NAT rule
iptables -t nat -A POSTROUTING -o tun0 -j MASQUERADE

# Restart danted
systemctl restart danted
```

---

## 5. Network & Routing

### مشکل 5.1: IP Forwarding کار نمیکنه

**چک:**
```bash
sysctl net.ipv4.ip_forward
```

**حل:**
```bash
# Temporary
sysctl -w net.ipv4.ip_forward=1

# Permanent
echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf
sysctl -p
```

### مشکل 5.2: NAT کار نمیکنه

**چک:**
```bash
iptables -t nat -L -n -v
```

**حل:**
```bash
# اضافه کردن MASQUERADE rules
iptables -t nat -A POSTROUTING -s 10.0.0.0/24 -o tun0 -j MASQUERADE
iptables -t nat -A POSTROUTING -s 10.8.0.0/24 -o tun0 -j MASQUERADE

# ذخیره
netfilter-persistent save

# یا
iptables-save > /etc/iptables/rules.v4
```

### مشکل 5.3: Routing loop یا packet loss

**تشخیص:**
```bash
traceroute -n 8.8.8.8
mtr -n 8.8.8.8
```

**حل:**
```bash
# چک routing table
ip route show
route -n

# حذف route های duplicate
ip route del [problematic route]
```

---

## 6. Performance

### مشکل 6.1: سرعت خیلی کمه

**تست سرعت:**
```bash
./scripts/test-speed.sh
```

**علل و حل‌ها:**

1. **Resolver های کند:**
```bash
# تست سرعت هر resolver
while read ip; do
    time=$(dig @$ip google.com | grep "Query time" | awk '{print $4}')
    echo "$ip: ${time}ms"
done < /etc/slipstream/resolvers.txt

# حذف resolver های > 500ms
```

2. **MTU زیاد:**
```bash
# کاهش MTU
ip link set tun0 mtu 1280
ip link set wg0 mtu 1280
```

3. **Congestion control:**
```bash
# استفاده از BBR
sysctl -w net.ipv4.tcp_congestion_control=bbr
```

### مشکل 6.2: CPU یا RAM بالا

**تشخیص:**
```bash
top -p $(pgrep slipstream)
htop
```

**حل:**

1. **کاهش تعداد resolvers:**
```bash
# در /etc/slipstream/client.conf
concurrent_resolvers = 250  # به جای 500
```

2. **کاهش worker threads:**
```bash
# در config
worker_threads = 8  # به جای 16
```

### مشکل 6.3: Connection drops مکرر

**چک logs:**
```bash
journalctl -u slipstream-client | grep -i "disconnect\|timeout"
```

**حل:**

1. **افزایش timeout ها:**
```bash
# در /etc/slipstream/client.conf
query_timeout = 3000  # از 2000 به 3000
connection_timeout = 180  # از 120 به 180
```

2. **Keepalive:**
```bash
# فعال کردن TCP keepalive
sysctl -w net.ipv4.tcp_keepalive_time=600
```

---

## 🛠️ ابزارهای عیب‌یابی

### دستورات مفید

```bash
# مانیتورینگ real-time
./scripts/monitor.sh

# تست سرعت
./scripts/test-speed.sh

# عیب‌یابی خودکار
./scripts/troubleshoot.sh

# دیدن تمام connection ها
watch -n 1 'netstat -an | grep ESTABLISHED'

# مانیتور bandwidth
iftop -i tun0
nethogs tun0

# Packet capture
tcpdump -i tun0 -n
```

### Log Files مهم

```bash
# slipstream server
/var/log/slipstream-server.log
journalctl -u slipstream-server

# slipstream client
/var/log/slipstream-client.log
journalctl -u slipstream-client

# WireGuard
journalctl -u wg-quick@wg0

# SOCKS5
journalctl -u danted
/var/log/syslog | grep danted
```

---

## 🆘 چک‌لیست عیب‌یابی کلی

اگر هیچ چیز کار نمیکنه، این مراحل رو دنبال کن:

- [ ] همه سرویس‌ها running هستن؟
  ```bash
  systemctl status slipstream-client wg-quick@wg0 danted
  ```

- [ ] همه interface ها up هستن؟
  ```bash
  ip addr show tun0 wg0
  ```

- [ ] DNS propagate شده؟
  ```bash
  dig @8.8.8.8 t.irihost.com NS
  ```

- [ ] Firewall port ها باز هستن؟
  ```bash
  ufw status
  ```

- [ ] IP forwarding فعال است؟
  ```bash
  sysctl net.ipv4.ip_forward
  ```

- [ ] NAT rules درست هستن؟
  ```bash
  iptables -t nat -L -n -v
  ```

- [ ] Resolvers کافی هستن؟
  ```bash
  wc -l /etc/slipstream/resolvers.txt
  ```

- [ ] Logs چه error ای میدن؟
  ```bash
  journalctl -xe
  ```

---

## 📞 دریافت کمک

اگر بعد از تمام این مراحل مشکل حل نشد:

1. **جمع‌آوری اطلاعات:**
```bash
./scripts/troubleshoot.sh > troubleshoot-report.txt
journalctl --since "1 hour ago" > logs.txt
```

2. **بررسی مستندات:**
- README.md
- DNS-SETUP.md
- این فایل (TROUBLESHOOTING.md)

3. **تست مجدد با config پایه:**
- Config های نمونه رو بدون تغییر تست کن
- با تعداد کم resolver شروع کن (مثلاً 10 تا)

---

**نسخه:** 1.0  
**تاریخ:** ۱۴۰۳/۱۰/۲۷  
**تهیه‌کننده:** DrConnect (@drconnect)
