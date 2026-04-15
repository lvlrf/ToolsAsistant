# Rebecca Panel — گزارش تحلیل کامل v2
## (مقایسه با Marzban، Marzneshin، Remnawave)

**تاریخ**: 2026-04-15  
**نسخه**: dev branch — سرور تست: 91.107.166.136  
**DB**: `/root/Rebecca/db.sqlite3` — بکاپ از سرور اصلی (مارس ۲۰۲۶ تا آوریل ۲۰۲۶)

---

## وضعیت فعلی سرور (snapshot DB)

| متریک | مقدار |
|-------|-------|
| کاربران active | 175 |
| کاربران limited | 241 |
| کاربران expired | 7 |
| Overuse در limited users | **279 GB** |
| System uplink total | 274 GB |
| System downlink total | 1789 GB |
| NodeUsages total | 2063 GB ✓ (با System تطابق دارد) |
| OutboundTraffic total | 963 GB ⚠️ (1100 GB کمتر از System) |
| SQLite journal_mode | `delete` (باید WAL باشد) |
| Redis | غیرفعال |
| نودها | همه در وضعیت error/connecting |

---

## مقایسه معماری پنل‌ها

| ویژگی | **Rebecca** | **Marzban** | **Marzneshin** | **Remnawave** |
|-------|-------------|-------------|----------------|---------------|
| زبان backend | Python/FastAPI | Python/FastAPI | Python/FastAPI | TypeScript/NestJS |
| ارتباط با نود | gRPC (custom) | gRPC (custom) | gRPC streaming | WebSocket/gRPC |
| User limit enforcement | ✅ dual job | ✅ review job | ✅ async review | ✅ NestJS scheduler |
| Error handling در remove_user | ✅ try-catch | ❌ بدون try-catch | ✅ async try | ✅ |
| Queue برای نود offline | ❌ نه | ❌ نه | ❌ نه | ⚠️ partial |
| Local state روی نود | ❌ نه | ❌ نه | ❌ نه | ⚠️ partial (SDK) |
| Skip disconnected node | ✅ (`if connected`) | ✅ (`if connected`) | ✅ (`if synced`) | N/A |
| Unique constraint روی outbound tag | ❌ **باگ** | N/A | N/A | N/A |
| WAL mode SQLite | ❌ | ⚠️ | N/A | N/A |
| Async jobs | ❌ sync | ❌ sync | ✅ async | ✅ async |

---

## مشکل 1 — کاربران بعد از اتمام حجم قطع نمیشن (CRITICAL)

### کشف مهم: این یه مشکل Universal است، نه فقط Rebecca!

**Marzban** (کد اصلی که Rebecca از آن fork شده):
```python
# app/xray/operations.py — Marzban
def remove_user(dbuser):
    email = f"{dbuser.id}.{dbuser.username}"
    for inbound_tag in xray.config.inbounds_by_tag:
        _remove_user_from_inbound(xray.api, inbound_tag, email)
        for node in list(xray.nodes.values()):
            if node.connected and node.started:  # ← همان مشکل!
                _remove_user_from_inbound(node.api, inbound_tag, email)
```

**Marzneshin** (async بودن کمکی نمیکند):
```python
# app/marznode/operations.py — Marzneshin
async def update_user(user, remove=True):
    for node_id, tags in node_inbounds.items():
        if marznode.nodes.get(node_id):  # ← اگه node offline باشه skip میشه
            asyncio.ensure_future(
                marznode.nodes[node_id].update_user(user=..., inbounds=tags)
            )
# NO retry queue — fire-and-forget
```

**نتیجه**: هیچ‌کدام از پنل‌های معروف این مشکل رو کامل حل نکردن. هیچ‌کدام queue برای نودهای آفلاین ندارند.

### تفاوت مهم Rebecca vs Marzban

Rebecca **قوی‌تر** از Marzban در این حوزه است:

```python
# Rebecca — user_usage.py
def _enforce_user_limits_and_expiry(db, user_ids):
    # ← اجرا در هر چرخه record_user_usages (هر 10s)
    for user in users:
        if limited:
            xray.operations.remove_user(user)  # با try-catch ✓
        
# همچنین در شروع هر چرخه:
def record_user_usages():
    _enforce_due_active_admins(db)    # ← اجرا حتی بدون traffic جدید
    _enforce_due_active_users(db)     # ← چک همه کاربران active
```

```python
# Marzban — review_users.py
def review():
    for user in active_batch:
        xray.operations.remove_user(user)  # ← بدون try-catch!
        update_user_status(db, user, status)
```

