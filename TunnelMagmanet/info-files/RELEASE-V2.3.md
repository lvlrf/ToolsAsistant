# Release v2.3 - نسخه نهایی با Dashboard کامل! 🎉

**تاریخ:** 2026-01-06  
**تغییرات عمده:** نام‌گذاری یکسان + Dashboard کامل با Modal ها

---

## ✨ تغییرات کلیدی:

### 1. نام‌گذاری یکسان (همه‌جا)

```
فرمت: @lvlRF-Tunnel-{IranName}-{KharejName}-{Port}-{Transport}-{Profile}

مثال:
Service: @lvlRF-Tunnel-Tehran-Germany-100-tcp-speed.service
Config:  @lvlRF-Tunnel-Tehran-Germany-100-tcp-speed.toml
Log:     @lvlRF-Tunnel-Tehran-Germany-100-tcp-speed.json
```

**مزایا:**
- اسم service و file یکسان
- واضح معلومه بین کدوم سرورها
- آسان برای مدیریت

---

### 2. Dashboard کامل v2.3

#### 🎨 قابلیت‌های جدید:

**A) Modal برای همه Actions:**
```
Start/Stop/Restart/Status → Modal باز می‌شه
→ Command اجرا می‌شه
→ نتیجه نمایش داده می‌شه
→ Command خودکار کپی می‌شه
```

**B) Logs Modal:**
```
[📜 لاگ] → Modal باز
→ 100 خط آخر
→ Command کپی (auto)
→ دکمه Refresh + Copy Command
```

**C) Edit Port Modal:**
```
[✏️ ویرایش] → Modal باز
→ نمایش پورت‌های فعلی
→ فرم ویرایش:
  - Tunnel Port
  - Web Port
  - iperf Port
  - Forward Ports (نمایش)
→ Save → Update config + Restart service
```

**D) Test Speed Modal:**
```
[⚡ تست سرعت] → Modal باز
→ دستورات Iran و Kharej
→ مرحله به مرحله
→ هر دستور دکمه Copy داره
```

**E) Remove (2 دکمه):**
```
[🗑️ حذف سرویس] → stop + disable + rm service
[🗑️ حذف فایل] → rm config.toml
```

---

## 📊 ساختار خروجی:

```
output/
├── Iran/
│   └── Tehran/
│       ├── @lvlRF-Tunnel-Tehran-Germany-100-tcp-speed.toml
│       ├── @lvlRF-Tunnel-Tehran-Germany-101-tcp-stable.toml
│       ├── @lvlRF-Tunnel-Tehran-Germany-102-tcp-balanced.toml
│       ├── install-services.sh
│       └── ...
│
└── Kharej/
    └── Germany/
        ├── @lvlRF-Tunnel-Tehran-Germany-100-tcp-speed.toml
        ├── @lvlRF-Tunnel-Tehran-Germany-101-tcp-stable.toml
        └── ...
```

**نکته:** اسم فایل‌ها یکسان، محتوا متفاوت!

---

## 🚀 نحوه استفاده:

### مرحله 1: Generate Configs
```bash
python3 generator.py
# انتخاب [4] Everything
```

### مرحله 2: Upload به Iran
```bash
scp @lvlRF-Tunnel.tar.gz output/Iran/Tehran/* \\
    root@194.225.130.34:/var/lib/@lvlRF-Tunnel/
```

### مرحله 3: نصب در Iran
```bash
ssh root@194.225.130.34
cd /var/lib/@lvlRF-Tunnel
tar -xzf @lvlRF-Tunnel.tar.gz
chmod +x @lvlRF-Tunnel
bash install-services.sh
```

### مرحله 4: Upload به Kharej
```bash
scp @lvlRF-Tunnel.tar.gz output/Kharej/Germany/* \\
    root@91.107.190.78:/var/lib/@lvlRF-Tunnel/
```

### مرحله 5: نصب در Kharej
```bash
ssh root@91.107.190.78
cd /var/lib/@lvlRF-Tunnel
tar -xzf @lvlRF-Tunnel.tar.gz
chmod +x @lvlRF-Tunnel
bash install-services.sh
```

### مرحله 6: نصب Dashboard (اختیاری)
```bash
# آپلود
scp dashboard-v2.3.py install-dashboard.sh root@SERVER:/var/lib/@lvlRF-Tunnel/

# نصب
ssh root@SERVER
cd /var/lib/@lvlRF-Tunnel
cp dashboard-v2.3.py dashboard.py
nano dashboard.py  # تغییر password
bash install-dashboard.sh

# دسترسی
http://YOUR_SERVER_IP:8000
```

