# گزارش تحلیل کامل Rebecca Panel

**تاریخ**: 2026-04-15  
**نسخه بررسی‌شده**: dev branch  
**سرور تست**: 91.107.166.136  
**DB**: `/root/Rebecca/db.sqlite3`  

---

## خلاصه وضعیت فعلی سرور

| آیتم | وضعیت |
|------|--------|
| Python venv | APScheduler 3.10.4 نصب شده ✅ |
| SQLite mode | DELETE (نه WAL) ⚠️ |
| SQLite busy_timeout | 5000ms ⚠️ |
| کاربران active | 175 نفر |
| کاربران limited | 241 نفر |
| کاربران expired | 7 نفر |
| Overuse در limited users | ~279 GB |
| نودها | همه در وضعیت error/connecting |
| سرویس rebecca | غیرفعال (test environment) |

---

## مشکل 1 — کاربران بعد از اتمام حجم قطع نمیشن (CRITICAL)

### Root Cause (چند لایه‌ای)

**لایه اول: جریان طبیعی کارکرد**

```
record_user_usages() [هر 10 ثانیه]
  → از API xray آمار می‌گیره (reset=True)
  → used_traffic در DB آپدیت میشه
  → _enforce_user_limits_and_expiry() فراخوانی میشه
      → user.status = "limited"
      → xray.operations.remove_user(user) فراخوانی میشه
          → فقط از نودهای CONNECTED حذف میشه ⚠️
```

**لایه دوم: مشکل اصلی — نود قطع‌شده**

فایل `app/reb_node/operations.py:remove_user()`:
```python
def remove_user(dbuser):
    for inbound_tag in state.config.inbounds_by_tag:
        _remove_user_from_inbound(state.api, inbound_tag, email)
        for node in list(state.nodes.values()):
            if node.connected and node.started:  # ← اگه نود قطع باشه، skip میشه!
                _remove_user_from_inbound(node.api, inbound_tag, email)
```

وقتی نود disconnect است:
1. کاربر از DB به `limited` تغییر میکنه ✅  
2. `remove_user()` از master حذف میشه ✅  
3. از نود **حذف نمیشه** ❌ → کاربر روی نود ترافیک عبور میده!

**لایه سوم: reconnect نود**

فایل `app/reb_node/config.py:include_db_users()`:
```python
.filter(db_models.User.status.in_([UserStatus.active, UserStatus.on_hold]))
```
وقتی نود reconnect میشه، config فقط شامل `active` و `on_hold` است. پس کاربر `limited` بعد از reconnect قطع میشه — اما این **دیر** اتفاق میفته.

**لایه چهارم: job skipping**

لاگ: `"Execution of job 'record_user_usages' skipped: maximum number of running instances reached (1)"`

فایل `app/jobs/usage/__init__.py`:
```python
scheduler.add_job(
    record_user_usages,
    "interval",
    seconds=JOB_RECORD_USER_USAGES_INTERVAL,  # 10 ثانیه
    coalesce=True,
    max_instances=1,  # ← اگه job قبلی هنوز تموم نشده، skip میشه
    ...
)
```

جاب هر 10 ثانیه یه بار اجرا میشه. اگه بیشتر از 10 ثانیه طول بکشه:
- stats جمع‌آوری نمیشه
- enforcement اجرا نمیشه
- کاربر تا اجرای بعدی همچنان ترافیک مصرف میکنه

### تأثیر مالی

- 241 کاربر limited با 279 GB overuse
- overuse روی نودها اتفاق افتاده چون ارتباط master-node قطع بوده

### راه‌حل پیشنهادی

**راه‌حل 1 (کوتاه‌مدت — کم‌ریسک):**  
وقتی نود reconnect میشه، قبل از push کردن config جدید، یه بررسی اضافه کن که کاربرهای `limited/expired` رو صراحتاً از نود حذف کنه:

```python
# در _connect_node_impl، بعد از node.start(config):
def _cleanup_limited_users_on_reconnect(node, db):
    """Remove any limited/expired users that might be running on the node."""
    limited_users = db.query(User).filter(
        User.status.in_([UserStatus.limited, UserStatus.expired])
    ).all()
    for user in limited_users:
        email = f"{user.id}.{user.username}"
        for inbound_tag in state.config.inbounds_by_tag:
            try:
                node.api.remove_inbound_user(tag=inbound_tag, email=email, timeout=30)
            except Exception:
                pass
```

