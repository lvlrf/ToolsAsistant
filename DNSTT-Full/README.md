# 🚀 DNS Tunnel MegaPrompt - slipstream + WireGuard + SOCKS5

## نمای کلی پروژه

این پروژه یک تانل DNS با پهنای باند بالا (~500 Mbps) ایجاد میکنه که از **slipstream** استفاده میکنه و ترافیک رو از طریق ۵۰۰ DNS resolver عبور میده.

```
[اینترنت آزاد]
       ▲
       │
[سرور خارج - slipstream-server]
       ▲
       │ (UDP 53)
[500× DNS Resolver]
       │
       ▼
[سرور ایران - slipstream-client]
       │
       ├── WireGuard Server (:51820)
       └── SOCKS5 Proxy (:1080)
              │
              ▼
       [کاربران نهایی]
```

---

## 📋 مشخصات سرورها

### سرور خارج:
- CPU: 16 core
- RAM: 32 GB
- Network: 1 Gbps
- OS: Ubuntu 22.04 / 24.04
- Location: نزدیک به ایران (هلند/آلمان)

### سرور ایران:
- CPU: 16 core
- RAM: 32 GB  
- Network: 1 Gbps
- OS: Ubuntu 22.04 / 24.04

---

## 📁 ساختار فایل‌ها

```
dns-tunnel-megaprompt/
├── README.md                          # این فایل
├── configs/                           # فایل‌های تنظیمات
│   ├── server.conf                    # slipstream server config
│   ├── client.conf                    # slipstream client config
│   ├── resolvers.txt                  # لیست 500 DNS resolver
│   ├── slipstream-server.service      # systemd service (سرور خارج)
│   ├── slipstream-client.service      # systemd service (سرور ایران)
│   ├── wg0.conf                       # WireGuard server
│   ├── client-wg0.conf                # WireGuard client نمونه
│   ├── danted.conf                    # SOCKS5 config
│   ├── danted.service                 # SOCKS5 systemd service
│   └── 99-tunnel-tuning.conf          # Kernel tuning
├── scripts/                           # اسکریپت‌های نصب و مدیریت
│   ├── install-server.sh              # نصب خودکار سرور خارج
│   ├── install-client.sh              # نصب خودکار سرور ایران
│   ├── setup-dns.sh                   # راهنمای DNS setup
│   ├── test-speed.sh                  # تست سرعت
│   ├── monitor.sh                     # مانیتورینگ
│   ├── add-wg-client.sh               # اضافه کردن WireGuard client
│   └── troubleshoot.sh                # عیب‌یابی
├── docs/                              # مستندات
│   ├── DNS-SETUP.md                   # راهنمای DNS
│   └── TROUBLESHOOTING.md             # حل مشکلات
└── downloads/                         # فایل‌های آفلاین
    └── offline-packages.txt           # لیست بسته‌ها برای دانلود
```

---

## 🚀 راهنمای نصب سریع

### مرحله ۱: آماده‌سازی

1. **دانلود این پروژه** (همه فایل‌ها)
2. **آماده کردن فایل `resolvers.txt`** (500 IP)
3. **تنظیم DNS** (مطابق `docs/DNS-SETUP.md`)

### مرحله ۲: نصب سرور خارج

```bash
# انتقال فایل‌ها به سرور خارج
scp -r dns-tunnel-megaprompt root@SERVER_IP:/root/

# اجرای اسکریپت نصب
ssh root@SERVER_IP
cd /root/dns-tunnel-megaprompt
chmod +x scripts/install-server.sh
./scripts/install-server.sh
```

### مرحله ۳: نصب سرور ایران

```bash
# انتقال فایل‌ها به سرور ایران (از طریق USB یا transfer)
# یا اگر دسترسی SSH داری:
scp -r dns-tunnel-megaprompt root@IRAN_SERVER_IP:/root/

# اجرای اسکریپت نصب
ssh root@IRAN_SERVER_IP
cd /root/dns-tunnel-megaprompt
chmod +x scripts/install-client.sh
./scripts/install-client.sh
```

### مرحله ۴: تست و راه‌اندازی

```bash
# روی سرور ایران
cd /root/dns-tunnel-megaprompt
./scripts/test-speed.sh
./scripts/monitor.sh
```

---

## 📦 نصب آفلاین (بدون اینترنت)

اگر سرور ایران دسترسی به اینترنت نداره:

1. **روی یک سیستم با اینترنت:**
```bash
cd dns-tunnel-megaprompt/downloads
./download-offline-packages.sh
```

2. **انتقال کل پوشه به سرور ایران** (USB / FTP / SCP)

3. **نصب از فایل‌های آفلاین:**
```bash
cd dns-tunnel-megaprompt/downloads
./install-offline-packages.sh
```

---

## 🔧 تنظیمات پیش‌فرض

| سرویس | پورت | پروتکل |
|--------|------|--------|
| slipstream-server | 53 | UDP |
| WireGuard | 51820 | UDP |
| SOCKS5 | 1080 | TCP |

### شبکه‌های داخلی:
- **slipstream TUN:** 10.0.0.0/24
- **WireGuard:** 10.8.0.0/24

---

## 📊 پهنای باند مورد انتظار

| تعداد Resolver | پهنای باند تخمینی |
|----------------|-------------------|
| 100 | ~80-100 Mbps |
| 200 | ~160-200 Mbps |
| 500 | ~400-500 Mbps |

---

## 🆘 مشکل داری؟

1. **مطالعه:** `docs/TROUBLESHOOTING.md`
2. **اجرای عیب‌یابی:** `./scripts/troubleshoot.sh`
3. **بررسی logs:**
```bash
journalctl -u slipstream-server -f    # سرور خارج
journalctl -u slipstream-client -f    # سرور ایران
journalctl -u wg-quick@wg0 -f         # WireGuard
journalctl -u danted -f               # SOCKS5
```

---

## 📞 اطلاعات تماس

- **Domain:** irihost.com
- **Tunnel Domain:** t.irihost.com
- **Telegram:** @drconnect
- **Phone:** +98 912 741 9412

---

## 🔒 نکات امنیتی

⚠️ **هشدار:** کلیدها و اطلاعات حساس رو در فایل‌های config پیدا میکنی - **حتماً تغییرشون بده!**

- کلید WireGuard: خودکار generate میشه
- کلید slipstream: در فایل config موجوده (باید عوض کنی)
- SOCKS5 authentication: در `danted.conf` تنظیم کن

---

## 📝 License

این پروژه برای استفاده شخصی DrConnect (@drconnect) ساخته شده.

---

## ✅ Checklist نصب

- [ ] DNS تنظیم شد (t.irihost.com)
- [ ] slipstream روی سرور خارج نصب شد
- [ ] slipstream روی سرور ایران نصب شد
- [ ] فایل resolvers.txt با 500 IP آماده شد
- [ ] WireGuard راه‌اندازی شد
- [ ] SOCKS5 راه‌اندازی شد
- [ ] Kernel tuning اعمال شد
- [ ] تست سرعت انجام شد
- [ ] مانیتورینگ راه‌اندازی شد

---

**نسخه:** 1.0  
**تاریخ:** ۱۴۰۳/۱۰/۲۷  
**توسعه‌دهنده:** DrConnect