---

## 🎯 Dashboard Features:

### Live Status:
- Auto-refresh هر 3 ثانیه
- Status badge: ● Active / ○ Inactive / ⚠ Unknown
- فیلتر بر اساس Active/Inactive

### Web Panel:
```
[🌐 Tehran] [🌐 Germany]
```
باز کردن در tab جدید

### Service Management (با Modal):
```
[▶️ استارت] → Modal + نتیجه + Auto copy
[⏸️ استاپ] → Modal + نتیجه + Auto copy
[🔄 ری‌استارت] → Modal + نتیجه + Auto copy
[📊 وضعیت] → Modal + نتیجه + Auto copy
```

### Logs:
```
[📜 لاگ] → Modal + 100 خط آخر
→ Command: journalctl -u SERVICE.service -f
→ Auto copy command
→ [Refresh] [Copy Command]
```

### Edit Port:
```
[✏️ ویرایش] → Modal با فرم
→ نمایش پورت‌های فعلی
→ ویرایش Tunnel/Web/iperf
→ نمایش Forward Ports
→ [Save & Restart]
```

### Test Speed:
```
[⚡ تست سرعت] → Modal
→ دستورات Iran (3 مرحله)
→ دستورات Kharej (1 مرحله)
→ هر دستور دکمه Copy
```

### Remove:
```
[🗑️ حذف سرویس] → Confirm → حذف کامل
[🗑️ حذف فایل] → Confirm → حذف config.toml
```

### Bulk Actions:
```
[▶️ استارت همه]
[⏸️ استاپ همه]
[🔄 ری‌استارت همه]
```

### Filters:
```
[جستجو]
[سرور ▼]
[Transport ▼]
[وضعیت ▼] All/Active/Inactive
```

### Dark Mode:
```
[🌙] → تغییر تم
→ ذخیره در localStorage
```

---

## 📱 UI Examples:

### Config Card:
```
┌────────────────────────────────────────┐
│  @lvlRF-Tunnel-Tehran-Germany-100-tcp  │
│  ● فعال                                │
│  Tehran (194.x.x.x) ↔ Germany (91.x.x) │
│  TCP | SPEED | Port: 100 | Web: 800   │
├────────────────────────────────────────┤
│  وب پنل:                               │
│  [🌐 Tehran] [🌐 Germany]             │
├────────────────────────────────────────┤
│  مدیریت سرویس:                        │
│  [▶️ استارت] [⏸️ استاپ]              │
│  [🔄 ری‌استارت] [📊 وضعیت]           │
├────────────────────────────────────────┤
│  عملیات:                              │
│  [📜 لاگ] [✏️ ویرایش]                │
│  [⚡ تست سرعت]                        │
│  [🗑️ حذف سرویس] [🗑️ حذف فایل]      │
└────────────────────────────────────────┘
```

### Modal Example (Action Result):
```
┌─────────────────────────────────────┐
│  نتیجه start                   [✕] │
├─────────────────────────────────────┤
│  $ systemctl start SERVICE.service  │
│  Started SERVICE.service            │
│                                     │
│  [کپی دستور]                       │
└─────────────────────────────────────┘
```

### Modal Example (Logs):
```
┌─────────────────────────────────────┐
│  لاگ‌ها                        [✕] │
├─────────────────────────────────────┤
│  [کپی دستور] [Refresh]             │
├─────────────────────────────────────┤
│  Jan 06 12:00 [INFO] Starting...    │
│  Jan 06 12:01 [INFO] Connected...   │
│  ...                                │
│  (100 خط آخر)                      │
└─────────────────────────────────────┘
```

### Modal Example (Edit Port):
```
┌─────────────────────────────────────┐
│  ویرایش پورت‌ها               [✕] │
├─────────────────────────────────────┤
│  پورت فعلی Tunnel: [100     ]      │
│  پورت جدید Tunnel: [____]          │
│                                     │
│  پورت فعلی Web: [800     ]         │
│  پورت جدید Web: [____]             │
│                                     │
│  پورت فعلی iperf: [5001   ]        │
│  پورت جدید iperf: [____]           │
│                                     │
│  Forward Ports:                     │
│  5023 → 127.0.0.1:5201             │
│                                     │
│  [ذخیره و ری‌استارت]               │
└─────────────────────────────────────┘
```