**راه‌حل 2 (میان‌مدت — مهم):**  
افزایش `JOB_RECORD_USER_USAGES_INTERVAL` به 30 ثانیه و `JOB_REVIEW_USERS_INTERVAL` به 30 ثانیه تا احتمال skipping کمتر بشه.  
یا: موازی‌سازی جمع‌آوری آمار از نودها (هم‌اکنون با ThreadPoolExecutor انجام میشه — timeout را از 30s به 15s کاهش بده).

**راه‌حل 3 (بلندمدت — معماری):**  
پیاده‌سازی xray policy-based limit روی خود نودها (مشابه Remnawave). جزئیات در مشکل 4.

### ریسک

- راه‌حل 1: ریسک کم — فقط یه cleanup اضافه میشه
- راه‌حل 2: ریسک کم — فقط interval تغییر میکنه
- راه‌حل 3: نیاز به تغییر معماری — ریسک بالا

---

## مشکل 2 — ترافیک phantom (مصرف اشتباه)

### آنالیز

**جمع‌آوری آمار:**

فایل `app/jobs/usage/collectors.py`:
```python
def get_users_stats(api: XRayAPI):
    params = defaultdict(int)
    for stat in filter(attrgetter("value"), api.get_users_stats(reset=True, ...)):
        params[stat.name.split(".", 1)[0]] += stat.value  # uplink + downlink جمع میشه
    return [{"uid": uid, "value": value} for uid, value in params.items()]
```

- `reset=True` → آمار بعد از هر collection پاک میشه ✅ (double-counting نیست)
- هر دو uplink و downlink کاربر جمع میشن ✅ (صحیح)
- `usage_coefficient = 1.0` برای همه نودها ✅ (ضریب تضعیف نیست)

**پیکربندی stats در xray:**

فایل `app/reb_node/config.py:_apply_api()`:
```python
"levels": {"0": {"statsUserUplink": True, "statsUserDownlink": True}},
"system": {
    "statsInboundDownlink": False,  # ← inbound stats غیرفعال (double count نمیشه)
    "statsInboundUplink": False,
    "statsOutboundDownlink": True,
    "statsOutboundUplink": True,
}
```

### علت احتمالی phantom traffic

1. **Overhead پروتکل**: handshake های TCP/TLS، DNS queries، keepalive packets — همه به حساب کاربر میان. یه کاربر بدون استفاده ظاهری با یه اتصال باز میتونه 100-300 MB overhead داشته باشه.

2. **Background sync های گوشی**: وقتی صفحه قفله ولی VPN فعاله، app ها sync میکنن (ایمیل، notification، OS updates).

3. **احتمال race condition در reset**: اگه `reset_user_data_usage` (هر روز/هفته/ماه چک میکنه) همزمان با `record_user_usages` اجرا بشه، یه بازه کوچک وجود داره که DB usage صفر شده ولی آمار xray هنوز reset نشده — اما این خیلی نادره چون xray stats با `reset=True` در جمع‌آوری هر interval پاک میشن.

### راه‌حل پیشنهادی

1. **لاگ دقیق‌تر**: در `_apply_usage_to_db` یه لاگ اضافه کن که uplink vs downlink رو جداگانه نشون بده تا بشه بررسی کرد کدوم بخش بیشتره.

2. **توضیح به کاربران**: overhead پروتکل واقعیه — مستنداتی تهیه کن که توضیح بده چرا کاربران traffic می‌بینن حتی وقتی صفحه خاموشه.

3. **کاهش overhead**: تنظیم xray برای کاهش keepalive و idle connections.

---

## مشکل 3 — گزارش ترافیک ناقص/اشتباه

### آنالیز

**جریان داده:**

```
xray API (outbound>>> stats)
    ↓ [get_outbounds_stats با cache 10s]
    ↓
    ├─→ record_node_usages() → System.uplink + System.downlink
    └─→ record_outbound_traffic() → OutboundTraffic.uplink + OutboundTraffic.downlink
```

**کش مشترک (shared cache):**

