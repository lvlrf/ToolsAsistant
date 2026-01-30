# 🚀 راهنمای سریع نصب Sub-Relay

## 📥 دانلود و استقرار

```bash
# آپلود فایل zip به سرور و استخراج
unzip sub-relay.zip
cd sub-relay
chmod +x *.sh
```

## ⚙️ تنظیمات اولیه (5 دقیقه)

### 1️⃣ ویرایش config.env

```bash
nano config.env
```

**حداقل تنظیمات:**
- `SUB_DOMAIN` → دامنه شما
- `PANEL_URL` → آدرس پنل مرزبان
- `EXISTING_SNI` → SNI سرویس فعلی

**برای WireGuard:**
- کلیدهای WireGuard را بسازید و وارد کنید

**برای Xray:**
- `XRAY_UUID` و سایر مشخصات کانکشن را وارد کنید

### 2️⃣ دریافت SSL

```bash
certbot certonly --standalone -d YOUR_SUB_DOMAIN
```

### 3️⃣ جابجایی سرویس فعلی به پورت 8443

```bash
# کانفیگ Xray فعلی را ویرایش کنید
nano /usr/local/etc/xray/config.json
# پورت 443 را به 8443 تغییر دهید

systemctl restart xray
```

### 4️⃣ نصب

```bash
sudo ./install.sh
```

### 5️⃣ فعال‌سازی

```bash
# انتخاب یکی از دو مدل:
sudo ./switch-mode.sh wireguard
# یا
sudo ./switch-mode.sh xray
```

## 🎯 دسترسی

- **داشبورد:** `http://YOUR_IP:8080`
- **Subscription:** `https://YOUR_SUB_DOMAIN/sub/TOKEN`

## 📊 بررسی وضعیت

```bash
# همه سرویس‌ها
systemctl status haproxy
systemctl status sub-relay-dashboard

# WireGuard
wg show wg0

# Xray
systemctl status xray-client
```

## 🔧 دستورات مفید

```bash
# تغییر مدل
./switch-mode.sh wireguard
./switch-mode.sh xray

# مشاهده لاگ
journalctl -u haproxy -f
journalctl -u sub-relay-dashboard -f

# ریستارت
systemctl restart haproxy
systemctl restart sub-relay-dashboard
```

## 📝 فایل‌های کلیدی

- `config.env` → تمام تنظیمات
- `install.sh` → نصب اولیه
- `switch-mode.sh` → تغییر بین WireGuard و Xray
- `README-FA.md` → راهنمای کامل

## ⚠️ نکات مهم

1. **DNS:** رکورد A دامنه به IP سرور ایران
2. **Firewall:** پورت‌های 443، 8080، 51820 باز باشند
3. **سرویس فعلی:** حتماً به پورت 8443 منتقل شود
4. **WireGuard:** هم روی سرور ایران و هم خارج نصب شود

## 🆘 پشتیبانی

مشکل داری؟ README-FA.md رو بخون یا با ما در تماس باش:
- Telegram: @drconnect
- کانال: @lvlRF

---

**موفق باشی! 🎉**
