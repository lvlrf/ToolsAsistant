# راهنمای سریع - نسخه 3.5

## 🚀 ۳ مرحله ساده

### ۱. ویرایش config.json

```json
{
  "binary_config": {
    "standard": {
      "path": "/var/lib/@lvlRF-Tunnel/Standard",
      "filename": "@lvlRF-Tunnel"
    },
    "premium": {
      "path": "/var/lib/@lvlRF-Tunnel/Premium",
      "filename": "@lvlRF-Tunnel"
    }
  },

  "iran_servers": [
    {"name": "Tehran-Main", "ip": "1.2.3.4"}
  ],

  "kharej_servers": [
    {"name": "Germany-VPS", "ip": "5.6.7.8"}
  ],

  "connections": [
    {
      "iran": "Tehran-Main",
      "kharej": "Germany-VPS",
      "standard_transports": ["tcp", "ws"],
      "premium_transports": ["tcptun", "faketcptun"]
    }
  ]
}
```

### ۲. اجرای Generator

```bash
python generator.py
```

خروجی:
```
Backhaul Configuration Generator
==================================================
Token: abc123...
==================================================

[OK] Generated STANDARD: Tehran-Main -> Germany-VPS (tcp) Port 100
[OK] Generated STANDARD: Tehran-Main -> Germany-VPS (ws) Port 101
[OK] Generated PREMIUM: Tehran-Main -> Germany-VPS (tcptun) Port 102
[OK] Generated PREMIUM: Tehran-Main -> Germany-VPS (faketcptun) Port 103

[OK] All configurations generated successfully!
```

### ۳. نصب روی سرورها

#### الف) آپلود فایل فشرده

```bash
# Iran Standard
scp @lvlRF-Tunnel.tar.gz root@1.2.3.4:/var/lib/@lvlRF-Tunnel/Standard/

# Iran Premium
scp @lvlRF-Tunnel.tar.gz root@1.2.3.4:/var/lib/@lvlRF-Tunnel/Premium/

# Kharej Standard
scp @lvlRF-Tunnel.tar.gz root@5.6.7.8:/var/lib/@lvlRF-Tunnel/Standard/

# Kharej Premium
scp @lvlRF-Tunnel.tar.gz root@5.6.7.8:/var/lib/@lvlRF-Tunnel/Premium/
```

#### ب) آپلود فایل‌های Config

```bash
# Iran Standard
scp output/Iran/Standard/Tehran-Main/* root@1.2.3.4:/var/lib/@lvlRF-Tunnel/Standard/

# Iran Premium
scp output/Iran/Premium/Tehran-Main/* root@1.2.3.4:/var/lib/@lvlRF-Tunnel/Premium/

# Kharej Standard
scp output/Kharej/Standard/Germany-VPS/* root@5.6.7.8:/var/lib/@lvlRF-Tunnel/Standard/

# Kharej Premium
scp output/Kharej/Premium/Germany-VPS/* root@5.6.7.8:/var/lib/@lvlRF-Tunnel/Premium/
```

#### ج) اجرای Install Script

```bash
# Iran Standard
ssh root@1.2.3.4 "cd /var/lib/@lvlRF-Tunnel/Standard && bash install-services.sh"

# Iran Premium
ssh root@1.2.3.4 "cd /var/lib/@lvlRF-Tunnel/Premium && bash install-services.sh"

# Kharej Standard
ssh root@5.6.7.8 "cd /var/lib/@lvlRF-Tunnel/Standard && bash install-services.sh"

# Kharej Premium
ssh root@5.6.7.8 "cd /var/lib/@lvlRF-Tunnel/Premium && bash install-services.sh"
```

---

## ✅ چک کردن

```bash
# لیست سرویس‌ها
systemctl list-units '@lvlRF-Tunnel-*' --all

# استاتوس یک سرویس
systemctl status @lvlRF-Tunnel-Standard-Tehran-Main-Germany-VPS-tcp

# لاگ‌ها
journalctl -u @lvlRF-Tunnel-Standard-Tehran-Main-Germany-VPS-tcp -f
```

---

## 📁 ساختار خروجی

```
output/
├── Iran/
│   ├── Standard/
│   │   └── Tehran-Main/
│   │       ├── config-Germany-VPS-tcp.toml
│   │       ├── config-Germany-VPS-ws.toml
│   │       └── install-services.sh
│   └── Premium/
│       └── Tehran-Main/
│           ├── config-Germany-VPS-tcptun.toml
│           ├── config-Germany-VPS-faketcptun.toml
│           └── install-services.sh
│
└── Kharej/
    ├── Standard/
    │   └── Germany-VPS/
    │       ├── config-Tehran-Main-tcp.toml
    │       ├── config-Tehran-Main-ws.toml
    │       └── install-services.sh
    └── Premium/
        └── Germany-VPS/
            ├── config-Tehran-Main-tcptun.toml
            ├── config-Tehran-Main-faketcptun.toml
            └── install-services.sh
```

---

## 💡 نکته مهم

فایل `@lvlRF-Tunnel.tar.gz` باید **قبل از اجرای install script** در مسیر مناسب قرار بگیرد!

```bash
# مثال صحیح
/var/lib/@lvlRF-Tunnel/Standard/@lvlRF-Tunnel.tar.gz  ✅

# مثال اشتباه
/root/@lvlRF-Tunnel.tar.gz  ❌
```

---

**موفق باشید!** 🎉
