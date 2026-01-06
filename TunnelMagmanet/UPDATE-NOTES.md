# آپدیت نهایی v2.0 - تغییرات اعمال شده

## ✅ تغییرات اعمال شده:

### 1. فیکس config.json
```python
# قبل:
config_path: str = "config-test.json"  ❌

# بعد:
config_path: str = "config.json"  ✅
```

### 2. دکمه Install Service اضافه شد
هر کانفیگ حالا دکمه Install داره:

```
📥 Install Tehran-Main
📥 Install Germany-Hetzner
```

**دستور تولید شده:**
```bash
cat > /etc/systemd/system/backhaul-iran100-tcp-speed.service << 'EOF'
[Unit]
Description=backhaul-iran100-tcp-speed
After=network.target

[Service]
Type=simple
WorkingDirectory=/root/backhaul-core
ExecStart=/root/backhaul-core/./backhaul_premium -c /root/backhaul-core/iran100-tcp-speed.toml
Restart=always
RestartSec=3
LimitNOFILE=1048576

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable backhaul-iran100-tcp-speed.service
systemctl start backhaul-iran100-tcp-speed.service
```

این دستور:
- Service file رو می‌سازه
- systemd رو reload می‌کنه
- سرویس رو enable می‌کنه
- سرویس رو start می‌کنه

### 3. Footer حذف شد
```html
<!-- قبل: -->
<div class="footer">
    <a href="#">Transport Guide</a>
    <a href="https://github.com/Musixal/Backhaul">Backhaul GitHub</a>
    <a href="README.md">Documentation</a>
</div>

<!-- بعد: حذف شد ✅ -->
```

### 4. راهنمای Transport به فارسی
**محتوای کامل با:**
- ✅ توضیحات فارسی
- ✅ دستورات عملی
- ✅ مثال‌های کاربردی
- ✅ تنظیمات پیشنهادی
- ✅ جدول انتخاب سریع
- ✅ دستورات systemctl
- ✅ دستورات iperf3
- ✅ تنظیمات BBR
- ✅ استفاده Edge IP
- ✅ نکات مهم

**مثال محتوا:**

```
🟢 TCP Transport
بهترین برای: سرعت بالا، دانلود، استریم

دستور نصب:
systemctl enable backhaul-iran100-tcp-speed.service
systemctl start backhaul-iran100-tcp-speed.service

---

🌐 WS Transport
استفاده با Cloudflare:
transport = "ws"
edge_ip = "188.114.96.0"
# پورت: 443, 8443, 2053, 2083, 2087, 2096

---

🔧 دستورات مفید:
نصب: systemctl enable ...
استارت: systemctl start ...
وضعیت: systemctl status ...
لاگ: journalctl -u ... -f

---

تست سرعت:
# Kharej:
iperf3 -s -B 127.0.0.1 -p 5201

# Iran:
iperf3 -c 127.0.0.1 -p 5001 -t 30
```

---

## 📊 ترتیب دکمه‌ها در هر Config Card:

```
🌐 Web {Server1}          🌐 Web {Server2}
📥 Install {Server1}      📥 Install {Server2}
📊 Status {Server1}       📊 Status {Server2}
▶️ Start {Server1}        ▶️ Start {Server2}
⏸️ Stop {Server1}         ⏸️ Stop {Server2}
🔄 Restart {Server1}      🔄 Restart {Server2}
📜 Logs {Server1}         📜 Logs {Server2}
```

**جمعاً:** 14 دکمه برای هر config (7 برای Iran + 7 برای Kharej)

---

## 🎯 نحوه استفاده Install:

### روش 1: نصب تکی
1. کلیک روی **📥 Install Tehran-Main**
2. دستور کپی می‌شه
3. SSH به سرور Tehran-Main
4. Paste و Enter
5. سرویس نصب و اجرا می‌شه

### روش 2: نصب دسته‌ای (همه سرویس‌ها)
1. کلیک روی **📦 Extract & Chmod Binary** در بالا
2. SSH به سرور
3. Paste و Enter (باینری آماده می‌شه)
4. از پوشه output فایل `install-services.sh` رو آپلود کن
5. اجرا کن: `bash install-services.sh`

---

## 🆚 مقایسه روش‌ها:

| روش | مزایا | معایب |
|-----|-------|-------|
| **Install تکی** (دکمه) | انتخاب دقیق، تست تکی | باید برای هر config تکرار شه |
| **Install دسته‌ای** (اسکریپت) | همه با یک دستور | نمی‌تونی تکی انتخاب کنی |

**توصیه:**
- برای **تست:** Install تکی
- برای **production:** Install دسته‌ای

---

## 📋 Checklist استفاده:

### اولین بار (Setup):
- [ ] آپلود `backhaul_premium.tar.gz`
- [ ] کلیک **📦 Extract & Chmod Binary**
- [ ] Paste در سرور Iran
- [ ] Paste در سرور Kharej
- [ ] آپلود config files (از پوشه output)

### نصب سرویس‌ها:
**روش A - تکی:**
- [ ] کلیک **📥 Install** برای هر config
- [ ] Paste در سرور مربوطه

**روش B - دسته‌ای:**
- [ ] آپلود `install-services.sh`
- [ ] اجرا: `bash install-services.sh`

### چک کردن:
- [ ] کلیک **📊 Status** برای هر config
- [ ] کلیک **🌐 Web Panel** برای monitoring
- [ ] تست سرعت با iperf3

---

## 🎨 ظاهر Dashboard:

```
┌─────────────────────────────────────────┐
│  🚀 Tunnel Management  [📚 Guide]       │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  Quick Actions                          │
│  [📦 Extract]  [🔄 Restart]  [⏸️ Stop] │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  Filters...                             │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  backhaul-iran100-tcp-speed             │
│  Tehran (Iran) → Germany (Kharej)       │
│  TCP  SPEED                             │
│  Port: 100  Web: 800                    │
│                                         │
│  [🌐 Web Tehran]  [🌐 Web Germany]     │
│  [📥 Install Tehran]  [📥 Install Ger] │
│  [📊 Status Tehran]  [📊 Status Ger]   │
│  [▶️ Start Tehran]  [▶️ Start Germany] │
│  [⏸️ Stop Tehran]  [⏸️ Stop Germany]   │
│  [🔄 Restart...]  [📜 Logs...]         │
└─────────────────────────────────────────┘

(Footer حذف شد - لینک‌ها نیست)
```

---

**تمام تغییرات اعمال شد!** ✅
