# Backhaul Premium Generator v2.3 - نسخه نهایی

تولید خودکار config های تانل با Dashboard مدیریتی کامل

---

## 🚀 شروع سریع

### 1. تنظیم config.json
```bash
nano config.json
```

**ویرایش IP ها:**
```json
{
  "iran_servers": [
    {"name": "Tehran-Main", "ip": "YOUR_IRAN_IP_1"},
    {"name": "Tehran-Backup", "ip": "YOUR_IRAN_IP_2"},
    {"name": "Shiraz-Primary", "ip": "YOUR_IRAN_IP_3"}
  ],
  "kharej_servers": [
    {"name": "Germany-Hetzner", "ip": "YOUR_KHAREJ_IP_1"},
    {"name": "Netherlands-OVH", "ip": "YOUR_KHAREJ_IP_2"},
    {"name": "Finland-Contabo", "ip": "YOUR_KHAREJ_IP_3"}
  ],
  "connections": [
    {
      "iran": "Tehran-Main",
      "kharej": "Germany-Hetzner",
      "transports": ["tcp", "tcpmux", "ws", "wsmux"]
    }
  ]
}
```

### 2. تولید Config ها
```bash
python3 generator.py
# انتخاب [4] Everything
```

### 3. آپلود و نصب
```bash
# Iran
scp output/Iran/Tehran-Main/* root@IRAN_IP:/var/lib/@lvlRF-Tunnel/
ssh root@IRAN_IP "cd /var/lib/@lvlRF-Tunnel && tar -xzf @lvlRF-Tunnel.tar.gz && chmod +x @lvlRF-Tunnel && bash install-services.sh"

# Kharej
scp output/Kharej/Germany-Hetzner/* root@KHAREJ_IP:/var/lib/@lvlRF-Tunnel/
ssh root@KHAREJ_IP "cd /var/lib/@lvlRF-Tunnel && tar -xzf @lvlRF-Tunnel.tar.gz && chmod +x @lvlRF-Tunnel && bash install-services.sh"
```

### 4. نصب Dashboard (اختیاری)
```bash
scp dashboard.py install-dashboard.sh root@SERVER:/var/lib/@lvlRF-Tunnel/
ssh root@SERVER
cd /var/lib/@lvlRF-Tunnel
nano dashboard.py  # تغییر password در خط 12
bash install-dashboard.sh
ufw allow 8000/tcp
```

**دسترسی:** `http://YOUR_SERVER_IP:8000`

---

## 📋 نام‌گذاری

```
@lvlRF-Tunnel-{IranName}-{KharejName}-{Port}-{Transport}-{Profile}

مثال: @lvlRF-Tunnel-Tehran-Main-Germany-Hetzner-100-tcp-speed
```

---

## 🎯 Dashboard Features

- Live status monitoring
- Start/Stop/Restart با Modal
- مشاهده و Refresh لاگ‌ها
- ویرایش پورت‌ها
- تست سرعت (راهنمای گام‌به‌گام)
- حذف سرویس/فایل
- Dark mode
- فیلتر و جستجو

---

## 📚 Transports (13 نوع)

tcp, tcpmux, utcpmux, xtcpmux, ws, wsmux, uwsmux, xwsmux, udp, tcptun, faketcptun, wstun, udptun

**Profiles:** speed, stable, balanced

---

## 🔧 مدیریت

```bash
# وضعیت
systemctl status @lvlRF-Tunnel-Tehran-Main-Germany-Hetzner-100-tcp-speed

# Start/Stop/Restart
systemctl start|stop|restart SERVICE_NAME

# Logs
journalctl -u SERVICE_NAME.service -f
```

---

## 📁 ساختار خروجی

```
output/
├── Iran/Tehran-Main/*.toml
├── Kharej/Germany-Hetzner/*.toml
```

---

**نسخه:** 2.3 Final  
**تاریخ:** 2026-01-06
