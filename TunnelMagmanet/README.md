# Backhaul Configuration Generator

یک ابزار خودکار برای تولید کانفیگ‌ها و سرویس‌های Backhaul - هم نسخه Standard و هم نسخه Premium

## ویژگی‌ها

✅ پشتیبانی همزمان از نسخه Standard و Premium  
✅ مدیریت خودکار پورت‌ها (بدون تداخل)  
✅ تولید فایل‌های سرویس systemd  
✅ اسکریپت‌های نصب آماده (کپی-پیست)  
✅ پیکربندی iperf3 برای تست سرعت  
✅ State Management (برای اضافه کردن سرور جدید)  
✅ یک Token مشترک برای همه تانل‌ها  
✅ پشتیبانی از نام‌های فارسی/انگلیسی سرورها  

## Transport های پشتیبانی شده

### نسخه Standard:
- `tcp` - TCP ساده
- `tcpmux` - TCP با Multiplexing
- `udp` - UDP ساده
- `ws` - WebSocket
- `wsmux` - WebSocket با Multiplexing

### نسخه Premium (علاوه بر Standard):
- `utcpmux` - UDP over TCP Multiplexing
- `uwsmux` - UDP over WebSocket Multiplexing
- `tcptun` - TCP Tunnel با TUN interface
- `faketcptun` - Fake TCP Tunnel

## نصب و راه‌اندازی

### ۱. نیازمندی‌ها
```bash
python3
```

### ۲. ساختار پروژه
```
backhaul-manager/
├── generator.py          # اسکریپت اصلی
├── config.json          # تنظیمات شما
├── state.json           # وضعیت (auto-generated)
└── output/              # خروجی‌ها
    ├── standard/
    │   ├── iran-servers/
    │   └── kharej-servers/
    ├── premium/
    │   ├── iran-servers/
    │   └── kharej-servers/
    └── port-mapping.md
```

### ۳. تنظیم config.json

نمونه:
```json
{
  "settings": {
    "tunnel_port_start": 100,
    "web_port_start": 800,
    "iperf_iran_port_start": 5001,
    "iperf_kharej_port": 5201
  },

  "iran_servers": [
    {"name": "tehran-main", "ip": "1.2.3.4"},
    {"name": "shiraz-backup", "ip": "5.6.7.8"}
  ],

  "kharej_servers": [
    {"name": "germany-hetzner", "ip": "20.30.40.50"},
    {"name": "france-ovh", "ip": "21.31.41.51"}
  ],

  "connections": [
    {
      "iran": "tehran-main",
      "kharej": "germany-hetzner",
      "standard_transports": ["tcp", "tcpmux"],
      "premium_transports": ["udp", "wsmux"]
    }
  ]
}
```

### ۴. اجرا
```bash
cd backhaul-manager
python3 generator.py
```

## استفاده

### روی سرور ایران:
۱. فایل‌های `.toml` را به `/root/` کپی کنید
۲. اسکریپت `install-services.sh` را اجرا کنید:
```bash
cd output/standard/iran-servers/tehran-main/  # یا premium
bash install-services.sh
```

### روی سرور خارج:
۱. iperf3 server را روی localhost راه‌اندازی کنید:
```bash
iperf3 -s -B 127.0.0.1 -p 5201
```
۲. فایل‌های `.toml` را به `/root/` کپی کنید
۳. اسکریپت `install-services.sh` را اجرا کنید

### تست با iperf3:
روی سرور ایران:
```bash
# تست تانل اول
iperf3 -c 127.0.0.1 -p 5001 -t 10

# تانل دوم
iperf3 -c 127.0.0.1 -p 5002 -t 10
```

## مدیریت سرویس‌ها

### چک کردن وضعیت:
```bash
systemctl status backhaul-*
```

### ری‌استارت:
```bash
systemctl restart backhaul-tehran-main-germany-tcp
```

### مشاهده لاگ‌ها:
```bash
journalctl -u backhaul-tehran-main-germany-tcp -f
```

## Web Interface

هر تانل یک Web Interface دارد:
```
http://SERVER_IP:WEB_PORT
```

مثال:
- `http://1.2.3.4:800` - تانل اول
- `http://1.2.3.4:801` - تانل دوم

## اضافه کردن سرور جدید

۱. فایل `config.json` را ویرایش کنید
۲. سرور جدید یا connection جدید اضافه کنید
۳. دوباره اسکریپت را اجرا کنید:
```bash
python3 generator.py
```

**نکته:** پورت‌ها به صورت خودکار از جایی که قطع شده‌اند ادامه پیدا می‌کنند (بدون تداخل).

## فایل‌های تولید شده

### برای هر سرور:
- `config-*.toml` - فایل‌های کانفیگ → کپی به `/root/`
- `install-services.sh` - اسکریپت نصب سرویس‌ها
- `port-mapping.md` - مستندات پورت‌ها و دستورات

### State File:
`state.json` - حاوی:
- آخرین پورت استفاده شده
- Token مشترک
- تاریخچه تولید

**هرگز این فایل را پاک نکنید** مگر اینکه بخواهید از اول شروع کنید.

## نکات مهم

⚠️ **Token:** یک token برای همه تانل‌ها استفاده می‌شود. در `state.json` ذخیره شده.

⚠️ **Binary Paths:**
- Standard: `/root/backhaul`
- Premium: `/root/backhaul-core/backhaul_premium`

⚠️ **TUN Transports:** `tcptun` و `faketcptun` نیاز به subnet جداگانه دارند که خودکار تخصیص داده می‌شود.

## مثال کامل

```bash
# ۱. ایجاد config
nano config.json

# ۲. تولید کانفیگ‌ها
python3 generator.py

# ۳. روی سرور ایران
scp output/premium/iran-servers/tehran-main/*.toml root@iran-ip:/root/
scp output/premium/iran-servers/tehran-main/install-services.sh root@iran-ip:/root/
ssh root@iran-ip "bash /root/install-services.sh"

# ۴. روی سرور خارج
ssh root@kharej-ip "iperf3 -s -B 127.0.0.1 -p 5201 &"
scp output/premium/kharej-servers/germany-hetzner/*.toml root@kharej-ip:/root/
scp output/premium/kharej-servers/germany-hetzner/install-services.sh root@kharej-ip:/root/
ssh root@kharej-ip "bash /root/install-services.sh"

# ۵. تست
ssh root@iran-ip "iperf3 -c 127.0.0.1 -p 5001 -t 10"
```

## پشتیبانی

- Telegram: گروه Backhaul
- GitHub Issues: [مخزن Backhaul](https://github.com/Musixal/Backhaul)

---

**ساخته شده با ❤️ برای مدیریت راحت‌تر تانل‌های Backhaul**
