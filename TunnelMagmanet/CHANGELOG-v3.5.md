# 📋 تغییرات نسخه 3.5

## 🎯 تغییرات عمده

### ۱. ساختار فولدرهای خروجی (قبل → بعد)

**قبل (نسخه 3.0):**
```
output/
├── standard/
│   ├── iran-servers/
│   └── kharej-servers/
└── premium/
    ├── iran-servers/
    └── kharej-servers/
```

**بعد (نسخه 3.5):**
```
output/
├── Iran/
│   ├── Standard/
│   │   └── Doris-Respina/
│   └── Premium/
│       └── Doris-Respina/
└── Kharej/
    ├── Standard/
    │   └── Netherlands-NForce/
    └── Premium/
        └── Netherlands-NForce/
```

---

### ۲. اسم سرویس‌ها (بر اساس نام باینری)

**قبل:**
```
backhaul-Doris-Respina-Netherlands-NForce-tcp
```

**بعد:**
```
@lvlRF-Tunnel-Standard-Doris-Respina-Netherlands-NForce-tcp
@lvlRF-Tunnel-Premium-Doris-Respina-Netherlands-NForce-tcp
```

الگو: `{binary_filename}-{Version}-{Iran/Kharej}-{Remote}-{Transport}`

---

### ۳. مسیر فایل‌های Config

**قبل:** Config ها در `/root/` بودند

**بعد:** Config ها در همان مسیر باینری هستند

```bash
# Standard
/var/lib/@lvlRF-Tunnel/Standard/@lvlRF-Tunnel
/var/lib/@lvlRF-Tunnel/Standard/config-Netherlands-NForce-tcp.toml

# Premium
/var/lib/@lvlRF-Tunnel/Premium/@lvlRF-Tunnel
/var/lib/@lvlRF-Tunnel/Premium/config-Netherlands-NForce-tcp.toml
```

---

### ۴. اجرای باینری با `./`

**Service File:**
```ini
[Service]
Type=simple
WorkingDirectory=/var/lib/@lvlRF-Tunnel/Standard
ExecStart=/var/lib/@lvlRF-Tunnel/Standard/./@lvlRF-Tunnel -c config-Netherlands-NForce-tcp.toml
```

---

### ۵. Extract خودکار فایل فشرده

**Install Script:**
```bash
#!/bin/bash
echo "Installing @lvlRF-Tunnel STANDARD services..."

# Extract binary
echo "Extracting binary: @lvlRF-Tunnel.tar.gz"
cd /var/lib/@lvlRF-Tunnel/Standard
tar -xzf @lvlRF-Tunnel.tar.gz
chmod +x @lvlRF-Tunnel

# ادامه نصب سرویس‌ها...
```

---

## 📋 مقایسه کامل

| ویژگی | نسخه 3.0 | نسخه 3.5 |
|-------|----------|----------|
| ساختار فولدر | `standard/iran-servers` | `Iran/Standard` |
| اسم سرویس | `backhaul-...` | `@lvlRF-Tunnel-Standard-...` |
| مسیر config | `/root/config.toml` | `/var/lib/.../config.toml` |
| اجرای binary | `/path/file` | `/path/./file` |
| Extract | دستی | خودکار در install script |

---

## 🚀 نحوه استفاده

### ۱. آماده‌سازی

```bash
# قرار دادن فایل فشرده در سرور
# Iran Standard:
scp @lvlRF-Tunnel.tar.gz root@iran:/var/lib/@lvlRF-Tunnel/Standard/

# Iran Premium:
scp @lvlRF-Tunnel.tar.gz root@iran:/var/lib/@lvlRF-Tunnel/Premium/

# Kharej Standard:
scp @lvlRF-Tunnel.tar.gz root@kharej:/var/lib/@lvlRF-Tunnel/Standard/

# Kharej Premium:
scp @lvlRF-Tunnel.tar.gz root@kharej:/var/lib/@lvlRF-Tunnel/Premium/
```

### ۲. نصب

```bash
# کپی config ها و install script
scp output/Iran/Standard/Doris-Respina/* root@iran:/var/lib/@lvlRF-Tunnel/Standard/

# اجرای install script
ssh root@iran "cd /var/lib/@lvlRF-Tunnel/Standard && bash install-services.sh"
```

### ۳. چک کردن

```bash
# لیست سرویس‌ها
systemctl list-units '@lvlRF-Tunnel-*' --all

# استاتوس یک سرویس
systemctl status @lvlRF-Tunnel-Standard-Doris-Respina-Netherlands-NForce-tcp
```

---

## 🎯 مزایا

✅ **ساختار واضح‌تر:** فولدرها به صورت `Iran/Kharej` و `Standard/Premium` مجزا شدند

✅ **اسم سرویس منحصر به فرد:** با نام باینری شروع می‌شود، تداخل نمی‌کند

✅ **همه فایل‌ها یکجا:** باینری و config ها در یک مسیر

✅ **نصب آسان‌تر:** فقط tar.gz رو آپلود کن، install script بقیه کارها رو انجام میده

✅ **سازگاری بهتر:** `./` قبل از باینری برای اجرای بهتر

---

## ⚠️ نکات مهم

### فایل فشرده باید در مسیر صحیح باشد:

```
/var/lib/@lvlRF-Tunnel/Standard/@lvlRF-Tunnel.tar.gz  ✅
/var/lib/@lvlRF-Tunnel/Premium/@lvlRF-Tunnel.tar.gz   ✅
/root/@lvlRF-Tunnel.tar.gz                            ❌
```

### اسم فایل فشرده:

الگو: `{binary_filename}.tar.gz`

مثال: اگه `filename: "@lvlRF-Tunnel"` → فایل فشرده: `@lvlRF-Tunnel.tar.gz`

---

## 📦 ساختار نهایی روی سرور

```
/var/lib/@lvlRF-Tunnel/
├── Standard/
│   ├── @lvlRF-Tunnel.tar.gz          (فایل فشرده اصلی)
│   ├── @lvlRF-Tunnel                  (بعد از extract)
│   ├── config-Netherlands-NForce-tcp.toml
│   ├── config-Netherlands-NForce-tcpmux.toml
│   └── install-services.sh
│
└── Premium/
    ├── @lvlRF-Tunnel.tar.gz
    ├── @lvlRF-Tunnel
    ├── config-Netherlands-NForce-tcp.toml
    └── install-services.sh
```

---

**نسخه:** 3.5.0  
**تاریخ:** 2026-01-03
