# راهنمای Dashboard تحت وب

Dashboard مدیریت تانل‌ها با قابلیت کنترل real-time

---

## 🚀 نصب سریع

### مرحله 1: آپلود فایل‌ها
```bash
# آپلود به سرور
scp dashboard.py root@YOUR_SERVER:/root/backhaul-core/
scp install-dashboard.sh root@YOUR_SERVER:/root/backhaul-core/
```

### مرحله 2: تغییر پسورد
```bash
ssh root@YOUR_SERVER
cd /root/backhaul-core
nano dashboard.py
```

**خط 12 را تغییر دهید:**
```python
DASHBOARD_PASSWORD = "your-secure-password-here"  # ⚠️ حتماً تغییر بده!
```

**تغییر پورت (اختیاری):**
```python
DASHBOARD_PORT = 8000  # اگر می‌خواهی پورت دیگری باشد
```

### مرحله 3: نصب
```bash
chmod +x install-dashboard.sh
bash install-dashboard.sh
```

### مرحله 4: باز کردن Firewall
```bash
# UFW
ufw allow 8000/tcp

# یا iptables
iptables -A INPUT -p tcp --dport 8000 -j ACCEPT
```

### مرحله 5: دسترسی
```
http://YOUR_SERVER_IP:8000
```

---

## ⚙️ تنظیمات

### تغییر Port
```python
DASHBOARD_PORT = 9000  # هر پورتی که بخواهی
```

### تغییر Auto-Refresh
```python
AUTO_REFRESH_SECONDS = 5  # بازه refresh به ثانیه
```

### تغییر مسیرها
```python
BINARY_PATH = "/root/backhaul-core"
STATE_FILE = f"{BINARY_PATH}/state.json"
CONFIG_FILE = f"{BINARY_PATH}/config.json"
```

---

## 🎯 قابلیت‌ها

### ✅ Live Status
- نمایش وضعیت real-time تمام سرویس‌ها
- Auto-refresh هر 3 ثانیه
- فیلتر بر اساس Active/Inactive

### ✅ کنترل مستقیم
- Start/Stop/Restart سرویس‌ها
- بدون نیاز به کپی دستور
- اعمال فوری تغییرات

### ✅ مشاهده Logs
- لاگ‌های real-time
- 100 خط آخر
- کلیک روی دکمه → باز می‌شه

### ✅ ویرایش Port
- تغییر Port Tunnel
- تغییر Port Web
- تغییر Port iperf
- Auto-restart بعد از تغییر

### ✅ تست سرعت
- راهنمای گام‌به‌گام
- دستورات Iran و Kharej
- کپی با یک کلیک

### ✅ مدیریت Dashboard
- فعال/غیرفعال کردن Dashboard Service
- از داخل خود Dashboard
- برای امنیت بیشتر

### ✅ فیلترهای قدرتمند
- جستجو در همه فیلدها
- فیلتر بر اساس Server
- فیلتر بر اساس Transport
- فیلتر بر اساس Status

### ✅ Dark Mode
- تم تاریک/روشن
- ذخیره در localStorage
- تغییر با یک کلیک

---

## 📊 رابط کاربری

### صفحه ورود
```
┌──────────────────────────┐
│  🚀 داشبورد تانل        │
│                          │
│  [رمز عبور]             │
│  [ورود]                 │
└──────────────────────────┘
```

### داشبورد اصلی
```
┌─────────────────────────────────────────┐
│  🚀 @lvlRF Tunnel Dashboard  [🌙] [⚙️] │
├─────────────────────────────────────────┤
│  عملیات سریع:                          │
│  [▶️ استارت همه] [⏸️ استاپ همه]       │
├─────────────────────────────────────────┤
│  فیلتر:                                 │
│  [جستجو] [سرور] [Transport] [وضعیت]   │
├─────────────────────────────────────────┤
│  ┌───────────────────────────────────┐  │
│  │ ● @lvlRF-Tunnel-100-tcp-speed    │  │
│  │   Tehran ↔ Germany | TCP | SPEED  │  │
│  │   Port: 100  Web: 800            │  │
│  │                                   │  │
│  │   [🌐 Tehran] [🌐 Germany]       │  │
│  │   [▶️ Start] [⏸️ Stop] [🔄]      │  │
│  │   [📜 Log] [✏️ Edit] [⚡ Test]   │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

---

## 🔐 امنیت

### 1. تغییر Password
**حتماً** password را در `dashboard.py` تغییر دهید:
```python
DASHBOARD_PASSWORD = "your-SUPER-secure-PASSWORD-123!"
```

### 2. فعال/غیرفعال کردن Dashboard
وقتی نیاز ندارید، Dashboard را خاموش کنید:

```bash
# از خط فرمان:
systemctl stop lvlrf-dashboard
systemctl disable lvlrf-dashboard

