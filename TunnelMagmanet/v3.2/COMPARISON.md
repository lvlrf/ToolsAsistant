# 📊 مقایسه نسخه 3.0 و 3.5

## ۱. ساختار فولدرها

### قبل (v3.0):
```
output/
├── standard/
│   ├── iran-servers/
│   │   └── Doris-Respina/
│   └── kharej-servers/
│       └── Netherlands-NForce/
└── premium/
    ├── iran-servers/
    └── kharej-servers/
```

### بعد (v3.5):
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

## ۲. اسم سرویس‌ها

### قبل (v3.0):
```
backhaul-Doris-Respina-Netherlands-NForce-tcp
```

### بعد (v3.5):
```
@lvlRF-Tunnel-Standard-Doris-Respina-Netherlands-NForce-tcp
@lvlRF-Tunnel-Premium-Doris-Respina-Netherlands-NForce-tcp
```

**الگو:** `{binary_filename}-{Version}-{Server1}-{Server2}-{Transport}`

---

## ۳. Service File

### قبل (v3.0):
```ini
[Service]
Type=simple
ExecStart=/var/lib/@lvlRF-Tunnel/Standard/@lvlRF-Tunnel -c /root/config-Netherlands-NForce-tcp.toml
Restart=always
```

### بعد (v3.5):
```ini
[Service]
Type=simple
WorkingDirectory=/var/lib/@lvlRF-Tunnel/Standard
ExecStart=/var/lib/@lvlRF-Tunnel/Standard/./@lvlRF-Tunnel -c config-Netherlands-NForce-tcp.toml
Restart=always
```

**تغییرات:**
- ✅ اضافه شد: `WorkingDirectory`
- ✅ تغییر: `./` قبل از binary
- ✅ تغییر: config در همان مسیر binary

---

## ۴. Install Script

### قبل (v3.0):
```bash
#!/bin/bash
echo "Installing Backhaul services..."

# Ensure binary has execute permission
chmod +x /var/lib/@lvlRF-Tunnel/Standard/@lvlRF-Tunnel

# Create services...
```

### بعد (v3.5):
```bash
#!/bin/bash
echo "Installing @lvlRF-Tunnel STANDARD services..."

# Extract binary from compressed file
echo "Extracting binary: @lvlRF-Tunnel.tar.gz"
cd /var/lib/@lvlRF-Tunnel/Standard
tar -xzf @lvlRF-Tunnel.tar.gz
chmod +x @lvlRF-Tunnel

# Create services...
```

**تغییرات:**
- ✅ اضافه شد: خودکار extract فایل `.tar.gz`
- ✅ اضافه شد: `cd` به مسیر binary

---

## ۵. مسیر فایل‌ها

### قبل (v3.0):

```
Binary:  /var/lib/@lvlRF-Tunnel/Standard/@lvlRF-Tunnel
Config:  /root/config-Netherlands-NForce-tcp.toml
```

### بعد (v3.5):

```
Binary:  /var/lib/@lvlRF-Tunnel/Standard/@lvlRF-Tunnel
Config:  /var/lib/@lvlRF-Tunnel/Standard/config-Netherlands-NForce-tcp.toml
Archive: /var/lib/@lvlRF-Tunnel/Standard/@lvlRF-Tunnel.tar.gz
```

**همه فایل‌ها در یک مسیر!**

---

## ۶. نصب

### قبل (v3.0):

```bash
# 1. آپلود binary (قبلاً extract شده)
scp @lvlRF-Tunnel root@server:/var/lib/@lvlRF-Tunnel/Standard/

# 2. آپلود configs
scp *.toml root@server:/root/

# 3. آپلود install script
scp install-services.sh root@server:/tmp/

# 4. اجرا
ssh root@server "bash /tmp/install-services.sh"
```

### بعد (v3.5):

```bash
# 1. آپلود binary فشرده
scp @lvlRF-Tunnel.tar.gz root@server:/var/lib/@lvlRF-Tunnel/Standard/

# 2. آپلود همه چیز (config + script)
scp *.toml install-services.sh root@server:/var/lib/@lvlRF-Tunnel/Standard/

# 3. اجرا
ssh root@server "cd /var/lib/@lvlRF-Tunnel/Standard && bash install-services.sh"
```

**ساده‌تر و تمیزتر!**

---

## 📋 جدول مقایسه

| ویژگی | v3.0 | v3.5 |
|-------|------|------|
| ساختار فولدر | `standard/iran-servers` | `Iran/Standard` |
| اسم سرویس | `backhaul-...` | `@lvlRF-Tunnel-Standard-...` |
| مسیر config | `/root/` | همان مسیر binary |
| اجرای binary | `/path/file` | `/path/./file` |
| Extract | دستی | خودکار |
| WorkingDirectory | ❌ | ✅ |
| فایل فشرده | دستی extract | install script |

---

## ✅ مزایای v3.5

1. **ساختار واضح‌تر:** Iran/Kharej بجای iran-servers/kharej-servers
2. **اسم منحصر به فرد:** نام binary در اسم سرویس، تداخل نمی‌کنه
3. **همه فایل‌ها یکجا:** config و binary در یک مسیر
4. **نصب آسان‌تر:** فقط .tar.gz آپلود کن، بقیه خودکار
5. **سازگاری بهتر:** WorkingDirectory + `./` برای اجرای بهتر

---

**نتیجه:** نسخه 3.5 ساده‌تر، تمیزتر و کاربردی‌تر است! 🎉