Marzban اگه `xray.operations.remove_user` fail کند، exception کل job را متوقف می‌کند! Rebecca این را handle می‌کند.

### Root Cause واقعی

جریان وقتی نود disconnect است:

```
کاربر حجم تموم میکنه
    ↓
record_user_usages() اجرا میشه
    ↓
used_traffic در DB آپدیت میشه
    ↓
_enforce_user_limits_and_expiry() → user.status = "limited" ✅
    ↓
xray.operations.remove_user(user)
    ├─→ از master حذف میشه ✅
    └─→ for node in nodes:
            if node.connected:  ← نود قطعه → SKIP ❌
                remove from node
    ↓
کاربر روی نود همچنان ترافیک میده تا نود reconnect بشه ⚠️
    ↓
نود reconnect → include_db_users() → فقط active/on_hold → کاربر limited اضافه نمیشه ✅
    → کاربر قطع میشه (دیر) ✓
```

**Window خطرناک**: فاصله بین `قطع شدن نود` تا `reconnect نود` ← در این بازه overuse اتفاق میفته.

### پیشنهاد Remnawave برای حل

Remnawave یه `xtls-sdk` جداگانه دارد (TypeScript) که روی نود اجرا میشود. اما حتی آن هم local state کامل ندارد — فقط gRPC wrapper است.

**تنها راه واقعی**: enforce کردن limit روی **خود نود** بدون نیاز به master.
در xray این قابلیت وجود ندارد (xray policy-based limit ندارد). اما راه کار موقت:

### Fix پیشنهادی — کوتاه‌مدت

**فایل `app/reb_node/operations.py`** — اضافه کردن cleanup بعد از reconnect:

```python
def _connect_node_impl(node_id: int, config=None, *, force: bool = False) -> None:
    ...
    node.start(config)  # config فقط active users دارد — درسته
    
    # ← اضافه کردن این:
    _cleanup_limited_users_from_node(node, node_id)
    ...

def _cleanup_limited_users_from_node(node: XRayNode, node_id: int):
    """
    بعد از reconnect نود، کاربران limited/expired رو صراحتاً حذف کن.
    include_db_users() آن‌ها را اضافه نمی‌کند، ولی ممکن است از قبل در xray باشند.
    """
    try:
        with GetDB() as db:
            limited_users = (
                db.query(User)
                .filter(User.status.in_([UserStatus.limited, UserStatus.expired]))
                .with_entities(User.id, User.username)
                .limit(1000)  # max batch
                .all()
            )
        
        for uid, username in limited_users:
            email = f"{uid}.{username}"
            for inbound_tag in state.config.inbounds_by_tag:
                try:
                    node.api.remove_inbound_user(tag=inbound_tag, email=email, timeout=10)
                except Exception:
                    pass  # user might not exist in this node — that's fine
        
        logger.info(f"Cleanup: removed {len(limited_users)} limited/expired users from node {node_id}")
    except Exception as exc:
        logger.warning(f"Failed to cleanup limited users from node {node_id}: {exc}")
```

**ریسک**: کم — این فقط یک cleanup اضافه است. اگه user روی نود وجود نداشته باشه، `EmailNotFoundError` گرفته میشه که handle شده.

---

## مشکل 2 — ترافیک phantom

### تفاوت با سایر پنل‌ها

Marzban و Marzneshin هم همین مشکل را دارند — هیچ راه‌حل خاصی ندارند.

### آنالیز دقیق Rebecca

```python
# collectors.py
def get_users_stats(api):
    params = defaultdict(int)
    for stat in api.get_users_stats(reset=True):   # reset=True → double-count نیست
        params[stat.name.split(".", 1)[0]] += stat.value  # uplink + downlink هر دو count میشه
    return [{"uid": uid, "value": value} for uid, value in params.items()]
```

**xray policy** (از `_apply_api()` در config.py):
```json
{
  "levels": {"0": {"statsUserUplink": true, "statsUserDownlink": true}},
  "system": {
    "statsInboundDownlink": false,
    "statsInboundUplink": false
  }
}
```

- `inbound stats` غیرفعال ← double-counting بین inbound+user نیست ✅
- `usage_coefficient = 1.0` برای همه نودها ← تضعیف ندارد ✅

### علت واقعی phantom traffic