### Modal Example (Test Speed):
```
┌─────────────────────────────────────┐
│  تست سرعت                      [✕] │
├─────────────────────────────────────┤
│  🔴 سرور Tehran:                    │
│                                     │
│  مرحله 1: راه‌اندازی سرور          │
│  iperf3 -s -B 127.0.0.1 -p 5001    │
│  [کپی]                             │
│                                     │
│  مرحله 2: تست دانلود               │
│  iperf3 -c 127.0.0.1 -p 5001 -t 30 │
│  [کپی]                             │
│                                     │
│  مرحله 3: تست آپلود                │
│  iperf3 -c ... -R                   │
│  [کپی]                             │
├─────────────────────────────────────┤
│  🟢 سرور Germany:                   │
│  iperf3 -s -B 127.0.0.1 -p 5201    │
│  [کپی]                             │
└─────────────────────────────────────┘
```

---

## ⚙️ تنظیمات Dashboard:

### در dashboard-v2.3.py:

```python
# خط 11-13:
DASHBOARD_PORT = 8000
DASHBOARD_PASSWORD = "your-secure-password-here"  # ⚠️ تغییر بده!
AUTO_REFRESH_SECONDS = 3
```

### Firewall:
```bash
ufw allow 8000/tcp
```

### مدیریت:
```bash
systemctl status lvlrf-dashboard
systemctl stop lvlrf-dashboard
systemctl start lvlrf-dashboard
systemctl restart lvlrf-dashboard

journalctl -u lvlrf-dashboard -f
```

---

## 🔒 امنیت:

### 1. تغییر Password:
```python
DASHBOARD_PASSWORD = "Super-Strong-Password-123!"
```

### 2. غیرفعال کردن:
```bash
systemctl stop lvlrf-dashboard
systemctl disable lvlrf-dashboard
```

### 3. محدود کردن IP:
```bash
ufw allow from YOUR_IP to any port 8000
```

---

## 💡 نکات مهم:

### 1. اسم سرویس یکسان
```
Iran:   @lvlRF-Tunnel-Tehran-Germany-100-tcp-speed
Kharej: @lvlRF-Tunnel-Tehran-Germany-100-tcp-speed

یکسان هستن! ولی config متفاوت!
```

### 2. Log File
```
هر دو سرور به همین log می‌نویسن:
/var/lib/@lvlRF-Tunnel/@lvlRF-Tunnel-Tehran-Germany-100-tcp-speed.json

اگه روی یک سرور باشن → overwrite
اگه روی سرورهای جدا باشن → مشکلی نیست
```

### 3. Config File
```
Iran:   /var/lib/@lvlRF-Tunnel/@lvlRF-Tunnel-Tehran-Germany-100-tcp-speed.toml
Kharej: /var/lib/@lvlRF-Tunnel/@lvlRF-Tunnel-Tehran-Germany-100-tcp-speed.toml

اسم یکسان، محتوا متفاوت!
```

### 4. Service Description
```bash
systemctl status @lvlRF-Tunnel-Tehran-Germany-100-tcp-speed

# Description نشون میده بین کدوم سرورهاست
```

---

## 🆚 مقایسه با v2.2:

| Feature | v2.2 | v2.3 |
|---------|------|------|
| **نام سرویس** | @lvlRF-Tunnel-100-tcp | @lvlRF-Tunnel-Tehran-Germany-100-tcp |
| **نام Config** | 100-tcp-speed.toml | @lvlRF-Tunnel-Tehran-Germany-100-tcp-speed.toml |
| **Log File** | 100-tcp-speed.json | @lvlRF-Tunnel-Tehran-Germany-100-tcp-speed.json |
| **Dashboard UI** | ساده | کامل با Modal ها |
| **Action Result** | فقط notification | Modal + Output + Auto Copy |
| **Logs** | Copy command فقط | Modal + Logs + Refresh |
| **Edit Port** | ❌ | ✅ با Modal |
| **Test Speed** | ❌ | ✅ با Modal مرحله‌به‌مرحله |
| **Remove** | ❌ | ✅ دو دکمه جدا |

---

## 🎉 نتیجه:

**v2.3 = نسخه نهایی و کامل!**

- ✅ نام‌گذاری واضح و یکسان
- ✅ Dashboard کامل با همه قابلیت‌ها
- ✅ Modal ها برای همه actions
- ✅ Auto copy commands
- ✅ Live status
- ✅ Dark mode
- ✅ Filters
- ✅ Bulk operations
- ✅ Edit ports
- ✅ Test speed guide
- ✅ Remove service/file
- ✅ Remote access

**آماده برای Production!** 🚀

---

**نسخه:** 2.3  
**تاریخ:** 2026-01-06  
**وضعیت:** Final Release ✅
