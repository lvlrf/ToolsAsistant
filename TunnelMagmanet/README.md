# Backhaul Premium Bulk Config Generator

ابزار خودکار برای ساخت کانفیگ‌های Backhaul Premium با پشتیبانی از همه transport ها و سه پروفایل بهینه‌سازی

---

## ✨ ویژگی‌ها

### 🎯 پشتیبانی کامل Transport
- ✅ **13 نوع transport:** tcp, tcpmux, utcpmux, xtcpmux, ws, wsmux, uwsmux, xwsmux, udp, tcptun, faketcptun, wstun, udptun
- ✅ **Mux Versions:** نسخه 1 و 2 برای همه mux transport ها
- ✅ **TUN Support:** مدیریت خودکار subnet ها برای TUN transports

### 🚀 سه پروفایل بهینه‌سازی
- **Speed:** برای حداکثر پهنای باند و سرعت
- **Stable:** برای پایداری در شبکه‌های ناپایدار
- **Balanced:** تعادل بین سرعت و پایداری

### 📊 مدیریت هوشمند
- مدیریت خودکار پورت‌ها (tunnel, web, iperf)
- مدیریت خودکار subnet های TUN
- Token یکتا برای هر connection
- State management برای اجتناب از تداخل

### 🛠 ابزارهای کامل
- اسکریپت‌های مدیریت سرویس (install, stop, restart, remove)
- اسکریپت‌های بهینه‌سازی سرور (Iran & Kharej)
- State manager برای مدیریت و آپدیت

---

## 📋 پیش‌نیازها

- Python 3.6+
- دسترسی SSH به سرورها
- باینری Backhaul Premium (فایل فشرده `.tar.gz`)

---

## 🚀 شروع سریع

### ۱. ویرایش config.json

```json
{
  "iran_servers": [
    {"name": "Tehran-Main", "ip": "1.2.3.4"}
  ],
  
  "kharej_servers": [
    {"name": "Germany-Hetzner", "ip": "5.6.7.8"}
  ],
  
  "connections": [
    {
      "iran": "Tehran-Main",
      "kharej": "Germany-Hetzner",
      "transports": ["tcp", "tcpmux", "ws", "tcptun"]
    }
  ],
  
  "settings": {
    "profiles": ["speed", "stable", "balanced"]
  }
}
```

### ۲. اجرای Generator

```bash
python3 generator.py
```

خروجی:
```
============================================================
Backhaul Premium Bulk Config Generator
============================================================

[OK] Tehran-Main -> Germany-Hetzner: tcp-speed (Port 100)
[OK] Tehran-Main -> Germany-Hetzner: tcp-stable (Port 101)
[OK] Tehran-Main -> Germany-Hetzner: tcp-balanced (Port 102)
[OK] Tehran-Main -> Germany-Hetzner: tcpmux-v1-speed (Port 103)
...

============================================================
[OK] Generated 36 configurations successfully!
Output directory: /path/to/output
State saved to: state.json
============================================================
```

### ۳. آپلود فایل باینری

```bash
# آپلود فایل فشرده به سرورها
scp backhaul_premium.tar.gz root@1.2.3.4:/root/backhaul-core/
scp backhaul_premium.tar.gz root@5.6.7.8:/root/backhaul-core/
```

### ۴. آپلود کانفیگ‌ها

```bash
# Iran
scp output/Iran/Tehran-Main/*.toml root@1.2.3.4:/root/backhaul-core/
scp output/Iran/Tehran-Main/*.sh root@1.2.3.4:/root/backhaul-core/

# Kharej
scp output/Kharej/Germany-Hetzner/*.toml root@5.6.7.8:/root/backhaul-core/
scp output/Kharej/Germany-Hetzner/*.sh root@5.6.7.8:/root/backhaul-core/
```

### ۵. بهینه‌سازی سرورها (اختیاری)

```bash
# Iran
ssh root@1.2.3.4 "cd /root/backhaul-core && bash optimize-iran.sh"

# Kharej
ssh root@5.6.7.8 "cd /root/backhaul-core && bash optimize-kharej.sh"
```