1. **VPN protocol overhead** (مهم‌ترین علت):
   - TLS handshake: ~6-8 KB per connection
   - TCP ACK: ~40-60 bytes per packet
   - DNS queries: ~200-500 bytes per query (even DIRECT)
   - KeepAlive packets: هر 30 ثانیه اگه اتصال باز باشه
   - برای یه کاربر با 100 اتصال فعال: ~2-5 MB/ساعت overhead فقط keepalive

2. **Background app traffic**: گوشی قفل باشه ≠ VPN بسته باشه. App‌های background (email، push notification، social media sync) همه از VPN رد میشن.

3. **DNS traffic**: بعضی تنظیمات xray همه DNS را از outbound عبور میده.

### پیشنهاد اطلاع‌رسانی به کاربر

هیچ bug کد نیست. اما یه endpoint اضافه برای نشان دادن breakdown:

```python
# روی /api/users/{username}/traffic-breakdown
{
    "uplink_bytes": 1234567,      # upload کاربر
    "downlink_bytes": 8765432,    # download کاربر
    "total_bytes": 9999999,
    "node_breakdown": [           # از کدام نود
        {"node": "Asiatech", "bytes": 5000000},
        ...
    ]
}
```

---

## مشکل 3 — گزارش ترافیک ناقص (باگ جدید کشف شد!)

### باگ کشف شده: Duplicate Tags در `outbound_traffic`

```sql
-- کوئری روی DB واقعی:
SELECT tag, COUNT(*) cnt FROM outbound_traffic GROUP BY tag HAVING cnt > 1;
```
نتیجه:
```
('out-#01', 3)   ← 3 ردیف با همین tag!
('out-#03', 2)
('out-#06', 2)
('out-#09', 2)
('wireguard-import-for-test', 2)
```

**جزئیات `out-#01` (3 ردیف)**:

| id | outbound_id | uplink | downlink | total |
|----|-------------|--------|----------|-------|
| 4 | ff8c90fd... | 45.8 GB | 348.4 GB | **394 GB** |
| 5 | de13076c... | 25.3 GB | 162.0 GB | **187 GB** |
| 51 | ada8fe63... | 3.5 GB | 41.1 GB | **44 GB** |

یعنی ترافیک `out-#01` روی **سه ردیف مجزا** پخش شده!

### Root Cause: بدون UNIQUE constraint + `outbound_id` تغییر میکند

```python
# record_outbound_traffic.py
existing = db.query(OutboundTraffic).filter(OutboundTraffic.tag == tag).first()
if existing:
    existing.uplink += stat.get("up", 0)
    existing.outbound_id = generate_outbound_id(outbound_config)  # ← outbound_id آپدیت میشه!
else:
    new_record = OutboundTraffic(outbound_id=..., tag=tag, ...)
    db.add(new_record)
```

وقتی xray config تغییر کند (مثلاً تغییر outbound settings)، `generate_outbound_id` مقدار جدید میدهد. کد قدیمی قرار بود با `outbound_id` جستجو کند، نه `tag`. در نسخه فعلی با `tag` جستجو میکند که درسته. اما چگونه duplicates ایجاد شدند؟

احتمال: در migration از DB اصلی، ردیف‌هایی که با `outbound_id` متفاوت داشتند از DB قبلی import شدند. یا race condition در migration اولیه.

### تأثیر: گزارش اشتباه

```
OutboundTraffic SUM: 963 GB
System total:       2063 GB
فاصله: 1100 GB (53% گم!)
```

برای `out-#09`:
- Row 1 (id=12): 5.3 GB
- Row 2 (id=13): 4.6 GB
- `db.query(...).first()` فقط ردیف id=12 را آپدیت میکند!
- ردیف id=13 از زمان ایجاد بدون تغییر مانده

**پیشنهاد Fix فوری** — اضافه کردن UNIQUE constraint:

```python
# migration جدید
# app/db/migrations/versions/XXXX_add_unique_tag_to_outbound_traffic.py
def upgrade():
    # اول duplicates را merge کن
    connection = op.get_bind()
    connection.execute("""
        UPDATE outbound_traffic AS t1
        SET uplink = (
            SELECT SUM(t2.uplink) FROM outbound_traffic t2 WHERE t2.tag = t1.tag
        ),
        downlink = (
            SELECT SUM(t2.downlink) FROM outbound_traffic t2 WHERE t2.tag = t1.tag
        )
        WHERE t1.id = (
            SELECT MIN(id) FROM outbound_traffic t3 WHERE t3.tag = t1.tag
        )
    """)
    # حذف duplicates
    connection.execute("""
        DELETE FROM outbound_traffic
        WHERE id NOT IN (
            SELECT MIN(id) FROM outbound_traffic GROUP BY tag
        )
    """)
    # اضافه کردن UNIQUE constraint
    with op.batch_alter_table("outbound_traffic") as batch_op:
        batch_op.create_unique_constraint("uq_outbound_traffic_tag", ["tag"])
```

