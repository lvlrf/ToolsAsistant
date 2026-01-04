# راهنمای تنظیم مسیر فایل‌های باینری

## 📍 تنظیمات پیش‌فرض

به صورت پیش‌فرض، مسیرهای زیر استفاده می‌شوند:

### نسخه Standard:
```
/root/backhaul
```

### نسخه Premium:
```
/root/backhaul-core/backhaul_premium
```

---

## ⚙️ تغییر مسیرها

در فایل `config.json`، بخش `binary_config` را ویرایش کنید:

```json
{
  "binary_config": {
    "standard": {
      "path": "/root",              ← مسیر فولدر
      "filename": "backhaul"        ← نام فایل
    },
    "premium": {
      "path": "/root/backhaul-core",
      "filename": "backhaul_premium"
    }
  }
}
```

---

## 📝 مثال‌های تغییر

### مثال ۱: تغییر مسیر Standard
اگر فایل backhaul رو در `/usr/local/bin` دارید:

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

مسیر کامل: `/usr/local/bin/backhaul`

---

### مثال ۲: تغییر نام فایل Premium
اگر فایل premium رو تغییر نام داده‌اید به `backhaul_pro`:

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

مسیر کامل: `/root/backhaul-core/backhaul_pro`

---

### مثال ۳: تغییر کامل هر دو
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

مسیرهای کامل:
- Standard: `/opt/backhaul/backhaul-std`
- Premium: `/opt/backhaul/backhaul-premium`

---

## 🎯 نکات مهم

### ✅ درست:
```json
"path": "/root"                    ← بدون / در آخر
"path": "/usr/local/bin"           ← بدون / در آخر
"filename": "backhaul"             ← بدون / در اول
"filename": "my-custom-backhaul"   ← بدون / در اول
```

### ❌ اشتباه:
```json
"path": "/root/"                   ← / اضافی در آخر
"path": "root"                     ← بدون / در اول
"filename": "/backhaul"            ← / اضافی در اول
```

---

## 🔄 استفاده

بعد از تغییر `config.json`:

```bash
# اجرای generator
python3 generator.py

# فایل‌های service با مسیر جدید ساخته می‌شوند
```

---

## 🧪 بررسی مسیرها

بعد از generate، مسیرها را چک کنید:

```bash
# چک کردن service files
grep "ExecStart" output/standard/iran-servers/*/install-services.sh
grep "ExecStart" output/premium/iran-servers/*/install-services.sh
```

باید مسیر دلخواه شما را نشان دهد.

---

## 📋 config.json کامل با توضیحات

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

  "settings": {
    "tunnel_port_start": 100,
    "web_port_start": 800,
    "iperf_iran_port_start": 5001,
    "iperf_kharej_port": 5201
  },

  "iran_servers": [
    {"name": "server1", "ip": "1.2.3.4"}
  ],

  "kharej_servers": [
    {"name": "server2", "ip": "5.6.7.8"}
  ],

  "connections": [
    {
      "iran": "server1",
      "kharej": "server2",
      "standard_transports": ["tcp"],
      "premium_transports": ["udp"]
    }
  ]
}
```

---

**نکته:** اگر فقط یکی از نسخه‌ها (Standard یا Premium) را استفاده می‌کنید، همان را تنظیم کنید و دیگری را پیش‌فرض بگذارید.
