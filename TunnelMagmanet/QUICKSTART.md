# راهنمای سریع - Backhaul Bulk Generator

## 🚀 ۵ دقیقه تا راه‌اندازی!

---

### مرحله ۱: آماده‌سازی فایل‌ها

```bash
# دانلود generator
unzip backhaul-bulk-generator-v1.0.zip
cd backhaul-bulk-generator

# دانلود Backhaul Premium binary
# از لینک رسمی دانلود کنید و نام فایل را تغییر ندهید:
# backhaul_premium.tar.gz
```

---

### مرحله ۲: ویرایش config.json

```json
{
  "binary_config": {
    "premium": {
      "path": "/root/backhaul-core",
      "filename": "backhaul_premium"
    }
  },

  "settings": {
    "profiles": ["balanced"]
  },

  "iran_servers": [
    {"name": "Tehran", "ip": "YOUR_IRAN_IP"}
  ],

  "kharej_servers": [
    {"name": "Germany", "ip": "YOUR_KHAREJ_IP"}
  ],

  "connections": [
    {
      "iran": "Tehran",
      "kharej": "Germany",
      "transports": ["tcp", "tcpmux", "ws", "tcptun"]
    }
  ]
}
```

**نکته:** فقط profile `balanced` را انتخاب کنید برای شروع.

---

### مرحله ۳: اجرای Generator

```bash
python3 generator.py
```

**خروجی:**
```
[OK] Tehran -> Germany: tcp-balanced (Port 100)
[OK] Tehran -> Germany: tcpmux-v1-balanced (Port 101)
[OK] Tehran -> Germany: tcpmux-v2-balanced (Port 102)
[OK] Tehran -> Germany: ws-balanced (Port 103)
[OK] Tehran -> Germany: tcptun-balanced (Port 104)

[OK] Generated 5 configurations successfully!
```

---

### مرحله ۴: آپلود به سرورها

#### الف) آپلود Binary:

```bash
# Iran
scp backhaul_premium.tar.gz root@YOUR_IRAN_IP:/root/backhaul-core/

# Kharej
scp backhaul_premium.tar.gz root@YOUR_KHAREJ_IP:/root/backhaul-core/
```

#### ب) آپلود Config ها:

```bash
# Iran
scp output/Iran/Tehran/*.toml root@YOUR_IRAN_IP:/root/backhaul-core/
scp output/Iran/Tehran/*.sh root@YOUR_IRAN_IP:/root/backhaul-core/

# Kharej
scp output/Kharej/Germany/*.toml root@YOUR_KHAREJ_IP:/root/backhaul-core/
scp output/Kharej/Germany/*.sh root@YOUR_KHAREJ_IP:/root/backhaul-core/
```

---

### مرحله ۵: نصب

```bash
# Iran
ssh root@YOUR_IRAN_IP
cd /root/backhaul-core
bash install-services.sh

# Kharej
ssh root@YOUR_KHAREJ_IP
cd /root/backhaul-core
bash install-services.sh
```

---

## ✅ چک کردن

### Iran:

```bash
# لیست سرویس‌ها
systemctl list-units 'backhaul-iran*'

# چک یک سرویس
systemctl status backhaul-iran100-tcp-balanced

# لاگ
journalctl -u backhaul-iran100-tcp-balanced -f
```

### Kharej:

```bash
# لیست سرویس‌ها
systemctl list-units 'backhaul-kharej*'

# چک یک سرویس
systemctl status backhaul-kharej100-tcp-balanced
```

---

## 🧪 تست سرعت

### Kharej:

```bash
iperf3 -s -B 127.0.0.1 -p 5201
```

### Iran:

```bash
iperf3 -c 127.0.0.1 -p 5001 -t 30
```

---

## 🌐 Web Interface

```
http://YOUR_IRAN_IP:800   # iran100-tcp-balanced
http://YOUR_IRAN_IP:801   # iran101-tcpmux-v1-balanced
http://YOUR_IRAN_IP:802   # iran102-tcpmux-v2-balanced
...
```

---

## ⚙️ بهینه‌سازی (اختیاری)

```bash
# Iran
ssh root@YOUR_IRAN_IP
cd /root/backhaul-core
bash optimize-iran.sh

# Kharej  
ssh root@YOUR_KHAREJ_IP
cd /root/backhaul-core
bash optimize-kharej.sh
```

**نکته:** بعد از بهینه‌سازی سرور باید reboot شود.

---

## 🛠 مدیریت سرویس‌ها

```bash
# استاپ همه
bash stop-services.sh

# ری‌استارت همه
bash restart-services.sh

# حذف همه
bash remove-services.sh
```

---

## 🎯 مرحله بعدی

اکنون که سیستم شما کار می‌کند:

1. **اضافه کردن سرورها:** سرورهای بیشتری به config.json اضافه کنید
2. **تست Transport ها:** transport های مختلف را امتحان کنید
3. **پروفایل‌ها:** profiles دیگر (speed, stable) را امتحان کنید
4. **مستندات:** [README.md](README.md) را برای جزئیات بیشتر مطالعه کنید

---

## ❓ مشکل دارید؟

[TROUBLESHOOTING.md](TROUBLESHOOTING.md) را مطالعه کنید.

---

**موفق باشید!** 🎉
