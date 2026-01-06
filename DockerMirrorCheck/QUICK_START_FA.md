# 🚀 راهنمای نصب سریع - IranServerDockerMirror v2.0

## ⚡ نصب فوری (یک خط!)

```bash
curl -fsSL https://raw.githubusercontent.com/YOUR_REPO/IranServerDockerMirror_v2.sh | sudo bash
```

یا دانلود و اجرا:

```bash
wget https://raw.githubusercontent.com/YOUR_REPO/IranServerDockerMirror_v2.sh
chmod +x IranServerDockerMirror_v2.sh
sudo ./IranServerDockerMirror_v2.sh
```

---

## 📋 پیش‌نیازها

✅ سیستم‌عامل: Ubuntu/Debian (18.04+)  
✅ Docker نصب شده باشد  
✅ دسترسی root (sudo)  
✅ اتصال اینترنت  

---

## 🎯 روش‌های نصب

### روش 1️⃣: استفاده از فایل محلی (توصیه می‌شود)

```bash
# 1. کپی فایل به سرور
scp IranServerDockerMirror_v2.sh user@server:/tmp/

# 2. اجرا در سرور
ssh user@server
cd /tmp
sudo bash IranServerDockerMirror_v2.sh
```

### روش 2️⃣: نصب به عنوان ابزار سیستمی

```bash
# نصب
sudo cp IranServerDockerMirror_v2.sh /usr/local/bin/docker-mirror
sudo chmod +x /usr/local/bin/docker-mirror

# اجرا از هر جا
docker-mirror

# حذف
sudo rm /usr/local/bin/docker-mirror
```

### روش 3️⃣: اجرای خودکار هفتگی

```bash
# نصب ابتدا
sudo cp IranServerDockerMirror_v2.sh /usr/local/bin/docker-mirror
sudo chmod +x /usr/local/bin/docker-mirror

# افزودن به cron (هر یکشنبه ساعت 3 صبح)
sudo crontab -e

# اضافه کنید:
0 3 * * 0 /usr/local/bin/docker-mirror >> /var/log/docker-mirror-weekly.log 2>&1
```

### روش 4️⃣: اجرای Manual بدون نصب

```bash
sudo bash IranServerDockerMirror_v2.sh
```

---

## 🔍 بررسی قبل از نصب

```bash
# 1. بررسی Docker
docker --version
# خروجی مورد انتظار: Docker version 20.10.x یا بالاتر

# 2. بررسی دسترسی root
sudo whoami
# خروجی مورد انتظار: root

# 3. بررسی curl و jq
curl --version
# اگر نداشتید: sudo apt install curl -y

# 4. بررسی اتصال به میرورها
curl -I https://focker.ir/v2/
# خروجی مورد انتظار: HTTP/2 200 یا 401
```

---

## 📊 مثال خروجی موفق

```
╔════════════════════════════════════════════════════════════╗
║     IranServerDockerMirror v2.0 - Enhanced Edition         ║
╚════════════════════════════════════════════════════════════╝

ℹ Script started at 2025-01-03 14:30:45
ℹ Docker version: 24.0

═══════════════════════════════════════════════════
  Phase 1: Testing Mirror Availability
═══════════════════════════════════════════════════
ℹ Testing /v2 endpoints in parallel...
✓ Found 12 alive mirrors

═══════════════════════════════════════════════════
  Phase 2: Testing Manifest Speed & Accessibility
═══════════════════════════════════════════════════
  0.234s - https://focker.ir (HTTP 200)
  0.456s - https://docker.arvancloud.ir (HTTP 200)

✓ Selected Mirrors:
  [1] https://focker.ir
  [2] https://docker.arvancloud.ir

═══════════════════════════════════════════════════
  Phase 3: Updating Docker Configuration
═══════════════════════════════════════════════════
✓ Configuration updated successfully

═══════════════════════════════════════════════════
  Phase 4: Restarting Docker Service
═══════════════════════════════════════════════════
✓ Docker service restarted successfully

═══════════════════════════════════════════════════
  Phase 5: Verification Test
═══════════════════════════════════════════════════
✓ Pull completed in 3s
✓ Container test passed

✓ All operations completed successfully!
```

---

## ✅ تست نصب موفق

```bash
# 1. بررسی تنظیمات
cat /etc/docker/daemon.json

# باید ببینید:
{
  "registry-mirrors": [
    "https://focker.ir",
    "https://docker.arvancloud.ir"
  ]
}

# 2. بررسی Docker Info
docker info | grep -A 5 "Registry Mirrors"

# 3. تست Pull
docker pull nginx:alpine

# باید سریع‌تر از قبل باشد!
```

---

## 🔧 تنظیمات پیشرفته

### تغییر تعداد Worker ها

