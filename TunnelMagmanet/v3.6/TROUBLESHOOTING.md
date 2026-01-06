# راهنمای رفع مشکلات

این راهنما حل مشکلات رایج در نصب و استفاده از Backhaul را ارائه می‌دهد.

---

## 🔴 سرویس استارت نمی‌شود

### علائم:
```bash
systemctl status backhaul-iran100-tcp-speed
● backhaul-iran100-tcp-speed.service - Backhaul...
   Active: failed (Result: exit-code)
```

### راه‌حل:

#### ۱. چک کردن لاگ:
```bash
journalctl -u backhaul-iran100-tcp-speed -n 50 --no-pager
```

#### ۲. چک کردن binary:
```bash
ls -la /root/backhaul-core/backhaul_premium

# اگر وجود نداره:
cd /root/backhaul-core
tar -xzf backhaul_premium.tar.gz
chmod +x backhaul_premium
```

#### ۳. چک کردن config:
```bash
cat /root/backhaul-core/iran100-tcp-speed.toml

# تست دستی:
cd /root/backhaul-core
./backhaul_premium -c iran100-tcp-speed.toml
```

#### ۴. چک کردن پورت:
```bash
ss -tlnp | grep 100
```

اگر پورت اشغال است:
```bash
# پیدا کردن process
lsof -i :100

# کشتن process
kill -9 PID
```

---

## 🔴 Permission Denied

### علائم:
```
bash: ./backhaul_premium: Permission denied
```

### راه‌حل:
```bash
chmod +x /root/backhaul-core/backhaul_premium
```

---

## 🔴 Config File Not Found

### علائم:
```
Error: config file not found: /root/backhaul-core/iran100-tcp-speed.toml
```

### راه‌حل:
```bash
# چک کردن فایل:
ls -la /root/backhaul-core/*.toml

# اگر نیست، دوباره از output کپی کنید:
scp output/Iran/Tehran/*.toml root@IP:/root/backhaul-core/
```

---

## 🔴 Port Already in Use

### علائم:
```
Error: bind: address already in use
```

### راه‌حل:

#### ۱. پیدا کردن سرویس استفاده‌کننده:
```bash
ss -tlnp | grep :PORT
lsof -i :PORT
```

#### ۲. آزاد کردن پورت:
```bash
# استاپ سرویس دیگر
systemctl stop SERVICE_NAME

# یا کشتن process
kill -9 PID
```

#### ۳. آپدیت excluded_ports:
در `config.json`:
```json
"excluded_ports": [22, 80, 443, 8080, YOUR_PORT]
```

و دوباره generator را اجرا کنید.

---

## 🔴 Connection Refused از Kharej به Iran

### علائم:
```
Error: dial tcp IRAN_IP:PORT: connect: connection refused
```

### راه‌حل:

#### ۱. چک کردن سرویس Iran:
```bash
ssh root@IRAN_IP
systemctl status backhaul-iran100-tcp-speed

# اگر stopped است:
systemctl start backhaul-iran100-tcp-speed
```

#### ۲. چک کردن firewall:
```bash
# Iran
ufw allow PORT/tcp
# یا
iptables -A INPUT -p tcp --dport PORT -j ACCEPT
```

#### ۳. چک کردن bind_addr:
در config Iran:
```toml
bind_addr = "0.0.0.0:100"  # نه 127.0.0.1
```

---

## 🔴 TUN Subnet مشکل دارد

### علائم:
```
Error: invalid TUN subnet
```

### راه‌حل:

Subnet باید به صورت network address باشد:
```
✅ درست: 10.10.10.0/24
❌ اشتباه: 10.10.10.1/24
❌ اشتباه: 10.10.10.2/24
```

اگر اشتباه است:
1. فایل config را ویرایش کنید
2. subnet را به network address تغییر دهید
3. سرویس را restart کنید

---

## 🔴 Token Mismatch

### علائم:
```
Error: token mismatch
```

### راه‌حل:

Token در Iran و Kharej باید یکسان باشد:

```bash
# چک کردن token در Iran:
grep "token" /root/backhaul-core/iran100-tcp-speed.toml

# چک کردن token در Kharej:
grep "token" /root/backhaul-core/kharej100-tcp-speed.toml
```

اگر متفاوت است:
1. یکی را کپی کنید
2. در فایل دیگر paste کنید
3. سرویس را restart کنید

