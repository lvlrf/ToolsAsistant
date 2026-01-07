# آپدیت v2.1 - Dashboard تحت وب 🎉

تغییرات عمده در نسخه 2.1

---

## 🆕 چه چیزی اضافه شد؟

### 🌐 Dashboard تحت وب (Live Web Dashboard)

یک dashboard کامل Flask-based با قابلیت کنترل مستقیم سرویس‌ها!

**فایل‌های جدید:**
- `dashboard.py` - Flask server
- `install-dashboard.sh` - نصب خودکار
- `DASHBOARD-README.md` - راهنمای کامل

---

## ✨ قابلیت‌های Dashboard:

### 1. Live Status Monitoring
```
● Active  ○ Inactive
```
- وضعیت real-time همه سرویس‌ها
- Auto-refresh هر 3 ثانیه
- فیلتر بر اساس Active/Inactive

### 2. کنترل مستقیم
```
[▶️ Start] [⏸️ Stop] [🔄 Restart]
```
- بدون نیاز به SSH!
- کلیک → اجرا
- نتیجه فوری

### 3. ویرایش Port
```
[✏️ Edit]
```
- تغییر Port Tunnel
- تغییر Port Web  
- تغییر Port iperf
- Auto-restart بعد از ذخیره

### 4. مشاهده Logs
```
[📜 Logs]
```
- 100 خط آخر
- باز شدن در Modal
- کپی با کلیک

### 5. تست سرعت
```
[⚡ Test Speed]
```
- راهنمای گام‌به‌گام
- دستورات Iran و Kharej
- مرحله به مرحله

### 6. مدیریت Dashboard
```
[⚙️ Dashboard] → [Enable/Disable]
```
- فعال/غیرفعال کردن
- از داخل خود Dashboard
- برای امنیت

### 7. Dark Mode
```
[🌙]
```
- تم تاریک
- ذخیره automatic
- راحت برای چشم

---

## 🔄 تغییرات در Generator:

### اسم سرویس‌ها
```
قبل: backhaul-iran100-tcp-speed
الان: @lvlRF-Tunnel-iran100-tcp-speed
```

**مزایا:**
- شناسایی راحت‌تر
- دسته‌بندی بهتر
- سازگار با Dashboard

---

## 📦 نصب Dashboard:

### مرحله 1: آپلود
```bash
scp dashboard.py install-dashboard.sh root@SERVER:/root/backhaul-core/
```

### مرحله 2: تغییر Password
```bash
nano dashboard.py
# خط 12: DASHBOARD_PASSWORD = "your-password"
```

### مرحله 3: نصب
```bash
bash install-dashboard.sh
```

### مرحله 4: دسترسی
```
http://YOUR_SERVER_IP:8000
```

**پورت دیگه می‌خوای؟**
```python
# dashboard.py خط 11:
DASHBOARD_PORT = 9000
```

---

## 🔐 امنیت:

### 1. Password محافظت شده
- Login page
- Session 24 ساعته
- Logout

### 2. فعال/غیرفعال Dashboard
```bash
systemctl disable lvlrf-dashboard
systemctl stop lvlrf-dashboard
```
وقتی نیاز ندارید، خاموش کنید!

### 3. Firewall
```bash
ufw allow 8000/tcp  # پورت dashboard
```

---

## 🎯 Workflow جدید:

### روش قدیمی (v2.0):
```
1. Generate configs
2. Upload to server
3. SSH to server
4. Run install-services.sh
5. برای هر عملیات: SSH + command
```

### روش جدید (v2.1):
```
1. Generate configs  
2. Upload to server
3. Install dashboard
4. Open browser: http://SERVER:8000
5. همه کارها از Dashboard! 🎉
```

---

## 📊 مقایسه:

| عملیات | v2.0 | v2.1 Dashboard |
|--------|------|----------------|
| **Check Status** | SSH + systemctl | کلیک دکمه |
| **Start Service** | SSH + systemctl | کلیک دکمه |
| **View Logs** | SSH + journalctl | کلیک دکمه |
| **Edit Port** | SSH + nano + systemctl | فرم + ذخیره |
| **Test Speed** | کپی دستورات | راهنمای گام‌به‌گام |
| **Remote Access** | SSH فقط | Browser |

---

## 💡 Use Cases:

### Use Case 1: مدیریت روزانه
```
Morning: باز کردن Dashboard
Check: وضعیت همه سرویس‌ها
Problem? کلیک Restart
Done! ✅
```

### Use Case 2: تست سرعت
```
Dashboard → انتخاب Config → Test Speed
کپی دستورات → اجرا
نتیجه → تصمیم‌گیری
```

### Use Case 3: تغییر Port
```
Dashboard → Edit
تغییر Port → ذخیره
Auto-restart ✅
Check Status ✅
```

### Use Case 4: دسترسی Remote
```
از هر جا: http://SERVER:8000
Login → مدیریت کامل
```

---

## ⚙️ تنظیمات:

### Auto-Refresh
```python
# dashboard.py خط 13:
AUTO_REFRESH_SECONDS = 3  # ثانیه
```

### Session Timeout
```python
# dashboard.py خط 26:
app.permanent_session_lifetime = timedelta(hours=24)
```

### Allowed IPs (اختیاری)
```python
# فقط از IP های خاص:
ALLOWED_IPS = ['1.2.3.4', '5.6.7.8']
```

---

## 🐛 مشکلات احتمالی:

### Dashboard باز نمی‌شه؟
```bash
# چک service:
systemctl status lvlrf-dashboard

# چک logs:
journalctl -u lvlrf-dashboard -f

# چک firewall:
ufw status | grep 8000
```

### Password نمی‌شناسه؟
```bash
# تغییر password در کد
nano dashboard.py

# restart service
systemctl restart lvlrf-dashboard
```

### سرویس‌ها کنترل نمیشن؟
- اطمینان از اجرا با root
- چک کردن مسیر فایل‌ها
- state.json و config.json موجود باشند

---

## 📱 دسترسی از موبایل:

Dashboard responsive هست:
```
📱 موبایل → Chrome/Safari
🔐 Login
👆 کلیک دکمه‌ها
✅ کار می‌کنه!
```

---

## 🔄 Migration از v2.0:

### اگر v2.0 داری:

**مرحله 1:** دانلود v2.1
**مرحله 2:** اجرای generator با v2.1 (configs جدید می‌سازه)
**مرحله 3:** نصب Dashboard
**مرحله 4:** لذت بردن! 🎉

**نکته:** Config های قدیمی با Dashboard کار می‌کنن اما اسم‌شون فرق داره.

---

## 📚 منابع:

- **DASHBOARD-README.md:** راهنمای کامل Dashboard
- **README.md:** راهنمای اصلی
- **TROUBLESHOOTING.md:** عیب‌یابی

---

## 🎉 خلاصه:

**v2.1 =**
- ✅ همه چیز v2.0
- ✅ Dashboard تحت وب
- ✅ کنترل real-time
- ✅ ویرایش Port
- ✅ تست سرعت
- ✅ مدیریت Dashboard
- ✅ Dark mode
- ✅ Remote access

**نتیجه:**
مدیریت تانل‌ها **10 برابر راحت‌تر** شد! 🚀

---

**نسخه:** 2.1  
**تاریخ:** 2026-01-06  
**تغییرات عمده:** Dashboard تحت وب