فایل `app/jobs/usage/collectors.py`:
```python
_OUTBOUND_STATS_CACHE: dict[str, tuple[float, list[dict]]] = {}  # in-memory global cache

def get_outbounds_stats(api: XRayAPI, cache_ttl: int = 10):
    # اگه cache hit باشه (در 10 ثانیه)، همون داده برگرداند
    # اگه cache miss، xray API با reset=True صدا زده میشه
```

هر دو جاب در یه interval از **همون داده** استفاده میکنن — double counting نیست.

### علت underreporting

1. **نودهای قطع‌شده**: همه 5 نود فعال در وضعیت `error` هستن. وقتی نود قطعه، آمارش جمع‌آوری نمیشه. هر چقدر نودها بیشتر قطع باشن، کمتر گزارش میشه.

2. **آمار از دست رفته در xray restart**: وقتی یه نود reconnect میشه، xray روی نود restart میشه. آمار accumulated از آخرین collection تا این restart **از بین میره**. این traffic واقعی‌ه که کاربر مصرف کرده ولی هیچ‌وقت گزارش نمیشه.

3. **عدم تطابق System vs OutboundTraffic**:
   - `System.uplink/downlink`: تجمیع از `record_node_usages` — total از همه node outbounds
   - `OutboundTraffic`: per-tag از `record_outbound_traffic` — باید برابر System باشه اگه همه outbound tags tracked باشن
   - اگه بعضی outbound tags در xray config ندارن (مثلاً blackhole/direct) — در `OutboundTraffic` نمیان ولی `System` همه رو count میکنه

### راه‌حل پیشنهادی

1. **کوتاه‌مدت**: لاگ کن که وقتی نود قطعه، از کدوم بازه زمانی آمار جمع‌آوری نشده.

2. **بلندمدت**: ذخیره‌سازی آمار روی نود قبل از restart (مشابه Remnawave SDK که buffer local داره) تا بعد از reconnect sync بشه.

---

## مشکل 4 — قطع ارتباط مکرر node ↔ master

### آنالیز

**مکانیزم فعلی:**

فایل `app/reb_node/operations.py`:
- `_connect_node_impl()`: برقراری اتصال gRPC
- `schedule_node_reconnect()`: reconnect با cooldown 20s
- `core_health_check()` (هر 10s): بررسی سلامت نودها، trigger reconnect در صورت لزوم

**مشکلات:**

1. **بدون state محلی روی نود**: نود خودش نمیدونه کدوم کاربرها `limited/expired` هستن — هر چیزی از master میاد
2. **آمار از دست می‌ره**: وقتی نود قطع میشه و xray restart میکنه، آمار جمع‌نشده از بین میره  
3. **کاربر limited همچنان ترافیک عبور میده** در بازه disconnection

**مقایسه با Remnawave:**

Remnawave یه SDK جداگانه (`xtls-sdk`) داره که روی نود اجرا میشه. این SDK:
- لیست کاربران مجاز رو locally cache میکنه
- وقتی master قطعه، از state آخرین sync استفاده میکنه
- آمار رو buffer میکنه و وقتی master وصل شد sync میکنه

**مقایسه با Marzneshin:**

Marzneshin از یه agent جداگانه روی نود استفاده میکنه که:
- با WebSocket به master وصل میشه (نه فقط gRPC)
- fallback mechanism داره

### راه‌حل پیشنهادی

**کوتاه‌مدت (بدون تغییر معماری):**
1. در `_cleanup_limited_users_on_reconnect` (از راه‌حل مشکل 1)
2. افزایش cooldown reconnect به 5-10 ثانیه (هم‌اکنون 8 ثانیه — کافیه)
3. نگه داشتن last known state در Redis (اگه Redis فعال باشه)

**بلندمدت (تغییر معماری — ریسک بالا):**
1. نود باید لیست کاربران active/limited رو local داشته باشه
2. sync دوری state از master به نودها (مثلاً هر 60 ثانیه)
3. buffer آمار در نود و sync بعد از reconnect

---

## مشکل 5 — باگ‌های فنی

### 5a. APScheduler compatibility

**وضعیت فعلی:**
- `pyproject.toml`: `apscheduler==3.9.1.post1` ← **اشتباه**
- `venv/site-packages`: `APScheduler-3.10.4` ← **صحیح** (نصب‌شده)
- Python: 3.12.3 (نه 3.13 که در brief گفته شده)