### ۶. نصب سرویس‌ها

```bash
# Iran
ssh root@1.2.3.4 "cd /root/backhaul-core && bash install-services.sh"

# Kharej
ssh root@5.6.7.8 "cd /root/backhaul-core && bash install-services.sh"
```

---

## 📁 ساختار خروجی

```
output/
├── Iran/
│   └── Tehran-Main/
│       ├── iran100-tcp-speed.toml
│       ├── iran101-tcp-stable.toml
│       ├── iran102-tcp-balanced.toml
│       ├── iran103-tcpmux-v1-speed.toml
│       ├── iran104-tcpmux-v1-stable.toml
│       ├── iran105-tcpmux-v1-balanced.toml
│       ├── iran106-tcpmux-v2-speed.toml
│       ├── ... (همه transport ها × 3 پروفایل)
│       ├── install-services.sh
│       ├── stop-services.sh
│       ├── restart-services.sh
│       └── remove-services.sh
│
└── Kharej/
    └── Germany-Hetzner/
        ├── kharej100-tcp-speed.toml
        ├── kharej101-tcp-stable.toml
        ├── ... (همه transport ها × 3 پروفایل)
        ├── install-services.sh
        ├── stop-services.sh
        ├── restart-services.sh
        └── remove-services.sh
```

---

## ⚙️ تنظیمات config.json

### binary_config

```json
{
  "binary_config": {
    "premium": {
      "path": "/root/backhaul-core",
      "filename": "backhaul_premium"
    }
  }
}
```

### settings

```json
{
  "settings": {
    "tunnel_port_start": 100,
    "web_port_start": 800,
    "iperf_iran_port_start": 5001,
    "iperf_kharej_port": 5201,
    "excluded_ports": [22, 80, 443, 8080],
    "subnet_start": "10.10.10.0/24",
    "profiles": ["speed", "stable", "balanced"],
    "token_per_connection": true
  }
}
```

**پارامترها:**
- `tunnel_port_start`: پورت شروع تانل‌ها
- `web_port_start`: پورت شروع Web Interface
- `iperf_iran_port_start`: پورت شروع iperf3 در ایران
- `iperf_kharej_port`: پورت iperf3 در خارج
- `excluded_ports`: پورت‌هایی که نباید استفاده شوند
- `subnet_start`: Subnet شروع برای TUN transports
- `profiles`: لیست پروفایل‌های مورد نظر
- `token_per_connection`: یک token برای هر connection

### connections

```json
{
  "connections": [
    {
      "iran": "Tehran-Main",
      "kharej": "Germany-Hetzner",
      "transports": "all"
    }
  ]
}
```

**transports options:**
- `"all"`: همه transport ها
- `["tcp", "ws", ...]`: لیست خاص

---

## 🎯 پروفایل‌های بهینه‌سازی

### Speed Profile
```toml
channel_size = 4096
heartbeat = 20
mux_con = 128
connection_pool = 16
aggressive_pool = true
mtu = 1400
```

**بهترین برای:**
- دانلود و آپلود سرعت بالا
- پهنای باند بالا
- استریم و محتوای سنگین

### Stable Profile
```toml
channel_size = 2048
heartbeat = 40
mux_con = 64
connection_pool = 8
aggressive_pool = false
mtu = 1400
```

**بهترین برای:**
- شبکه‌های ناپایدار
- اتصالات بلندمدت
- تانل‌های مهم

### Balanced Profile
```toml
channel_size = 2048
heartbeat = 20
mux_con = 64
connection_pool = 8
aggressive_pool = false
mtu = 1400
```

**بهترین برای:**
- استفاده روزمره
- تعادل سرعت و پایداری
- استفاده عمومی

---

## 🔧 مدیریت سرویس‌ها

### لیست سرویس‌ها

```bash
systemctl list-units 'backhaul-iran*' --all
systemctl list-units 'backhaul-kharej*' --all
```

### مدیریت یک سرویس