---

## مشکل 4 — قطع ارتباط node ↔ master

### مقایسه دقیق با سایر پنل‌ها

**Marzneshin** — پیشرفته‌ترین رویکرد:

```python
# app/marznode/grpcio.py
class MarzNodeGRPCIO:
    def __init__(self):
        self._updates_queue = asyncio.Queue(5)  # bounded queue
    
    async def _stream_user_updates(self):
        stream = self._stub.SyncUsers()  # bidirectional streaming
        while True:
            user_update = await self._updates_queue.get()
            await stream.write(UserData(...))
    
    # monitoring task
    async def _monitor(self):
        if state != ChannelConnectivity.READY:
            self.synced = False
            # cancel streaming task
            # reschedule reconnect
```

**Marzneshin مزایا**:
- Bidirectional gRPC streaming (نه request-response)
- KeepAlive built-in در gRPC channel
- `synced` flag برای track کردن state

**Marzneshin معایب**:
- Queue capacity فقط 5! اگه بیشتر از 5 user update در صف باشه → block میشه
- هنوز local state روی نود ندارد
- اگه connection قطع شه → updates از دست میره

**Rebecca vs Marzneshin در reconnect**:

```python
# Rebecca: reconnect → start با config جدید که limited users در آن نیست
node.start(config)  # ← config از include_db_users() که فقط active دارد ✅

# Marzneshin: reconnect → sync کامل مجدد
await self._sync()  # ← push همه users مجدد
```

Rebecca در reconnect صحیح‌تر عمل می‌کند (config بدون limited users push میشه).

### آمار نودهای این سرور

| نود | traffic کل | وضعیت |
|-----|-----------|--------|
| Asiatech (node 3) | **939 GB** | error |
| DyarPishgaman (node 5) | 397 GB | error |
| DyarRespina (node 4) | 295 GB | error |
| Arvan-Simin (node 2) | 113 GB | error |
| Master (None) | 262 GB | - |

### پیشنهاد Fix — کوتاه‌مدت

۱. اضافه کردن xray API keepalive در گزینه‌های gRPC:

```python
# app/reb_node/node.py — اضافه کردن keepalive options
import grpc
channel_options = [
    ('grpc.keepalive_time_ms', 20000),
    ('grpc.keepalive_timeout_ms', 10000),
    ('grpc.keepalive_permit_without_calls', True),
    ('grpc.http2.max_pings_without_data', 0),
]
```

۲. کاهش `_NODE_AUTO_RECONNECT_COOLDOWN_SECONDS` از 20 به 10 در `operations.py`.

---

## مشکل 5 — باگ‌های فنی (به‌روزرسانی‌شده)

### 5a. APScheduler compatibility

| | وضعیت |
|--|--------|
| `pyproject.toml` | `apscheduler==3.9.1.post1` ← **قدیمی** |
| `venv/site-packages` | `APScheduler-3.10.4` ← **صحیح، نصب شده** |
| Python روی سرور | `3.12.3` (نه 3.13!) |

**مقایسه با Marzban**: Marzban هم APScheduler 3.x استفاده می‌کند و همین محدودیت را دارد.

**Fix**:
```toml
# pyproject.toml
"apscheduler>=3.10.4",
```

---

### 5b. packaging dependency

```python
# app/routers/subscription.py:2
from packaging.version import Version as LooseVersion
```

در venv نصب شده (`packaging-26.0`) ولی در `pyproject.toml` نیست.

**Fix**:
```toml
"packaging>=24.0",
```

---

### 5c. 404.html برای SPA routing

فایل `dashboard/__init__.py:62`:
```python
with open(build_dir / "404.html", "w") as file:
    file.write(html)
```

روی سرور `/opt/rebecca/build/` وجود دارد و 404.html ساخته شده. ✅ مشکل فقط در fresh deploy است.

---

### 5d. SQLite WAL mode — باگ تأیید‌شده

```
PRAGMA journal_mode → 'delete'   ← مشکل
PRAGMA busy_timeout → 5000       ← کم است (5 ثانیه)
```

**تأثیر direct روی مشکل ۱**:

با جاب‌های موازی (record_user_usages + review_users + record_node_usages + record_outbound_traffic) همزمان روی SQLite:

```
journal_mode=delete:
  → writer lock کل DB را lock میکند
  → reader‌های دیگر باید منتظر بمانند
  → با busy_timeout=5s → timeout و skip job
  → skip job → enforcement نمیشود → overuse

journal_mode=WAL:
  → writers فقط WAL file را lock میکنند
  → readers همزمان میتوانند بخوانند
  → lock contention به شدت کاهش میابد
```

**Fix — فایل `app/db/base.py`**:

```python
# قبل:
if IS_SQLITE:
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

# بعد:
if IS_SQLITE:
    from sqlalchemy import event

    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_con, con_record):
        dbapi_con.execute("PRAGMA journal_mode=WAL")
        dbapi_con.execute("PRAGMA synchronous=NORMAL")
        dbapi_con.execute("PRAGMA busy_timeout=30000")  # 30 ثانیه
        dbapi_con.execute("PRAGMA cache_size=-64000")   # 64 MB cache
        dbapi_con.execute("PRAGMA mmap_size=268435456") # 256 MB memory-map
```

**ریسک**: متوسط — WAL mode تغییر ساختار فایل DB میدهد (WAL + SHM فایل‌های جانبی اضافه میشند). باید سرویس کاملاً stop باشد.

---

### 5e. subscription_path migration

**وضعیت**:
- `DB.subscription_settings.subscription_path`: `'sub'` ← مسیر فعلی
- `.env`: `XRAY_SUBSCRIPTION_PATH = "api.v2"` ← مسیر قدیمی (override env)

**مسیرهای پشتیبانی‌شده فعلی**:

```python
# app/routers/subscription.py:60
router = APIRouter(prefix="/sub")  # ← /sub/{token}

# app/routers/subscription_alias.py:91
for fixed_prefix in ("/sub/", f"/{primary_path}/"):
    ...
# همچنین:
@router.get("/api/v1/client/subscribe")  # ← پشتیبانی میشه
```

**مسیر `/api.v2/` پشتیبانی نمیشه** — کاربران با لینک قدیمی 404 میگیرند.

**Fix فوری — اضافه کردن backward-compat route**:

در `app/routers/subscription_alias.py`:
```python
@router.get("/api.v2/{token}")
async def legacy_apiv2_redirect(token: str, request: Request):
    """Backward-compatible: old /api.v2/ path → new /sub/ path."""
    return RedirectResponse(url=f"/sub/{token}", status_code=301)
```

**همچنین**: در `.env` مقدار را آپدیت کن:
```
XRAY_SUBSCRIPTION_PATH=sub
```

---

## مشکل 6 — یافته‌های جدید از بررسی کد و مقایسه

### 6a. باگ: Duplicate Outbound Records (از مشکل 3)

**جزئیات**: نگاه کنید به مشکل 3 — `outbound_traffic` نیاز به UNIQUE constraint دارد.

**تأثیر مالی**: گزارش ترافیک خروجی (که owner پول میدهد) **53% کمتر** از واقعیت نشان داده میشود.

---

### 6b. باگ: Cache مشترک بین jobs میتواند Race Condition ایجاد کند

```python
# collectors.py — cache global و shared
_OUTBOUND_STATS_CACHE: dict[str, tuple[float, list[dict]]] = {}

def get_outbounds_stats(api, cache_ttl=10):
    with _OUTBOUND_CACHE_LOCK:
        cached = _OUTBOUND_STATS_CACHE.get(key)
        if cached and now - ts < cache_ttl:
            return cached  # ← record_node_usages و record_outbound_traffic همین میگیرند
    
    # اگه هر دو همزمان cache miss شوند:
    result = api.query_stats("outbound>>>", reset=True)  # ← RESET!
    _OUTBOUND_STATS_CACHE[key] = (now, result)
```

اگه دو job همزمان cache miss داشته باشند و هر دو `reset=True` صدا بزنند:
- job اول: stats V1 را میگیرد، reset میکند
- job دوم (چند میلی‌ثانیه بعد): stats = 0 (چون reset شده)
- نتیجه: V1 یک بار در system ثبت میشه، OutboundTraffic 0 دریافت میکند

**پیشنهاد Fix**:
```python
# اطمینان از اینکه فقط یک caller reset میزند:
def get_outbounds_stats(api, cache_ttl=10):
    with _OUTBOUND_CACHE_LOCK:
        cached = _OUTBOUND_STATS_CACHE.get(key)
        if cached and now - ts < cache_ttl:
            return cached
        # Mark as "being fetched" to prevent concurrent fetches
        _OUTBOUND_STATS_CACHE[key] = (now, [])  # placeholder
    
    result = api.query_stats("outbound>>>", reset=True)
    
    with _OUTBOUND_CACHE_LOCK:
        _OUTBOUND_STATS_CACHE[key] = (now, result)
    return result
```

