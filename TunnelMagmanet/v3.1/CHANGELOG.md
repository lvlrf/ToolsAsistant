# 📋 تغییرات نسخه 2

## ✨ ویژگی‌های جدید

### 🎯 تنظیم مسیر فایل‌های باینری

حالا می‌توانید مسیر و نام فایل‌های باینری Standard و Premium را در `config.json` تعیین کنید!

#### قبل (نسخه 1):
```
❌ مسیرها hard-coded بودند:
- Standard: /root/backhaul
- Premium: /root/backhaul-core/backhaul_premium
```

#### حالا (نسخه 2):
```json
✅ در config.json تنظیم کنید:
{
  "binary_config": {
    "standard": {
      "path": "/your/custom/path",
      "filename": "your-backhaul-name"
    },
    "premium": {
      "path": "/another/path",
      "filename": "custom-premium-name"
    }
  }
}
```

---

## 📁 فایل‌های جدید

1. **BINARY-PATHS.md** - راهنمای کامل تنظیم مسیرها
2. **config.example.json** - نمونه config با مثال‌ها

---

## 🔧 تغییرات فنی

### در `config.json`:
```json
{
  "binary_config": {
    "standard": {
      "path": "/root",           ← جدید
      "filename": "backhaul"      ← جدید
    },
    "premium": {
      "path": "/root/backhaul-core",
      "filename": "backhaul_premium"
    }
  },
  "settings": { ... }
}
```

### در `generator.py`:
- خواندن مسیرها از config به جای hard-code
- پشتیبانی از مسیرهای سفارشی
- ساخت systemd service با مسیر دلخواه

---

## 📝 مثال استفاده

### مثال 1: مسیر پیش‌فرض (بدون تغییر)
```json
{
  "binary_config": {
    "standard": {
      "path": "/root",
      "filename": "backhaul"
    },
    "premium": {
      "path": "/root/backhaul-core",
      "filename": "backhaul_premium"
    }
  }
}
```
✅ همان رفتار قبلی

---

### مثال 2: تغییر مسیر Standard
```json
{
  "binary_config": {
    "standard": {
      "path": "/usr/local/bin",
      "filename": "backhaul"
    }
  }
}
```
✅ Service file: `/usr/local/bin/backhaul`

---

### مثال 3: تغییر نام فایل Premium
```json
{
  "binary_config": {
    "premium": {
      "path": "/root/backhaul-core",
      "filename": "backhaul_pro"
    }
  }
}
```
✅ Service file: `/root/backhaul-core/backhaul_pro`

---

## 🎯 سناریوهای کاربردی

### سناریو 1: باینری‌ها در یک فولدر
```json
{
  "binary_config": {
    "standard": {
      "path": "/opt/backhaul",
      "filename": "backhaul-std"
    },
    "premium": {
      "path": "/opt/backhaul",
      "filename": "backhaul-premium"
    }
  }
}
```

### سناریو 2: نام‌های سفارشی
```json
{
  "binary_config": {
    "standard": {
      "path": "/root",
      "filename": "my-backhaul"
    },
    "premium": {
      "path": "/root",
      "filename": "my-backhaul-pro"
    }
  }
}
```

---

## ⬆️ آپگرید از نسخه 1

اگر نسخه 1 را دارید:

1. فایل `config.json` قدیمی را نگه دارید
2. بخش `binary_config` را به ابتدای فایل اضافه کنید:

```json
{
  "binary_config": {
    "standard": {
      "path": "/root",
      "filename": "backhaul"
    },
    "premium": {
      "path": "/root/backhaul-core",
      "filename": "backhaul_premium"
    }
  },
  
  ... بقیه config شما ...
}
```

3. `generator.py` را اجرا کنید

---

## 🐛 رفع باگ‌ها

- هیچ باگی رفع نشده (نسخه اول باگ نداشت ✅)

---

## 📚 مستندات

- **README.md** - راهنمای کامل (بدون تغییر)
- **QUICKSTART.md** - شروع سریع (بدون تغییر)
- **BINARY-PATHS.md** - راهنمای جدید مسیرها ⭐
- **config.example.json** - نمونه‌های جدید ⭐

---

## ✅ سازگاری

نسخه 2 کاملاً سازگار با نسخه 1 است. اگر `binary_config` را در config.json نداشته باشید، از مقادیر پیش‌فرض استفاده می‌شود.

---

تاریخ انتشار: 2026-01-03
نسخه: 2.0.0