```bash
# ویرایش فایل
nano IranServerDockerMirror_v2.sh

# تغییر خط:
readonly MAX_WORKERS=10  # به 5 یا 15 تغییر دهید
```

### تغییر Timeout ها

```bash
# برای شبکه بسیار ضعیف:
readonly V2_TIMEOUT=10
readonly MANIFEST_TIMEOUT=15

# برای شبکه سریع:
readonly V2_TIMEOUT=3
readonly MANIFEST_TIMEOUT=5
```

### افزودن میرور دلخواه

```bash
# ویرایش فایل
nano IranServerDockerMirror_v2.sh

# اضافه کردن به آرایه CANDIDATES:
CANDIDATES=(
  # میرورهای موجود...
  "https://your-custom-mirror.com"  # میرور شما
)
```

---

## 🐛 عیب‌یابی

### مشکل 1: "This script must be run as root"

**راه‌حل:**
```bash
# استفاده از sudo
sudo bash IranServerDockerMirror_v2.sh

# یا اجرا با root
su -
bash IranServerDockerMirror_v2.sh
```

### مشکل 2: "docker: command not found"

**راه‌حل:**
```bash
# نصب Docker
curl -fsSL https://get.docker.com | sudo bash

# یا:
sudo apt update
sudo apt install docker.io -y
```

### مشکل 3: "No mirrors passed /v2 check"

**علت:** اینترنت قطع یا فیلترینگ سنگین

**راه‌حل:**
```bash
# 1. بررسی اتصال
ping -c 3 8.8.8.8

# 2. تست دستی میرورها
curl -I https://focker.ir/v2/
curl -I https://docker.arvancloud.ir/v2/

# 3. استفاده از VPN/Proxy موقت
export http_proxy=socks5://127.0.0.1:1080
export https_proxy=socks5://127.0.0.1:1080
```

### مشکل 4: "Failed to restart Docker"

**راه‌حل:**
```bash
# بررسی خطا
journalctl -u docker -n 50

# ریست کامل
sudo systemctl stop docker
sudo systemctl start docker
sudo systemctl status docker

# اگر باز هم مشکل دارد:
sudo cat /etc/docker/daemon.json  # بررسی syntax
```

### مشکل 5: Pull همچنان کند است

**راه‌حل:**
```bash
# 1. بررسی میرورهای فعال
docker info | grep "Registry Mirrors"

# 2. افزودن DNS
sudo nano /etc/docker/daemon.json

{
  "registry-mirrors": [
    "https://focker.ir",
    "https://docker.arvancloud.ir"
  ],
  "dns": ["178.22.122.100", "185.51.200.2"]
}

# 3. Restart
sudo systemctl restart docker

# 4. تست مجدد
time docker pull nginx:alpine
```

---

## 📂 ساختار فایل‌ها پس از نصب

```
/etc/docker/
├── daemon.json                          # تنظیمات اصلی
└── daemon.json.backup.20250103_143052   # بکاپ خودکار

/var/log/
└── docker-mirror-setup.log              # لاگ کامل عملیات

/usr/local/bin/
└── docker-mirror                        # ابزار نصب شده (اختیاری)

/tmp/
└── docker-mirror-*.tmp                  # فایل‌های موقت (خودکار حذف می‌شوند)
```

---

## 🔄 به‌روزرسانی

```bash
# حذف نسخه قبلی
sudo rm /usr/local/bin/docker-mirror

# دانلود نسخه جدید
wget https://raw.githubusercontent.com/YOUR_REPO/IranServerDockerMirror_v2.sh

# نصب
sudo cp IranServerDockerMirror_v2.sh /usr/local/bin/docker-mirror
sudo chmod +x /usr/local/bin/docker-mirror

# اجرا
docker-mirror
```

---

## 🗑️ حذف کامل

```bash
# 1. بازگشت به تنظیمات پیش‌فرض
sudo nano /etc/docker/daemon.json
# حذف کنید: "registry-mirrors": [...]

# یا استفاده از بکاپ:
sudo cp /etc/docker/daemon.json.backup.* /etc/docker/daemon.json

# 2. Restart Docker
sudo systemctl restart docker

# 3. حذف ابزار
sudo rm /usr/local/bin/docker-mirror

# 4. حذف لاگ‌ها
sudo rm /var/log/docker-mirror-*.log

# 5. تست
docker info | grep "Registry Mirrors"
# نباید چیزی نشان دهد
```

---

## 💡 نکات مهم

### ✅ Do's (انجام دهید)

- همیشه با `sudo` اجرا کنید
- قبل از اجرا Docker را بررسی کنید
- لاگ‌ها را برای عیب‌یابی نگه دارید
- بکاپ‌های خودکار را حفظ کنید
- در production ابتدا در staging تست کنید