**تأثیر**: کد کار میکنه (venv درسته)، ولی `pyproject.toml` گمراه‌کننده‌ست.

**Fix**: در `pyproject.toml` تغییر:
```toml
# از:
"apscheduler==3.9.1.post1",
# به:
"apscheduler>=3.10.4",
```

**ریسک**: کم — فقط مستندات/install command درست میشه

---

### 5b. packaging dependency

**وضعیت فعلی:**
- `app/routers/subscription.py` line 2: `from packaging.version import Version as LooseVersion`
- `venv`: `packaging-26.0` نصب شده ✅
- `pyproject.toml`: packaging در dependencies نیست ❌

**تأثیر**: اگه روی یه محیط جدید `pip install .` اجرا بشه، packaging نصب نمیشه و import fail میشه.

**Fix**: در `pyproject.toml` اضافه کن:
```toml
"packaging>=24.0",
```

**ریسک**: خیلی کم

---

### 5c. 404.html برای SPA routing

**وضعیت فعلی:**  
فایل `dashboard/__init__.py`:
```python
def build():
    ...
    with open(build_dir / "index.html", "r") as file:
        html = file.read()
    with open(build_dir / "404.html", "w") as file:
        file.write(html)
```

404.html در `build()` ساخته میشه. مشکل اینه که `build_dir` ممکنه وجود نداشته باشه اگه frontend build نشده باشه.

**وضعیت سرور**: `/opt/rebecca/build/` وجود داره (build شده).

**ریسک**: کم — فقط در fresh deploy مشکل ایجاد میشه

---

### 5d. SQLite WAL mode و timeout

**وضعیت فعلی:**
```
journal_mode: delete  ← باید WAL باشه
busy_timeout: 5000ms  ← خیلی کمه برای concurrent access
```

فایل `app/db/base.py`:
```python
if IS_SQLITE:
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    # ← هیچ WAL یا timeout تنظیم نشده!
```

**تأثیر**: با چند job موازی (record_user_usages + review + record_node_usages + record_outbound_traffic)، SQLite lock contention ایجاد میشه. این میتونه باعث:
- "database is locked" error
- کند شدن jobs → skipping
- خود همین skipping دلیل تکرار مشکل 1 میشه

**Fix — فایل `app/db/base.py`**:
```python
if IS_SQLITE:
    def _on_sqlite_connect(dbapi_con, con_record):
        dbapi_con.execute("PRAGMA journal_mode=WAL")
        dbapi_con.execute("PRAGMA synchronous=NORMAL")
        dbapi_con.execute("PRAGMA busy_timeout=30000")
        dbapi_con.execute("PRAGMA cache_size=-64000")

    from sqlalchemy import event
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    event.listen(engine, "connect", _on_sqlite_connect)
```

**ریسک**: متوسط — WAL mode نیاز به یه migration ندارد ولی باید اطمینان حاصل شه که DB در حین تغییر mode open نیست. روی سرور اصلی باید قبل از restart این کار انجام بشه.

---

### 5e. subscription_path migration

**وضعیت فعلی:**
- `DB subscription_settings.subscription_path`: `'sub'` (مسیر جدید)
- `.env`: `XRAY_SUBSCRIPTION_PATH = "api.v2"` (مسیر قدیم)
- `app/routers/subscription.py` line 60: `router = APIRouter(tags=["Subscription"], prefix="/sub")`

**مسیرهای پشتیبانی‌شده:**
- `/sub/{token}` ← مسیر جدید ✅
- `/api/v1/client/subscribe` ← alias پشتیبانی‌شده ✅
- `/api.v2/{token}` ← **پشتیبانی نمیشه** ❌

**کاربران با لینک قدیمی `api.v2` اکنون 404 میگیرن.**

**Fix — اضافه کردن backward compatibility route:**

در `app/routers/subscription_alias.py` یا یه فایل جداگانه، اضافه کردن:
```python
@router.get("/api.v2/{token}")
async def legacy_api_v2_subscription(token: str, ...):
    """Backward-compatible redirect from old /api.v2/ path."""
    return RedirectResponse(url=f"/sub/{token}", status_code=301)
```