# یا از داخل Dashboard:
[⚙️ Dashboard] → [غیرفعال‌سازی]
```

### 3. محدود کردن IP
فقط از IP خاص دسترسی:
```bash
# Firewall
ufw allow from YOUR_IP to any port 8000

# یا در کد Python (dashboard.py):
# خط 14:
ALLOWED_IPS = ['1.2.3.4', '5.6.7.8']
```

### 4. استفاده از HTTPS
برای production، از reverse proxy استفاده کنید:
```nginx
# Nginx config
server {
    listen 443 ssl;
    server_name dashboard.yourdomain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 🛠️ مدیریت Service

### دستورات اصلی
```bash
# وضعیت
systemctl status lvlrf-dashboard

# استارت
systemctl start lvlrf-dashboard

# استاپ
systemctl stop lvlrf-dashboard

# ری‌استارت
systemctl restart lvlrf-dashboard

# فعال‌سازی (auto-start)
systemctl enable lvlrf-dashboard

# غیرفعال‌سازی
systemctl disable lvlrf-dashboard
```

### مشاهده Logs
```bash
# لاگ‌های real-time
journalctl -u lvlrf-dashboard -f

# 100 خط آخر
journalctl -u lvlrf-dashboard -n 100

# لاگ‌های امروز
journalctl -u lvlrf-dashboard --since today
```

### حذف کامل
```bash
systemctl stop lvlrf-dashboard
systemctl disable lvlrf-dashboard
rm /etc/systemd/system/lvlrf-dashboard.service
systemctl daemon-reload
```

---

## 🔧 عیب‌یابی

### Dashboard باز نمی‌شه

**1. چک کردن Service:**
```bash
systemctl status lvlrf-dashboard
```

**2. چک کردن Port:**
```bash
ss -tlnp | grep 8000
```

**3. چک کردن Firewall:**
```bash
ufw status
```

**4. چک کردن Logs:**
```bash
journalctl -u lvlrf-dashboard -n 50
```

### خطای "Password اشتباه"
- Password را در `dashboard.py` چک کنید
- Service را restart کنید:
  ```bash
  systemctl restart lvlrf-dashboard
  ```

### سرویس‌ها غیرفعال نمیشن
- بررسی کنید که از root اجرا می‌شود
- سرویس‌ها باید با نام `@lvlRF-Tunnel-*` باشند
- `state.json` و `config.json` باید موجود باشند

### Port قابل ویرایش نیست
- Config file باید در `/root/backhaul-core` باشد
- Permission فایل‌ها را چک کنید
- پس از ویرایش manual، service را restart کنید

---

## 📱 دسترسی Remote

### از طریق IP عمومی
```
http://YOUR_PUBLIC_IP:8000
```

### از طریق Domain
1. Domain را به IP سرور Point کنید
2. دسترسی:
   ```
   http://yourdomain.com:8000
   ```

### با Cloudflare Tunnel (امن‌تر)
```bash
# نصب cloudflared
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
dpkg -i cloudflared-linux-amd64.deb

# ایجاد tunnel
cloudflared tunnel create dashboard
cloudflared tunnel route dns dashboard dashboard.yourdomain.com

# اجرا
cloudflared tunnel run --url http://localhost:8000 dashboard
```

---

## 💡 نکات مهم

### 1. Session timeout
Session به مدت 24 ساعت معتبر است. بعد از آن باید دوباره login کنید.

### 2. Auto-refresh
Auto-refresh به صورت خودکار فعال است. برای غیرفعال کردن، تغییر دهید:
```python
AUTO_REFRESH_SECONDS = 0  # غیرفعال
```

### 3. همزمانی
Dashboard با چند کاربر همزمان کار می‌کند اما تغییرات فوری sync نمی‌شوند. 

### 4. Performance
برای تعداد زیاد سرویس (100+):
- Auto-refresh را به 5 یا 10 ثانیه تغییر دهید
- از فیلترها استفاده کنید

---

## 🎨 سفارشی‌سازی

### تغییر Theme
در `dashboard.py`، CSS variables را تغییر دهید:
```css
:root {
    --accent: #your-color;
    --bg-primary: #your-bg;
}
```

### اضافه کردن Feature
1. API endpoint جدید در Python
2. Function جدید در JavaScript
3. دکمه جدید در HTML

---

## 📞 پشتیبانی

**مشکل دارید؟**
1. Logs را چک کنید
2. این راهنما را مطالعه کنید
3. Github Issue باز کنید

**تلگرام:** @lvlRF

---

## 🔄 آپدیت

برای آپدیت به نسخه جدید:
```bash
# استاپ service
systemctl stop lvlrf-dashboard

# جایگزینی فایل
cp dashboard-new.py /root/backhaul-core/dashboard.py

# استارت service
systemctl start lvlrf-dashboard
```

---

**نسخه:** 2.0  
**تاریخ:** 2026-01-06  
**سازنده:** @lvlRF
