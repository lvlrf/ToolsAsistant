# Rebecca Panel — Claude Code Briefing Document

## محیط کار

| آیتم | مقدار |
|------|-------|
| سرور | `91.107.166.136` (root / 123.123.) |
| مسیر پروژه | `/opt/rebecca` |
| پنل | `https://dash.giftchi.link:10000/vdash` |
| یوزر پنل | `admin-admin` / `321.321.` |
| Branch | `dev` |
| Python | `3.13` |
| SQLite DB | `/opt/rebecca/db.sqlite3` |
| Service | `systemctl status rebecca` |

## ریپوها برای مرجع

```
Rebecca dev:     https://github.com/rebeccapanel/Rebecca/tree/dev
Rebecca scripts: https://github.com/rebeccapanel/Rebecca-scripts
Rebecca node:    https://github.com/rebeccapanel/Rebecca-node/tree/dev
Marzban:         https://github.com/Gozargah/Marzban
Marzneshin:      https://github.com/marzneshin/marzneshin
Remnawave:       https://github.com/remnawave/panel
Remnawave SDK:   https://github.com/remnawave/xtls-sdk
```

## معماری سیستم

- **Master server** (ایران، ایرانسل): فقط مدیریت یوزر + پنل
- **Nodes** (خارج): ترافیک واقعی کاربران از اینجا رد میشه
- ارتباط master ↔ node از طریق gRPC
- ترافیک مصرفی از node به master گزارش میشه

---

## مشکلات به ترتیب اولویت

### 🔴 مشکل 1 — کاربران بعد از اتمام حجم قطع نمیشن (CRITICAL)

**توضیح:**
کاربران بعد از مصرف کامل حجم مجازشون همچنان میتونن ترافیک عبور بدن.
اسکریپت `/opt/rebecca/rebecca_overuse.py` میزان overuse رو نشون میده.
آخرین run: ~261GB overuse در 244 کاربر.

**سوالات برای بررسی:**
- آیا xray config با کاربران `limited` درست push میشه به nodeها؟
- آیا `statsInboundUplink/Downlink` درست کار میکنه؟
- آیا job `record_user_usages` که هر 10 ثانیه اجرا میشه درست status کاربر رو آپدیت میکنه؟
- آیا بعد از تغییر status به `limited`، xray restart/reload میشه؟
- مقایسه با Marzban/Remnawave: اونا چطور این کار رو میکنن؟

**فایل‌های مرتبط:**
```
/opt/rebecca/app/jobs/usage/user_usage.py
/opt/rebecca/app/jobs/usage/outbound_traffic.py
/opt/rebecca/app/db/crud.py  (تابع disable_user یا مشابه)
/opt/rebecca/app/runtime/xray.py
/opt/rebecca/xray_api/
```

**علائم:**
```
Execution of job "record_user_usages" skipped: maximum number of running instances reached (1)
```
این یعنی job قبلی هنوز تموم نشده — احتمالاً به خاطر SQLite کند یا query سنگین.

---

### 🔴 مشکل 2 — ترافیک phantom (مصرف اشتباه)

**توضیح:**
کاربران ادعا دارن ترافیک مصرف نکردن ولی سیستم براشون حجم زده.
حتی وقتی گوشی خاموش بوده یا VPN بسته بوده.

**سوالات برای بررسی:**
- آیا xray stats API درست cleanup میشه؟
- آیا after reset، stats قبلی صفر میشن؟
- آیا مشکل double-counting وجود داره؟ (هم inbound هم outbound count بشه)
- بررسی کن `statsInboundUplink` vs `statsOutboundUplink` — کدوم use میشه؟
- آیا ترافیک DNS (overhead) به حساب کاربر میاد؟

**فایل‌های مرتبط:**
```
/opt/rebecca/app/jobs/usage/user_usage.py
/opt/rebecca/xray_api/stats.py (یا مشابه)
```

---

### 🟡 مشکل 3 — گزارش ترافیک ناقص/اشتباه

**توضیح:**
مصرف واقعی outbound (که owner پول میده) با چیزی که پنل نشون میده فرق داره.
پنل خیلی کمتر از مصرف واقعی نشون میده.

**معماری ترافیک:**
```
کاربر → Node Inbound → Outbound خریداری شده → اینترنت
```
هر Outbound یه provider داره که owner بهش پول میده.

**سوالات برای بررسی:**
- آیا `outbound_traffic` table درست populate میشه؟
- آیا ترافیک node-to-master sync درست کار میکنه؟
- مقایسه: `users.used_traffic` vs `outbound_traffic` vs `node_usages`
- آیا گزارش Usage در پنل همه این منابع رو aggregate میکنه؟

**فایل‌های مرتبط:**
```
/opt/rebecca/app/jobs/usage/outbound_traffic.py
/opt/rebecca/app/routers/system.py
/opt/rebecca/app/db/models.py  (OutboundTraffic, NodeUsages)
```

---

