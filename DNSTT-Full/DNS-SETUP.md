# راهنمای کامل تنظیم DNS

این راهنما به شما کمک میکنه که DNS رو برای slipstream tunnel به درستی تنظیم کنی.

---

## 🎯 هدف

برای اینکه slipstream tunnel کار کنه، باید یک NS record در DNS تنظیم کنی که به سرور خارج point کنه.

---

## 📋 پیش‌نیازها

- یک دامنه (مثل `irihost.com`)
- دسترسی به DNS Panel دامنه
- IP سرور خارج

---

## 🔧 مراحل تنظیم

### مرحله 1: تعیین نام‌ها

```
دامنه اصلی: irihost.com
Subdomain برای tunnel: t
Tunnel domain: t.irihost.com
Nameserver: ns1.irihost.com
Server IP: [IP سرور خارج]
```

### مرحله 2: افزودن A Record

در DNS Panel، یک **A Record** اضافه کن:

| Type | Name | Value | TTL |
|------|------|-------|-----|
| A    | ns1  | [IP سرور خارج] | 300 |

**مثال:**
```
Type: A
Name: ns1
Value: 185.123.45.67
TTL: 300
```

این کار باعث میشه که `ns1.irihost.com` به IP سرور خارج point کنه.

### مرحله 3: افزودن NS Record

حالا یک **NS Record** برای subdomain tunnel اضافه کن:

| Type | Name | Value | TTL |
|------|------|-------|-----|
| NS   | t    | ns1.irihost.com | 300 |

**مثال:**
```
Type: NS
Name: t
Value: ns1.irihost.com
TTL: 300
```

این کار باعث میشه که تمام query های `*.t.irihost.com` به سرور خارج فرستاده بشن.

---

## 🌐 مثال‌ها برای DNS Provider های مختلف

### Cloudflare

1. ورود به Dashboard → Domain انتخاب → DNS
2. Add Record:
   - **Type:** A
   - **Name:** ns1
   - **IPv4 address:** [IP سرور]
   - **Proxy status:** DNS only (خاکستری)
   - **TTL:** Auto
3. Add Record:
   - **Type:** NS
   - **Name:** t
   - **Nameserver:** ns1.irihost.com
   - **TTL:** Auto

⚠️ **نکته:** حتماً Proxy رو **DNS only** بذار (خاکستری)، نه Proxied (نارنجی)!

### Namecheap

1. Dashboard → Domain List → Manage → Advanced DNS
2. Add New Record:
   - **Type:** A Record
   - **Host:** ns1
   - **Value:** [IP سرور]
   - **TTL:** 5 min
3. Add New Record:
   - **Type:** NS Record
   - **Host:** t
   - **Value:** ns1.irihost.com
   - **TTL:** 5 min

### GoDaddy

1. My Products → DNS → Manage DNS
2. Add Record:
   - **Type:** A
   - **Name:** ns1
   - **Value:** [IP سرور]
   - **TTL:** 1 Hour
3. Add Record:
   - **Type:** NS
   - **Name:** t
   - **Nameserver:** ns1.irihost.com
   - **TTL:** 1 Hour

---

## ✅ تست و بررسی

### تست A Record

```bash
dig @8.8.8.8 ns1.irihost.com A
```

**خروجی مورد انتظار:**
```
ns1.irihost.com.    300    IN    A    185.123.45.67
```

### تست NS Record

```bash
dig @8.8.8.8 t.irihost.com NS
```

**خروجی مورد انتظار:**
```
t.irihost.com.    300    IN    NS    ns1.irihost.com.
```

### تست با nslookup

```bash
nslookup -type=NS t.irihost.com 8.8.8.8
```

### تست از DNS های مختلف

```bash
# Google DNS
dig @8.8.8.8 t.irihost.com NS

# Cloudflare DNS
dig @1.1.1.1 t.irihost.com NS

# Quad9 DNS
dig @9.9.9.9 t.irihost.com NS
```