یا در `.env`:
```
XRAY_SUBSCRIPTION_PATH=sub
```
و اضافه کردن alias route در router برای `api.v2`.

**ریسک**: کم — فقط یه route اضافه

---

## مشکل 6 — بررسی‌های اضافی و پیشنهادات ارتقا

### 6a. مشکل: SQLAlchemy Session در jobs — thread safety

فایل `app/db/base.py`:
```python
class GetDB:
    def __init__(self):
        self.db = SessionLocal()
```

چند job بصورت موازی روی SQLite کار میکنن. با `check_same_thread=False`، SQLite از چند thread تحمل می‌کنه ولی با WAL mode بهتر میشه.

**پیشنهاد**: اضافه کردن connection pooling settings برای SQLite:
```python
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    pool_size=10,  # SQLite doesn't need large pool
    max_overflow=5
)
```

---

### 6b. مشکل: گم شدن آمار هنگام node restart

وقتی `record_node_usages` یا `record_outbound_traffic` آمار رو از xray می‌گیره (`reset=True`)، اگه بلافاصله بعد از reset، xray crash کنه یا restart بشه، اون آمار **برای همیشه گم میشه**.

**پیشنهاد**: قبل از `reset=True`، snapshot از آمار رو در Redis یا یه temp table بریز. بعد از موفق بودن DB write، پاک کن.

---

### 6c. پیشنهاد: مانیتورینگ overuse real-time

اسکریپت `rebecca_overuse.py` وجود داره ولی باید scheduling بشه. پیشنهاد:
- یه endpoint اضافه کردن در API که overuse رو real-time نشون بده
- یا scheduler job برای alert کردن ادمین وقتی کاربری overuse داره

---

### 6d. مشکل: retry logic در xray operations

فایل `app/reb_node/operations.py`:
```python
def _remove_inbound_user_attempts(api, inbound_tag, email):
    for _ in range(2):
        try:
            api.remove_inbound_user(...)
        except (EmailNotFoundError, ConnectionError):
            break
        except Exception:
            continue
```

اگه connection temporarily fails، فقط 2 بار retry میشه. با node instability این ممکنه کافی نباشه.

**پیشنهاد**: exponential backoff با 3-5 retry برای critical operations مثل `remove_user`.

---

### 6e. مشکل: Redis غیرفعال است

`.env`: `REDIS_ENABLED = "false"`

با Redis فعال، performance بهتر میشه:
- آمار usage ابتدا در Redis نوشته میشه (سریع‌تر)
- بعداً sync به DB (کاهش lock contention)
- User cache در Redis برای subscription requests سریع‌تر

**پیشنهاد**: فعال‌سازی Redis (سرویس redis در `/opt/rebecca/redis/` موجوده).

---

## اولویت‌بندی Fixes

| اولویت | مشکل | تأثیر | ریسک | زمان تقریبی |
|--------|------|--------|------|------------|
| 🔴 1 | 5d: WAL mode SQLite | کاهش lock/skip | متوسط | 15 دقیقه |
| 🔴 2 | مشکل 1: cleanup on reconnect | کاهش overuse | کم | 30 دقیقه |
| 🟡 3 | 5e: subscription alias api.v2 | کاربران قدیمی | کم | 15 دقیقه |
| 🟡 4 | 5a: pyproject.toml APScheduler | مستندات | کم | 5 دقیقه |
| 🟡 5 | 5b: packaging dependency | fresh deploy | کم | 5 دقیقه |
| 🟢 6 | 6c: overuse monitoring | مانیتورینگ | کم | 1 ساعت |
| 🟢 7 | مشکل 4: node resilience | معماری | بالا | چند روز |

---

## نکات مهم قبل از Fix

1. **این سرور test است** — نود وصل نیست، سرویس غیرفعال است
2. **قبل از هر تغییر DB**: یه backup بگیر از `/root/Rebecca/db.sqlite3`
3. **برای WAL mode**: DB باید بسته باشه (سرویس stop شده باشه)
4. **تست کن**: بعد از هر تغییر سرویس رو start کن و لاگ بررسی کن

---

*گزارش توسط Claude Code — بر اساس بررسی کامل سورس‌کد و وضعیت DB*