---

### 6c. باگ: `record_node_usages` از ThreadPoolExecutor نادرست استفاده میکند

```python
# node_usage.py — باگ subtle
def record_node_usages():
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {node_id: executor.submit(get_outbounds_stats, api) ...}
    # ThreadPoolExecutor با with بسته شد → wait for all
    api_params = {node_id: future.result() for ...}  # ← بعد از with → futures تموم شدند
```

`with ThreadPoolExecutor() as executor:` صبر میکند تا همه futures تموم شوند. سپس بیرون از with، `.result()` صدا زده میشه. این ایرادی ندارد ولی inefficient است چون خروج از context manager منتظر می‌ماند.

مقایسه با `record_outbound_traffic`:
```python
# outbound_traffic.py — درست‌تر
with ThreadPoolExecutor(max_workers=10) as executor:
    futures = {node_id: executor.submit(...) ...}
    for node_id, future in futures.items():
        stats_list = future.result()  # ← داخل with
        all_stats.extend(stats_list)
```

---

### 6d. پیشنهاد: فعال‌سازی Redis

`.env` فعلی: `REDIS_ENABLED = "false"`

با Redis فعال:
- آمار usage → Redis (سریع) → بعداً sync به DB
- کاهش lock contention روی SQLite
- User cache → subscription requests سریع‌تر
- Review job از Redis pending usage هم چک میکند

`/opt/rebecca/redis/` در سرور موجود است. فعال‌سازی:
```env
REDIS_ENABLED=true
REDIS_AUTO_START=true
```

---

### 6e. پیشنهاد (از Marzneshin): Async Jobs

Marzneshin همه jobs را async میکند با `asyncio`. این:
- Blocking DB calls روی event loop block نمیکند
- Better resource utilization
- هماهنگی بهتر با FastAPI (که async است)

Rebecca از APScheduler sync استفاده میکند. تغییر به async ریسک بالا دارد ولی در بلندمدت بهتر است.

---

## اولویت‌بندی نهایی

| # | مشکل | فایل | تأثیر | ریسک | زمان |
|---|------|------|-------|------|------|
| 🔴 1 | WAL mode + busy_timeout | `app/db/base.py` | کاهش skip → کمتر overuse | متوسط | 20 دقیقه |
| 🔴 2 | Cleanup limited users on reconnect | `app/reb_node/operations.py` | کاهش مستقیم overuse | کم | 45 دقیقه |
| 🔴 3 | **Duplicate outbound tags** (باگ جدید) | migration جدید | گزارش ترافیک صحیح | کم* | 30 دقیقه |
| 🟡 4 | /api.v2/ backward compat | `app/routers/subscription_alias.py` | کاربران قدیمی | کم | 15 دقیقه |
| 🟡 5 | pyproject.toml dependencies | `pyproject.toml` | مستندات/deploy | کم | 10 دقیقه |
| 🟡 6 | Cache race condition fix | `app/jobs/usage/collectors.py` | گزارش دقیق‌تر | کم | 20 دقیقه |
| 🟢 7 | gRPC keepalive options | `app/reb_node/node.py` | کمتر disconnect | کم | 15 دقیقه |
| 🟢 8 | Redis فعال‌سازی | `.env` | performance | کم | 5 دقیقه |
| 🟢 9 | Node resilience (معماری) | معماری کامل | بلندمدت | بالا | روزها |

*قبل از migration، یه backup از DB بگیر.

---

## مقایسه خلاصه: قبل و بعد از Fix

| معیار | قبل | بعد از Fix‌های 1-6 |
|-------|-----|-------------------|
| SQLite locking | مکرر | نادر |
| Job skipping | گاهی | بندرت |
| Overuse per node disconnect | موجود | کاهش (نه صفر) |
| گزارش outbound traffic | اشتباه (53% کم) | صحیح |
| لینک subscription قدیمی | 404 | redirect |

---

*فایل v1 گزارش: `/opt/rebecca/ANALYSIS_REPORT.md`*  
*این فایل v2: `/opt/rebecca/ANALYSIS_REPORT_V2.md`*  
*Claude Code — بررسی کامل Rebecca + مقایسه Marzban/Marzneshin/Remnawave*