### ❌ Don'ts (انجام ندهید)

- بدون root اجرا نکنید
- daemon.json را دستی ویرایش نکنید (بعد از نصب)
- میرورهای نامعتبر اضافه نکنید
- Timeout ها را خیلی کوتاه نکنید
- Docker را در حین pull متوقف نکنید

---

## 🎓 سناریوهای کاربردی

### سناریو 1: نصب در سرور جدید

```bash
# 1. نصب Docker
curl -fsSL https://get.docker.com | sudo bash

# 2. نصب Mirror Setup
sudo bash IranServerDockerMirror_v2.sh

# 3. تست
docker pull hello-world

# تمام! 🎉
```

### سناریو 2: به‌روزرسانی سرور موجود

```bash
# 1. بررسی تنظیمات فعلی
cat /etc/docker/daemon.json

# 2. اجرای اسکریپت (خودکار backup می‌گیرد)
sudo bash IranServerDockerMirror_v2.sh

# 3. مقایسه
cat /etc/docker/daemon.json
cat /etc/docker/daemon.json.backup.*
```

### سناریو 3: عیب‌یابی سرعت Pull

```bash
# 1. بررسی سرعت فعلی
time docker pull nginx:alpine
# مثلاً: 2m 30s

# 2. نصب Mirror
sudo bash IranServerDockerMirror_v2.sh

# 3. حذف cache و تست مجدد
docker rmi nginx:alpine
time docker pull nginx:alpine
# مثلاً: 15s - بهبود 10 برابری! 🚀
```

### سناریو 4: تنظیم Cluster (چند سرور)

```bash
# روی سرور اول:
sudo bash IranServerDockerMirror_v2.sh

# کپی تنظیمات به بقیه سرورها:
MIRRORS=$(jq -r '.["registry-mirrors"]' /etc/docker/daemon.json)

# روی سرورهای دیگر:
echo "{\"registry-mirrors\": $MIRRORS}" | sudo tee /etc/docker/daemon.json
sudo systemctl restart docker
```

---

## 📞 پشتیبانی

### لاگ‌های مفید برای عیب‌یابی:

```bash
# 1. لاگ اسکریپت
cat /var/log/docker-mirror-setup.log

# 2. لاگ Docker
journalctl -u docker -n 100

# 3. تنظیمات فعلی
cat /etc/docker/daemon.json

# 4. وضعیت Docker
systemctl status docker

# 5. میرورهای فعال
docker info | grep -A 10 "Registry"
```

### دریافت کمک:

1. بررسی [عیب‌یابی](#-عیب‌یابی)
2. خواندن [راهنمای جامع](COMPARISON_GUIDE_FA.md)
3. بررسی لاگ‌ها
4. گزارش مشکل با اطلاعات کامل:
   - نسخه Ubuntu/Debian
   - نسخه Docker
   - خروجی کامل اسکریپت
   - محتوای لاگ فایل

---

## ⏱️ زمان‌بندی نصب

| مرحله | زمان تقریبی |
|-------|-------------|
| بررسی پیش‌نیازها | 1 دقیقه |
| دانلود فایل | 10 ثانیه |
| اجرای اسکریپت | 30-45 ثانیه |
| تست و تأیید | 1 دقیقه |
| **جمع کل** | **~3 دقیقه** |

---

## 🎯 چک‌لیست موفقیت

- [ ] Docker نصب است
- [ ] دسترسی root دارید
- [ ] اینترنت متصل است
- [ ] فایل دانلود شد
- [ ] chmod +x اجرا شد
- [ ] اسکریپت با sudo اجرا شد
- [ ] پیام "All operations completed successfully" دیدید
- [ ] daemon.json به‌روز شد
- [ ] Docker restart شد
- [ ] Pull test موفق بود
- [ ] سرعت pull بهبود یافت

همه ✅ شد؟ **تبریک! نصب موفقیت‌آمیز بود!** 🎉

---

## 🚦 وضعیت‌های ممکن

### 🟢 موفق (Success)
```
✓ All operations completed successfully!
✓ You can now use: docker pull <image>
```
**اقدام:** هیچ کاری لازم نیست، استفاده کنید!

### 🟡 موفق با هشدار (Success with Warning)
```
✓ Configuration updated
⚠ Pull test failed, but configuration was updated
```
**اقدام:** بررسی اتصال اینترنت، اجرای مجدد

### 🔴 ناموفق (Failure)
```
✗ Failed to find suitable mirrors
✗ No mirrors passed /v2 check
```
**اقدام:** بررسی [عیب‌یابی](#-عیب‌یابی)

---

**آخرین به‌روزرسانی:** 2025-01-03  
**نسخه:** 2.0  
**سازگار با:** Ubuntu 18.04+, Debian 10+, Docker 19.03+