### 🟡 مشکل 4 — قطع ارتباط مکرر node ↔ master در ایران

**توضیح:**
ارتباط gRPC بین پنل مستر (ایران) و nodeها (خارج) مکرر قطع میشه.
وقتی قطع میشه:
1. ترافیک کاربران گزارش نمیشه
2. کاربرهای limited قطع نمیشن
3. وقتی وصل میشه، ممکنه داده‌های buffered از دست بره

**خواسته‌ها:**
- node باید locally بدونه کدوم کاربر limited/expired هست
- اگه ارتباط با master قطع شد، node باید از آخرین state استفاده کنه
- buffer کردن usage stats و sync کردن بعد از reconnect
- مکانیزم fallback برای ارتباط (مثلاً WebSocket به جای gRPC خالص)

**بررسی کن:**
- Remnawave چطور این مشکل رو حل کرده؟ (SDK جداگانه دارن)
- Marzneshin چه معماری برای node communication داره؟
- آیا میشه xray policy-based traffic limit رو روی خود node enforce کرد؟

**فایل‌های مرتبط:**
```
/opt/rebecca/app/node/  (اگه وجود داره)
/opt/rebecca/xray_api/
https://github.com/rebeccapanel/Rebecca-node/tree/dev
```

---

### 🟢 مشکل 5 — باگ‌های فنی شناخته‌شده (از نصب)

اینا رو هم بررسی و fix کن:

**5a. APScheduler compatibility:**
```python
# pyproject.toml داره:
apscheduler==3.9.1.post1
# ولی با Python 3.13 کار نمیکنه (pkg_resources removed)
# باید به 3.10.4+ آپگرید بشه
```

**5b. packaging dependency:**
```
# packaging در requirements نیست ولی در کد import میشه
# باید به dependencies اضافه بشه
```

**5c. 404.html برای SPA routing:**
```python
# dashboard/__init__.py خط 59:
with open(build_dir / "404.html", "w") as file:
# این فایل باید بعد از build ساخته بشه
# الان باید دستی cp index.html 404.html بزنیم
```

**5d. SQLite WAL mode و timeout:**
```
# DB با concurrent access lock میشه
# WAL mode و timeout=30 باید default باشه
# الان دستی set کردیم
```

**5e. subscription_path migration:**
```
# dev branch مسیر رو از api.v2 به sub تغییر داد
# کاربران قدیمی لینکشون 404 میده
# migration script لازمه
```
### مشکل 6 باک های فنی یا پیشنهادات برای ارتقا سیستم مبنی بر بررسی های خودت یا مبنی بر دیدن مستندات و کد های پنل های دیگه لیست مرجع 

این محیط سرور تست هستش نودی وصل نیستش بک آپ از سرور اصلی روی نسحه dev ربکا هستش
---

## دستورالعمل Claude Code

### مرحله 1 — آنالیز و گزارش

قبل از هر تغییری:

1. سورس کد `/opt/rebecca` رو کامل بخون
2. مقایسه کن با Marzban، Marzneshin، Remnawave
3. یه گزارش کامل بده:
   - root cause هر مشکل
   - فایل‌های مرتبط
   - راه حل پیشنهادی
   - risk هر تغییر
4. گزارش رو به صورت `ANALYSIS_REPORT.md` ذخیره کن

### مرحله 2 — Fix کردن (بعد از تایید)

فقط بعد از اینکه گزارش تایید شد، تغییرات رو اعمال کن.

**اولویت fix:**
1. مشکل 1 (قطع نشدن کاربر) — بالاترین اولویت مالی
2. مشکل 5 (باگ‌های فنی) — برای stability
3. مشکل 3 (گزارش ترافیک)
4. مشکل 2 (phantom traffic)
5. مشکل 4 (node resilience) — نیاز به تغییرات معماری داره

### نکات مهم

- **تست کن** قبل از اعمال هر تغییر
- **backup بگیر** از DB قبل از migration
- **لاگ** تغییرات رو نگه دار
- **سرویس رو restart** بعد از هر تغییر و چک کن
- اگه fix نیاز به تغییر node داره، Rebecca-node repo رو هم بررسی کن

### دسترسی

```bash
# سرور
ssh root@91.107.166.136  # pass: 123.123.

# سرویس
systemctl status rebecca
journalctl -u rebecca -f

# DB
sqlite3 /opt/rebecca/db.sqlite3

# محیط Python
source /opt/rebecca/.venv/bin/activate
```

---

## وضعیت فعلی سیستم

```
Master: ایران (ایرانسل) — IP: [ایران IP]
Nodes:  Asiatech, Arvan-Simin, DyarPishgaman (همه xray v26.2.6)
DB:     SQLite با WAL mode (دستی set شده)
Users:  ~400+ کاربر
Overuse: 261GB در 244 کاربر (مشکل حیاتی)
```

---

*این فایل توسط Claude ساخته شده بر اساس session نصب و troubleshoot Rebecca panel.*
