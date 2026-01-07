# Backhaul Generator v2.3 - Final Fixed

## فایل‌های آماده:

1. **generator.py** - تولید کننده config ها
2. **dashboard.py** - Dashboard وب  
3. **install-dashboard.sh** - نصب کننده Dashboard
4. **tunnel-manager-offline.html** - مدیریت آفلاین (HTML)

---

## تغییرات اعمال شده:

### generator.py:
✅ حذف `@` از اول اسم service
✅ حذف `./` از ExecStart
✅ Unix line endings (LF)

### dashboard.py:
✅ حذف `@` از service name
✅ فیکس وضعیت‌ها: active, stopped, disabled, failed, not-installed
✅ localStorage برای فیلترها (پاک نمیشن با refresh)
✅ Unix line endings (LF)

### install-dashboard.sh:
✅ پرسیدن password با confirm
✅ پرسیدن port (default: 8000)
✅ چک کردن port در حال استفاده
✅ تشخیص خودکار مسیر از config.json
✅ بروزرسانی خودکار dashboard.py
✅ Unix line endings (LF)

### tunnel-manager-offline.html:
✅ کاملاً آفلاین (بدون نیاز به سرور)
✅ بارگذاری state.json از فایل
✅ کپی دستورات با یک کلیک
✅ راهنمای Transport ها
✅ دستورات بهینه‌سازی
✅ مدیریت Dashboard

---

## نحوه استفاده:

### 1. تولید Configs:
```bash
cd /var/lib/@lvlRF-Tunnel
python3 generator.py
# [4] Everything
```

### 2. نصب Dashboard (روی سرور):
```bash
cd /var/lib/@lvlRF-Tunnel  
sudo bash install-dashboard.sh

# سوالات:
Enter password: ****
Confirm password: ****
Enter port [8000]: 

# Firewall:
ufw allow 8000/tcp

# دسترسی:
http://YOUR_SERVER_IP:8000
```

### 3. مدیریت آفلاین (روی Windows):
```
1. دانلود state.json از سرور
2. باز کردن tunnel-manager-offline.html در مرورگر
3. انتخاب فایل state.json
4. کپی دستورات
```

---

## خطای رایج:

❌ `sudo bash dashboard.py`
✅ `python3 dashboard.py`

❌ `$'\r': command not found`  
✅ فایل‌ها با Unix LF هستند

---

## مدیریت:

```bash
# Dashboard
systemctl status lvlrf-dashboard
systemctl restart lvlrf-dashboard
journalctl -u lvlrf-dashboard -f

# Services
systemctl status SERVICE_NAME.service
systemctl start SERVICE_NAME.service
systemctl stop SERVICE_NAME.service
```

---

## نکات مهم:

1. همه فایل‌ها با **Unix line endings** (LF) ذخیره شده‌اند
2. اگر در Windows ویرایش می‌کنید، از Notepad++ استفاده کنید
3. Binary name: `@lvlRF-Tunnel` (با @)
4. Service name: `lvlRF-Tunnel-...` (بدون @)
5. فیلترهای Dashboard ذخیره میشن (localStorage)

---

نسخه: 2.3 Final
تاریخ: 2026-01-06