---

## ⏱️ زمان Propagation

- **حداقل:** 5 دقیقه
- **معمولی:** 10-30 دقیقه
- **حداکثر:** 24-48 ساعت (نادر)

**نکته:** TTL کمتر = propagation سریع‌تر

---

## 🧪 ابزارهای آنلاین برای تست

### 1. DNSChecker
- URL: https://dnschecker.org
- Type: NS
- Domain: t.irihost.com

### 2. WhatsMyDNS
- URL: https://whatsmydns.net
- Type: NS
- Domain: t.irihost.com

### 3. DNS Propagation Checker
- URL: https://www.whatsmydns.net

---

## ❌ مشکلات رایج و حل آن‌ها

### مشکل 1: A Record propagate نشده

**علت:** DNS هنوز به‌روزرسانی نشده

**حل:**
1. صبر کن 10-15 دقیقه
2. Cache DNS رو پاک کن:
   ```bash
   sudo systemd-resolve --flush-caches
   ```
3. دوباره تست کن

### مشکل 2: NS Record نادرست است

**علت:** Value در NS record اشتباه است

**حل:**
1. مطمئن شو Value باید `ns1.irihost.com` باشه (با dot در آخر یا بدون dot - بستگی به provider)
2. نباید IP بذاری، باید hostname بذاری

### مشکل 3: Cloudflare Proxy مشکل ایجاد میکنه

**علت:** Proxy روی NS record نمیتونه فعال باشه

**حل:**
1. Status رو به **DNS only** تغییر بده (خاکستری)
2. Proxy فقط برای A record های normal کار میکنه

### مشکل 4: Subdomain conflict

**علت:** قبلاً یک record با همین نام وجود داره

**حل:**
1. چک کن هیچ record دیگه‌ای با نام `t` نباشه
2. اگه هست، حذفش کن یا یک نام دیگه انتخاب کن

---

## 🔄 تنظیمات پیشرفته (اختیاری)

### استفاده از چند Nameserver

برای High Availability میتونی چند NS اضافه کنی:

```
A Record: ns1 → Server IP 1
A Record: ns2 → Server IP 2

NS Record: t → ns1.irihost.com
NS Record: t → ns2.irihost.com
```

### TTL Tuning

- **Development:** TTL = 300 (5 min) برای تست سریع
- **Production:** TTL = 3600 (1 hour) برای بار کمتر
- **Stable:** TTL = 86400 (24 hours) برای کاهش query ها

---

## 📝 Checklist

- [ ] A Record برای ns1 اضافه شد
- [ ] NS Record برای t اضافه شد
- [ ] تست A Record با dig
- [ ] تست NS Record با dig
- [ ] صبر کردم برای propagation (حداقل 10 دقیقه)
- [ ] تست از DNS های مختلف
- [ ] بررسی با DNSChecker آنلاین

---

## 🚀 مراحل بعدی

بعد از propagation موفق DNS:

1. روی سرور خارج، slipstream server رو start کن
2. روی سرور ایران، slipstream client رو start کن
3. تست کن اتصال برقرار میشه

---

## 💡 نکات مهم

- **همیشه** ابتدا A record رو اضافه کن، بعد NS record
- **هرگز** IP مستقیم در NS record نذار (باید hostname باشه)
- **حتماً** Cloudflare Proxy رو خاموش کن
- **اگر** دامنه جدید خریدی، ممکنه 24 ساعت طول بکشه تا Nameserver ها فعال شن

---

## 📞 کمک بیشتر

اگر مشکلی پیش اومد:

1. اسکریپت راهنما رو اجرا کن:
   ```bash
   ./scripts/setup-dns.sh
   ```

2. دستی تست کن با dig و nslookup

3. Screenshots از DNS Panel بگیر و بررسی کن

---

**نسخه:** 1.0  
**تاریخ:** ۱۴۰۳/۱۰/۲۷  
**تهیه‌کننده:** DrConnect (@drconnect)