```bash
# استاتوس
systemctl status backhaul-iran100-tcp-speed

# استارت
systemctl start backhaul-iran100-tcp-speed

# استاپ
systemctl stop backhaul-iran100-tcp-speed

# ری‌استارت
systemctl restart backhaul-iran100-tcp-speed

# لاگ
journalctl -u backhaul-iran100-tcp-speed -f
```

### مدیریت همه سرویس‌ها

```bash
# استاپ همه
bash stop-services.sh

# ری‌استارت همه
bash restart-services.sh

# حذف همه
bash remove-services.sh
```

---

## 📊 Web Interface

هر تانل یک Web Interface دارد که اطلاعات real-time ارائه می‌دهد:

```
http://SERVER_IP:800   # اولین تانل
http://SERVER_IP:801   # دومین تانل
http://SERVER_IP:802   # سومین تانل
...
```

**اطلاعات موجود:**
- وضعیت اتصال
- Transfer statistics
- Connection count
- Uptime

---

## 🧪 تست با iperf3

### روی Kharej:

```bash
iperf3 -s -B 127.0.0.1 -p 5201
```

### روی Iran:

```bash
# تانل اول
iperf3 -c 127.0.0.1 -p 5001 -t 30

# تانل دوم
iperf3 -c 127.0.0.1 -p 5002 -t 30

# تانل سوم
iperf3 -c 127.0.0.1 -p 5003 -t 30
```

---

## 🛠 State Manager

ابزار مدیریت state.json:

```bash
# حالت تعاملی
python3 update-state.py

# نمایش خلاصه
python3 update-state.py summary

# نمایش token ها
python3 update-state.py tokens

# نمایش config ها
python3 update-state.py configs 50
```

---

## 📚 مستندات اضافی

- [QUICKSTART.md](QUICKSTART.md) - راهنمای سریع
- [TRANSPORTS-GUIDE.md](TRANSPORTS-GUIDE.md) - راهنمای Transport ها
- [PROFILES-GUIDE.md](PROFILES-GUIDE.md) - راهنمای پروفایل‌ها
- [OPTIMIZATION-GUIDE.md](OPTIMIZATION-GUIDE.md) - راهنمای بهینه‌سازی
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - رفع مشکلات

---

## ⚠️ نکات مهم

### ۱. مسیر فایل باینری

```bash
# ✅ درست
/root/backhaul-core/backhaul_premium
/root/backhaul-core/backhaul_premium.tar.gz

# ❌ اشتباه
/root/backhaul_premium
/tmp/backhaul_premium
```

### ۲. Subnet برای TUN

- هر TUN transport یک subnet منحصر به فرد دارد
- Subnet ها باید در Iran و Kharej یکسان باشند
- فرمت: `10.10.X.0/24` (X = 10, 20, 30, ...)

### ۳. Token

- هر connection یک token مشترک دارد
- Iran و Kharej همان token را استفاده می‌کنند
- Token ها در state.json ذخیره می‌شوند

### ۴. نام سرویس‌ها

الگو: `backhaul-{iran/kharej}{port}-{transport}-{profile}`

مثال:
- `backhaul-iran100-tcp-speed`
- `backhaul-iran101-tcpmux-v2-stable`
- `backhaul-kharej100-tcp-speed`

---

## 🐛 رفع مشکلات

### خطا: Service failed to start

```bash
# چک لاگ
journalctl -u backhaul-iran100-tcp-speed -n 50

# چک config
cat /root/backhaul-core/iran100-tcp-speed.toml

# چک binary
ls -la /root/backhaul-core/backhaul_premium
```

### خطا: Permission denied

```bash
chmod +x /root/backhaul-core/backhaul_premium
```

### خطا: Port already in use

```bash
# چک پورت
ss -tlnp | grep 100

# آپدیت excluded_ports در config.json
```

---

## 📞 پشتیبانی

برای سوالات و گزارش مشکلات:
- Telegram: @Gozar_XRay
- GitHub Issues

---

**نسخه:** 1.0.0  
**تاریخ:** 2026-01-05  
**سازگار با:** Backhaul Premium v1.3.0+