---

## 🔴 Web Interface در دسترس نیست

### علائم:
```
http://IP:800 -> Connection refused
```

### راه‌حل:

#### ۱. چک کردن web_port:
```bash
grep "web_port" /root/backhaul-core/iran100-tcp-speed.toml
```

اگر `0` است، web interface غیرفعال است.

#### ۲. چک کردن firewall:
```bash
ufw allow 800/tcp
```

#### ۳. چک کردن سرویس:
```bash
systemctl status backhaul-iran100-tcp-speed
```

---

## 🔴 iperf3 کار نمی‌کند

### علائم:
```
iperf3: error - unable to connect
```

### راه‌حل:

#### ۱. روی Kharej iperf3 server را اجرا کنید:
```bash
iperf3 -s -B 127.0.0.1 -p 5201
```

#### ۲. روی Iran تست کنید:
```bash
iperf3 -c 127.0.0.1 -p 5001 -t 10
```

#### ۳. چک کردن ports در config:
```toml
# Iran
ports = [
    "5001=127.0.0.1:5201"
]

# Kharej
ports = [
    "5001=127.0.0.1:5201"
]
```

---

## 🔴 سرعت پایین

### راه‌حل:

#### ۱. تست با profile های مختلف:
```
speed   -> سریع‌ترین
stable  -> با ثبات
balanced -> تعادل
```

#### ۲. تست transport های مختلف:
```
tcp      -> سریع‌ترین
tcpmux   -> تعادل
utcpmux  -> multi-user
```

#### ۳. بهینه‌سازی سرور:
```bash
bash optimize-iran.sh
bash optimize-kharej.sh
# سپس reboot
```

#### ۴. چک MTU (برای TUN):
```toml
mtu = 1400  # به جای 1500
```

---

## 🔴 تانل قطع و وصل می‌شود

### راه‌حل:

#### ۱. استفاده از stable profile:
```json
"profiles": ["stable"]
```

#### ۲. استفاده از xtcpmux یا xwsmux:
این transport ها برای شرایط ناپایدار طراحی شده‌اند.

#### ۳. چک کردن heartbeat:
```toml
heartbeat = 40  # به جای 20
```

---

## 🔴 Generator خطا می‌دهد

### config.json invalid:
```bash
# چک syntax:
python3 -m json.tool config.json
```

### Python version:
```bash
python3 --version  # باید 3.6+ باشد
```

### state.json corrupt:
```bash
# پاک کردن و شروع دوباره:
rm state.json
python3 generator.py
```

---

## 🔴 همه سرویس‌ها failed هستند

### راه‌حل:

#### ۱. چک کردن binary extraction:
```bash
cd /root/backhaul-core
ls -la backhaul_premium

# اگر نیست:
tar -xzf backhaul_premium.tar.gz
chmod +x backhaul_premium
```

#### ۲. restart همه سرویس‌ها:
```bash
bash restart-services.sh
```

#### ۳. چک system limits:
```bash
ulimit -n  # باید >=1048576 باشد

# اگر کمتر است:
bash optimize-iran.sh  # یا optimize-kharej.sh
reboot
```

---

## 🔴 Log file نوشته نمی‌شود

### راه‌حل:

#### ۱. چک کردن مسیر:
```bash
# مسیر باید وجود داشته باشد:
mkdir -p /root/backhaul-core/iran100-tcp-speed
```

#### ۲. چک کردن config:
```toml
sniffer = true
sniffer_log = "/root/backhaul-core/iran100-tcp-speed/log.json"
```

#### ۳. چک کردن permissions:
```bash
ls -la /root/backhaul-core/
chmod 755 /root/backhaul-core/
```

---

## 📞 هنوز مشکل دارید؟

۱. **لاگ کامل** سرویس را بگیرید:
```bash
journalctl -u SERVICE_NAME -n 100 --no-pager > service.log
```

۲. **Config** را چک کنید:
```bash
cat /root/backhaul-core/CONFIG_FILE.toml
```

۳. **تست دستی:**
```bash
cd /root/backhaul-core
./backhaul_premium -c CONFIG_FILE.toml
```

۴. **پشتیبانی:**
- Telegram: @Gozar_XRay
- GitHub Issues
- مستندات رسمی Backhaul

---

**موفق باشید!** 🎯
