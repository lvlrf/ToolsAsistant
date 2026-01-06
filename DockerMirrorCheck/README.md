# 🐳 IranServerDockerMirror v2.0

<div dir="rtl">

**انتخاب خودکار و هوشمند بهترین Docker Registry Mirror برای سرورهای ایران**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-2.0-green.svg)]()
[![Bash](https://img.shields.io/badge/bash-5.0+-orange.svg)]()
[![Platform](https://img.shields.io/badge/platform-Ubuntu%20%7C%20Debian-lightgrey.svg)]()

</div>

---

## 📖 Table of Contents | فهرست

- [🇮🇷 نسخه فارسی](#-نسخه-فارسی)
- [🇬🇧 English Version](#-english-version)

---

<div dir="rtl">

# 🇮🇷 نسخه فارسی

## 🎯 ویژگی‌های کلیدی

- ⚡ **تست موازی** - سرعت اجرا 5-10 برابر سریعتر
- 🎨 **خروجی رنگی** - رابط کاربری زیبا و قابل فهم
- 📝 **سیستم Logging** - ثبت کامل تمام عملیات
- 🔄 **Retry هوشمند** - 3 بار تلاش مجدد برای Docker restart
- 🛡️ **امنیت بالا** - Validation کامل و backup خودکار
- 🌐 **18 میرور** - شامل میرورهای ایرانی و بین‌المللی
- 🧹 **Cleanup خودکار** - حذف فایل‌های موقت
- ✅ **تست واقعی** - Pull و اجرای تصویر hello-world

## 📊 مقایسه سریع

| ویژگی | نسخه قبلی | نسخه 2.0 |
|-------|-----------|----------|
| سرعت اجرا | 160 ثانیه | **32 ثانیه** |
| تست میرورها | سریالی | **موازی** |
| Logging | ساده | **کامل + فایل** |
| Retry | ندارد | **3 بار** |
| UI | متن ساده | **رنگی و زیبا** |
| Timeout | کوتاه | **بهینه شده** |

## 🚀 نصب سریع

### روش 1: اجرای مستقیم

```bash
# دانلود
wget https://raw.githubusercontent.com/YOUR_REPO/IranServerDockerMirror_v2.sh

# اجازه اجرا
chmod +x IranServerDockerMirror_v2.sh

# اجرا با sudo
sudo ./IranServerDockerMirror_v2.sh
```

### روش 2: نصب به عنوان ابزار سیستمی

```bash
# نصب
sudo cp IranServerDockerMirror_v2.sh /usr/local/bin/docker-mirror
sudo chmod +x /usr/local/bin/docker-mirror

# استفاده
docker-mirror
```

### روش 3: نسخه LITE (برای شبکه ضعیف)

```bash
sudo ./IranServerDockerMirror_LITE.sh
```

## 📋 پیش‌نیازها

- ✅ سیستم‌عامل: Ubuntu 18.04+ یا Debian 10+
- ✅ Docker نصب شده
- ✅ دسترسی root (sudo)
- ✅ اتصال اینترنت

## 🎬 مثال خروجی

```
╔════════════════════════════════════════════════════════════╗
║     IranServerDockerMirror v2.0 - Enhanced Edition         ║
╚════════════════════════════════════════════════════════════╝

ℹ Script started at 2025-01-03 14:30:45

═══════════════════════════════════════════════════
  Phase 1: Testing Mirror Availability
═══════════════════════════════════════════════════
✓ Found 12 alive mirrors

═══════════════════════════════════════════════════
  Phase 2: Testing Manifest Speed
═══════════════════════════════════════════════════
  0.234s - https://focker.ir (HTTP 200)
  0.456s - https://docker.arvancloud.ir (HTTP 200)

✓ Selected Mirrors:
  [1] https://focker.ir
  [2] https://docker.arvancloud.ir

✓ All operations completed successfully!
```

## 🗂️ نسخه‌های موجود

### نسخه 2.0 (استاندارد) - توصیه می‌شود ✨

- تست موازی برای سرعت بالا
- رابط کاربری کامل
- Logging جامع
- مناسب 90% موارد استفاده

**استفاده:**
```bash
sudo ./IranServerDockerMirror_v2.sh
```

### نسخه LITE (سبک) - برای شرایط خاص 🪶

- تست سریالی برای پایداری بیشتر
- Timeout های طولانی‌تر
- مصرف منابع کمتر
- مناسب: شبکه خیلی ضعیف، منابع محدود

**استفاده:**
```bash
sudo ./IranServerDockerMirror_LITE.sh
```

## 📚 مستندات کامل

- 📖 [راهنمای نصب سریع](QUICK_START_FA.md) - شروع در 5 دقیقه
- 📊 [مقایسه و بهبودها](COMPARISON_GUIDE_FA.md) - تحلیل جامع
- 🔧 [عیب‌یابی](QUICK_START_FA.md#-عیب‌یابی) - حل مشکلات رایج

## 🌐 میرورهای پشتیبانی شده

### ایرانی (اولویت اول)
- https://focker.ir
- https://docker.arvancloud.ir
- https://registry.docker.ir
- https://hub.hamdocker.ir
- https://docker.iranrepo.ir
- https://mirror.amin.ac.ir
- و...

### بین‌المللی (Fallback)
- https://docker.m.daocloud.io
- https://dockerproxy.com
- https://hub-mirror.c.163.com
- و...

## ⚙️ تنظیمات پیشرفته

### تغییر تعداد Worker ها (موازی)

```bash
# ویرایش فایل
nano IranServerDockerMirror_v2.sh

# تغییر خط:
readonly MAX_WORKERS=10  # 5-15 توصیه می‌شود
```

### تنظیم Timeout ها

```bash
# شبکه قوی
readonly V2_TIMEOUT=3
readonly MANIFEST_TIMEOUT=5

# شبکه ضعیف
readonly V2_TIMEOUT=10
readonly MANIFEST_TIMEOUT=15
```

### افزودن میرور دلخواه

```bash
# در آرایه CANDIDATES اضافه کنید:
CANDIDATES=(
  # میرورهای موجود...
  "https://your-mirror.com"
)
```

## 🔄 اجرای خودکار

### اجرای هفتگی

```bash
# افزودن به cron
sudo crontab -e

# اضافه کنید:
0 3 * * 0 /usr/local/bin/docker-mirror >> /var/log/docker-mirror-weekly.log 2>&1
```

## 🐛 عیب‌یابی

### خطا: "No mirrors passed /v2 check"

```bash
# تست دستی
curl -I https://focker.ir/v2/
curl -I https://docker.arvancloud.ir/v2/

# یا استفاده از نسخه LITE
sudo ./IranServerDockerMirror_LITE.sh
```

### خطا: "Failed to restart Docker"

```bash
# بررسی لاگ
journalctl -u docker -n 50

# ریست کامل
sudo systemctl stop docker
sudo systemctl start docker
```

### Pull همچنان کند است

```bash
# افزودن DNS ایرانی
sudo nano /etc/docker/daemon.json

{
  "registry-mirrors": [...],
  "dns": ["178.22.122.100", "185.51.200.2"]
}

sudo systemctl restart docker
```

## 📁 ساختار پروژه

```
IranServerDockerMirror/
├── IranServerDockerMirror_v2.sh      # نسخه اصلی (پیشرفته)
├── IranServerDockerMirror_LITE.sh    # نسخه سبک
├── README.md                         # این فایل
├── COMPARISON_GUIDE_FA.md            # راهنمای مقایسه
└── QUICK_START_FA.md                 # راهنمای شروع سریع
```

## 🤝 مشارکت

مشارکت‌ها خوش‌آمد هستند! لطفاً:

1. Fork کنید
2. Branch جدید بسازید (`git checkout -b feature/amazing`)
3. تغییرات را commit کنید (`git commit -am 'Add feature'`)
4. Push کنید (`git push origin feature/amazing`)
5. Pull Request ایجاد کنید

## 📞 پشتیبانی

- 📧 ایمیل: your-email@example.com
- 🐛 گزارش باگ: [Issues](https://github.com/YOUR_REPO/issues)
- 💬 بحث و گفتگو: [Discussions](https://github.com/YOUR_REPO/discussions)

## 📄 لایسنس

این پروژه تحت لایسنس MIT منتشر شده است - [LICENSE](LICENSE) را ببینید.

## 🙏 سپاسگزاری

- تمامی ارائه‌دهندگان میرورهای Docker در ایران
- جامعه Open Source
- تمامی کسانی که به بهبود این پروژه کمک کردند

## 🔗 لینک‌های مفید

- [مستندات Docker](https://docs.docker.com/)
- [Docker Registry Mirror](https://docs.docker.com/registry/recipes/mirror/)
- [Focker.ir](https://focker.ir)
- [ArvanCloud Docker](https://docker.arvancloud.ir)

---

</div>

# 🇬🇧 English Version

## 🎯 Key Features

- ⚡ **Parallel Testing** - 5-10x faster execution
- 🎨 **Colored Output** - Beautiful and clear UI
- 📝 **Comprehensive Logging** - Full operation tracking
- 🔄 **Smart Retry** - 3 attempts for Docker restart
- 🛡️ **High Security** - Complete validation & auto-backup
- 🌐 **18 Mirrors** - Iranian and international mirrors
- 🧹 **Auto Cleanup** - Automatic temp file removal
- ✅ **Real Testing** - Pull and run hello-world image

## 🚀 Quick Install

### Method 1: Direct Execution

```bash
# Download
wget https://raw.githubusercontent.com/YOUR_REPO/IranServerDockerMirror_v2.sh

# Make executable
chmod +x IranServerDockerMirror_v2.sh

# Run with sudo
sudo ./IranServerDockerMirror_v2.sh
```

### Method 2: Install as System Tool

```bash
# Install
sudo cp IranServerDockerMirror_v2.sh /usr/local/bin/docker-mirror
sudo chmod +x /usr/local/bin/docker-mirror

# Use
docker-mirror
```

### Method 3: LITE Version (for weak networks)

```bash
sudo ./IranServerDockerMirror_LITE.sh
```

## 📋 Prerequisites

- ✅ OS: Ubuntu 18.04+ or Debian 10+
- ✅ Docker installed
- ✅ Root access (sudo)
- ✅ Internet connection

## 🎬 Sample Output

```
╔════════════════════════════════════════════════════════════╗
║     IranServerDockerMirror v2.0 - Enhanced Edition         ║
╚════════════════════════════════════════════════════════════╝

ℹ Script started at 2025-01-03 14:30:45

═══════════════════════════════════════════════════
  Phase 1: Testing Mirror Availability
═══════════════════════════════════════════════════
✓ Found 12 alive mirrors

═══════════════════════════════════════════════════
  Phase 2: Testing Manifest Speed
═══════════════════════════════════════════════════
  0.234s - https://focker.ir (HTTP 200)
  0.456s - https://docker.arvancloud.ir (HTTP 200)

✓ Selected Mirrors:
  [1] https://focker.ir
  [2] https://docker.arvancloud.ir

✓ All operations completed successfully!
```

## 📚 Complete Documentation

- 📖 [Quick Start Guide](QUICK_START_FA.md)
- 📊 [Comparison & Improvements](COMPARISON_GUIDE_FA.md)
- 🔧 [Troubleshooting](QUICK_START_FA.md#troubleshooting)

## 🐛 Troubleshooting

### Error: "No mirrors passed /v2 check"

```bash
# Manual test
curl -I https://focker.ir/v2/

# Or use LITE version
sudo ./IranServerDockerMirror_LITE.sh
```

### Error: "Failed to restart Docker"

```bash
# Check logs
journalctl -u docker -n 50

# Full reset
sudo systemctl restart docker
```

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repo
2. Create a new branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -am 'Add feature'`)
4. Push (`git push origin feature/amazing`)
5. Create Pull Request

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file.

## 🙏 Acknowledgments

- All Docker mirror providers in Iran
- Open Source community
- All contributors to this project

---

<div dir="rtl">

## 📈 آمار پروژه

- ⭐ Stars: علاقه‌مندان
- 🍴 Forks: مشارکت‌کنندگان
- 🐛 Issues: گزارش‌های باگ
- ✅ Pull Requests: درخواست‌های Pull

## 🔄 تاریخچه نسخه‌ها

### نسخه 2.0 (2025-01-03)
- ✨ افزودن تست موازی
- 🎨 بهبود رابط کاربری
- 📝 سیستم logging کامل
- 🔄 Retry mechanism
- 🛡️ بهبود امنیت
- 🌐 میرورهای بیشتر

### نسخه 1.0 (قبلی)
- 🎯 عملکرد اصلی
- 🔍 تست سریالی
- 📊 خروجی ساده

---

**نگهدارنده:** DrConnect Infrastructure Team  
**آخرین به‌روزرسانی:** 2025-01-03  
**وضعیت:** فعال و در حال توسعه

</div>

---

<div align="center">

**Made with ❤️ for Iranian DevOps Community**

[⬆ بازگشت به بالا](#-iranserverdockermirror-v20)

</div>
