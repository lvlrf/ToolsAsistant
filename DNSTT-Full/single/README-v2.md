# 🚀 DNS Tunnel MegaPrompt v2 — Backbone سرور-به-سرور

## نمای کلی

یک لینک backbone با حداکثر throughput بین سرور ایران و سرور خارج از طریق DNS tunnel.
هدف: **۵۰۰+ Mbps پایدار** با قابلیت burst تا **۱ Gbps**.

```
                        ┌─────────────────────────────┐
                        │      سرور خارج (هلند/آلمان)  │
                        │                             │
                        │  slipstream-server ×N        │
                        │    ├─ instance-1 :53         │
                        │    ├─ instance-2 :5353       │
                        │    └─ instance-N :53NN       │
                        │         │                    │
                        │    target → Backhaul/xray    │
                        │         │                    │
                        │    ─── اینترنت آزاد ───      │
                        └────────────▲────────────────┘
                                     │ UDP 53
                            ┌────────┴────────┐
                            │  1000+ Resolver  │
                            │   (ایرانی/عمومی)  │
                            └────────┬────────┘
                                     │ DNS Queries
                        ┌────────────▼────────────────┐
                        │       سرور ایران             │
                        │                             │
                        │  slipstream-client ×N        │
                        │    ├─ instance-1 (250 res.)  │
                        │    ├─ instance-2 (250 res.)  │
                        │    └─ instance-N (250 res.)  │
                        │         │                    │
                        │    bonding/load-balance       │
                        │         │                    │
                        │    Backhaul/xray → کاربران   │
                        └─────────────────────────────┘
```

---

## تغییرات نسبت به v1

| موضوع | v1 | v2 |
|--------|-----|-----|
| هسته تانل | slipstream C (meson build) | slipstream-rust (cargo + picoquic FFI) |
| معماری | تک instance + WireGuard + SOCKS5 | Multi-instance + مستقیم به Backhaul/xray |
| Resolver | فایل resolvers.txt ثابت ۵۰۰ تا | اسکن خودکار + healthcheck + 1000+ |
| حالت عملکرد | فقط recursive | Authoritative (اولویت) + recursive fallback |
| Multi-path | ندارد | QUIC multipath ذاتی + multi-instance bonding |
| لایه بالایی | WireGuard + danted SOCKS5 | حذف — overhead بیخودی برای backbone |
| Congestion | پیشفرض | BBR + CAKE (الگوی استاد) |
| SIP003 | ندارد | ساپورت Shadowsocks plugin |

---

## 📋 مشخصات سرورها

### سرور خارج
- **CPU:** 16 core (یا بیشتر)
- **RAM:** 32 GB
- **Network:** 1 Gbps+
- **OS:** Ubuntu 22.04 / 24.04
- **Location:** نزدیک ایران (هلند/آلمان/ترکیه)
- **Port 53 UDP/TCP:** باز و بدون فیلتر

### سرور ایران
- **CPU:** 16 core (یا بیشتر)
- **RAM:** 32 GB
- **Network:** 1 Gbps+
- **OS:** Ubuntu 22.04 / 24.04
- **دسترسی DNS:** باید بتونه روی پورت 53 به resolver های ایرانی/عمومی query بزنه

---

## 📁 ساختار پروژه

```
dns-tunnel-megaprompt-v2/
├── README.md                          # این فایل
├── configs/
│   ├── server-instance.toml.example   # نمونه config سرور خارج
│   ├── client-instance.toml.example   # نمونه config سرور ایران
│   ├── backhaul-server.toml           # Backhaul سرور خارج
│   ├── backhaul-client.toml           # Backhaul سرور ایران
│   ├── viaDrConnect.conf          # Kernel sysctl tuning
│   └── conntrack-tuning.conf          # conntrack تنظیمات
├── scripts/
│   ├── install-server.sh              # نصب خودکار سرور خارج
│   ├── install-client.sh              # نصب خودکار سرور ایران
│   ├── setup-dns.sh                   # راهنمای DNS setup
│   ├── resolver-scanner.sh            # اسکن و تست resolver ها
│   ├── resolver-healthcheck.sh        # healthcheck دوره‌ای
│   ├── multi-instance-manager.sh      # مدیریت چند instance
│   ├── benchmark.sh                   # بنچمارک جامع
│   ├── monitor.sh                     # مانیتورینگ real-time
│   └── troubleshoot.sh                # عیب‌یابی خودکار
├── docs/
│   ├── DNS-SETUP.md                   # راهنمای DNS
│   ├── RESOLVER-STRATEGY.md           # استراتژی resolver
│   ├── KERNEL-TUNING.md               # تنظیمات کرنل
│   ├── MULTI-INSTANCE.md              # راهنمای multi-instance
│   ├── TROUBLESHOOTING.md             # حل مشکلات
│   └── BENCHMARKING.md                # راهنمای بنچمارک
└── resolvers/
    ├── iran-resolvers.txt             # لیست resolver ایرانی
    ├── public-resolvers.txt           # لیست resolver عمومی
    └── active-resolvers.txt           # خروجی healthcheck (auto-generated)
```

---

## 🚀 راهنمای استقرار فاز‌بندی‌شده

### فاز ۱ — پایه (هدف: بنچمارک اولیه)

۱. **DNS Setup** — مطابق `docs/DNS-SETUP.md`
۲. **Build و نصب slipstream-rust** روی هر دو سرور
۳. **یک instance** با ۱۰۰ resolver
۴. **بنچمارک با iperf3** — ثبت throughput پایه

### فاز ۲ — بهینه‌سازی (هدف: ۳۰۰-۵۰۰ Mbps)

۱. **Authoritative mode** فعال
۲. **Kernel tuning** کامل
۳. **conntrack tuning**
۴. **افزایش resolver به ۵۰۰+**
۵. **Performance flags:** BBR، keep-alive، GSO
۶. **بنچمارک مجدد**

### فاز ۳ — Scale-up (هدف: ۷۰۰+ Mbps)

۱. **Multi-instance** (۲-۴ instance، هر کدوم subdomain جدا)
۲. **Resolver تقسیم‌بندی** (هر instance ۲۵۰ resolver)
۳. **Bonding/load-balance** در لایه بالاتر
۴. **۱۰۰۰+ resolver فعال**
۵. **بنچمارک و fine-tune**

### فاز ۴ — مقایسه (اختیاری)

۱. **تست slipstream-rust-plus** (Fox-Fig fork)
۲. **مقایسه head-to-head** با اصلی
۳. **انتخاب بهترین** بر اساس داده واقعی

---

## 🔧 نصب سریع — سرور خارج

```bash
# ۱. Dependencies
sudo apt update && sudo apt install -y \
  build-essential cmake pkg-config libssl-dev git curl iperf3

# ۲. Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source $HOME/.cargo/env

# ۳. Clone و Build
cd ~
git clone https://github.com/Mygod/slipstream-rust.git
cd slipstream-rust
git submodule update --init --recursive
cargo build --release -p slipstream-client -p slipstream-server

# ۴. نصب باینری
sudo cp target/release/slipstream-{client,server} /usr/local/bin/
sudo chmod +x /usr/local/bin/slipstream-*

# ۵. TLS Certificate
openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout ~/slipstream-key.pem -out ~/slipstream-cert.pem -days 3650 \
  -subj "/CN=tunnel.local"

# ۶. Stateless Reset Seed (مهم برای restart بدون قطعی)
dd if=/dev/urandom bs=32 count=1 > ~/slipstream-reset-seed

# ۷. Stop systemd-resolved (آزاد کردن port 53)
sudo systemctl stop systemd-resolved
sudo systemctl disable systemd-resolved
echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf

# ۸. Kernel Tuning
sudo cp configs/viaDrConnect.conf /etc/sysctl.d/
sudo sysctl -p /etc/sysctl.d/viaDrConnect.conf

# ۹. conntrack Tuning
sudo cp configs/conntrack-tuning.conf /etc/sysctl.d/
sudo sysctl -p /etc/sysctl.d/conntrack-tuning.conf
```

---

## 🔧 نصب سریع — سرور ایران

### آنلاین (اگه دسترسی به repo داره):
```bash
# مراحل ۱-۶ مثل سرور خارج
# Certificate رو از سرور خارج کپی کن (فقط cert.pem، نه key!)
```

### آفلاین:
```bash
# روی سرور خارج: bundle بساز
cd ~
mkdir -p slipstream-offline
cp slipstream-rust/target/release/slipstream-{client,server} slipstream-offline/
cp ~/slipstream-cert.pem slipstream-offline/
tar -czf slipstream-offline.tar.gz slipstream-offline/

# انتقال به سرور ایران (SCP/USB/FTP)
scp slipstream-offline.tar.gz root@IRAN_IP:/root/

# روی سرور ایران:
cd ~
tar -xzf slipstream-offline.tar.gz
sudo cp slipstream-offline/slipstream-{client,server} /usr/local/bin/
sudo chmod +x /usr/local/bin/slipstream-*
cp slipstream-offline/slipstream-cert.pem ~/
```

**نکته:** اگه باینری compiled روی سرور ایران segfault داد، باید روی خود سرور ایران compile کنی. راهنمای آفلاین Rust toolchain در `slipstream-dns-tunnel-guide.md` (مستند قبلی) معتبره.

---

## 🌐 راه‌اندازی — Instance تکی (فاز ۱)

### سرور خارج:
```bash
sudo slipstream-server \
  --dns-listen-port 53 \
  --target-address 127.0.0.1:8080 \
  --domain t.irihost.com \
  --cert ~/slipstream-cert.pem \
  --key ~/slipstream-key.pem \
  --reset-seed ~/slipstream-reset-seed \
  --max-connections 512 \
  --idle-timeout-seconds 1800
```

### سرور ایران:
```bash
slipstream-client \
  --tcp-listen-port 7000 \
  --domain t.irihost.com \
  --cert ~/slipstream-cert.pem \
  --resolver 2.189.1.2:53 \
  --resolver 2.188.21.50:53 \
  --resolver 151.246.41.30:53 \
  --congestion-control bbr \
  --keep-alive-interval 300
```

### تست فوری:
```bash
# سرور خارج — iperf3 server
iperf3 -s -p 8080

# سرور ایران — iperf3 client از طریق tunnel
iperf3 -c 127.0.0.1 -p 7000 -t 30 -P 4
```

---

## 🌐 راه‌اندازی — Authoritative Mode (فاز ۲)

Authoritative mode از recursive resolver دور میزنه و مستقیم query رو به سرور خارج میفرسته. حدود **۲ برابر** سریع‌تره.

### سرور ایران (تغییر فلگ):
```bash
slipstream-client \
  --tcp-listen-port 7000 \
  --domain t.irihost.com \
  --cert ~/slipstream-cert.pem \
  --authoritative 2.189.1.2:53 \
  --authoritative 2.188.21.50:53 \
  --authoritative 151.246.41.30:53 \
  --congestion-control bbr \
  --keep-alive-interval 200
```

**تفاوت:** `--authoritative` به جای `--resolver`. کلاینت مستقیماً از resolver ایرانی به عنوان forwarder استفاده میکنه بدون recursive lookup اضافی.

**نکته:** همه resolver ها authoritative mode رو ساپورت نمیکنن. تست کن — اگه بعضی کار نکردن، اونا رو با `--resolver` عادی استفاده کن.

---

## 🌐 راه‌اندازی — Multi-Instance (فاز ۳)

### DNS Setup (چند subdomain):
```
A Record:  ns1  → IP سرور خارج
NS Record: t1   → ns1.irihost.com
NS Record: t2   → ns1.irihost.com
NS Record: t3   → ns1.irihost.com
NS Record: t4   → ns1.irihost.com
```

### سرور خارج — ۴ instance:
```bash
# Instance 1 — port 53
sudo slipstream-server \
  --dns-listen-port 53 \
  --target-address 127.0.0.1:8081 \
  --domain t1.irihost.com \
  --cert ~/slipstream-cert.pem --key ~/slipstream-key.pem \
  --reset-seed ~/reset-seed-1

# Instance 2 — port 5353 (iptables redirect از 53)
sudo slipstream-server \
  --dns-listen-port 5353 \
  --target-address 127.0.0.1:8082 \
  --domain t2.irihost.com \
  --cert ~/slipstream-cert.pem --key ~/slipstream-key.pem \
  --reset-seed ~/reset-seed-2

# Instance 3, 4 — به همین ترتیب روی port 5354, 5355
```

**iptables redirect برای instance های اضافی:**
```bash
# همه instance ها باید از بیرون روی port 53 قابل دسترسی باشن
# از iptables mark + REDIRECT استفاده کن:
# Option A: هر instance IP متفاوت (اگه چند IP داری)
# Option B: همه روی 53 — بر اساس domain تفکیک میشه
#           (slipstream خودش بر اساس domain route میکنه)

# ساده‌ترین روش: همه instance ها روی port 53 ولی domain متفاوت
# slipstream-server خودش بر اساس domain فیلتر میکنه
# پس فقط چند process روی port های مختلف + redirect:
sudo iptables -t nat -A PREROUTING -p udp --dport 53 -m statistic \
  --mode nth --every 4 --packet 0 -j REDIRECT --to-ports 53
sudo iptables -t nat -A PREROUTING -p udp --dport 53 -m statistic \
  --mode nth --every 3 --packet 0 -j REDIRECT --to-ports 5353
sudo iptables -t nat -A PREROUTING -p udp --dport 53 -m statistic \
  --mode nth --every 2 --packet 0 -j REDIRECT --to-ports 5354
sudo iptables -t nat -A PREROUTING -p udp --dport 53 -j REDIRECT --to-ports 5355
```

**نکته مهم:** بهتره هر instance domain جداگانه داشته باشه و همه روی port 53 listen کنن — ولی چون Linux اجازه bind چند process به یک port نمیده، از iptables redirect استفاده کن. یا اگه سرور چند IP داره، هر instance رو روی یه IP bind کن.

### سرور ایران — ۴ instance + bonding:
```bash
# Instance 1 (resolver 1-250)
slipstream-client \
  --tcp-listen-port 7001 \
  --domain t1.irihost.com \
  --cert ~/slipstream-cert.pem \
  --authoritative $(head -250 /etc/slipstream/active-resolvers.txt | sed 's/$/:53/' | sed 's/^/--authoritative /' | tr '\n' ' ')
  --congestion-control bbr

# Instance 2 (resolver 251-500) — port 7002, domain t2
# Instance 3 (resolver 501-750) — port 7003, domain t3
# Instance 4 (resolver 751-1000) — port 7004, domain t4
```

### Bonding با Backhaul:
```toml
# backhaul-client.toml — سرور ایران
[client]
remote_addr = "127.0.0.1:7001"  # instance 1
transport = "tcp"
token = "SECRET"

# اضافه کردن instance های دیگه:
# Backhaul رو چندبار اجرا کن هر کدوم به یه port
# یا از HAProxy/nginx stream برای load-balance استفاده کن
```

**ساده‌تر — HAProxy TCP load-balance:**
```
# /etc/haproxy/haproxy.cfg
frontend tunnel_in
    bind *:6000
    mode tcp
    default_backend tunnel_instances

backend tunnel_instances
    mode tcp
    balance roundrobin
    server inst1 127.0.0.1:7001 check
    server inst2 127.0.0.1:7002 check
    server inst3 127.0.0.1:7003 check
    server inst4 127.0.0.1:7004 check
```

حالا port 6000 خروجی aggregated همه instance هاست.

---

## 📊 Performance Flags — مرجع سریع

### Client Flags:
| Flag | مقدار پیشنهادی | توضیح |
|------|----------------|-------|
| `--congestion-control` | `bbr` | بهتر از default برای high-latency |
| `--keep-alive-interval` | `200-300` | (ms) کمتر = responsive‌تر، بیشتر overhead |
| `--authoritative` | IP:53 | ۲x سریع‌تر از `--resolver` |
| `--resolver` | IP:53 | fallback اگه authoritative کار نکنه |

### Server Flags:
| Flag | مقدار پیشنهادی | توضیح |
|------|----------------|-------|
| `--max-connections` | `512` | بالاتر = memory بیشتر |
| `--idle-timeout-seconds` | `1800` | ۳۰ دقیقه |
| `--reset-seed` | فایل 32 بایتی | مهم برای restart بدون قطعی |

---

## ⚙️ Kernel Tuning — خلاصه

فایل کامل: `configs/viaDrConnect.conf`

```bash
# UDP Buffers — حیاتی برای throughput بالا
net.core.rmem_max = 67108864
net.core.wmem_max = 67108864
net.core.rmem_default = 16777216
net.core.wmem_default = 16777216

# TCP Tuning (برای لایه بالاتر)
net.ipv4.tcp_congestion_control = bbr
net.core.default_qdisc = cake

# Conntrack — حیاتی برای سرور خارج
net.netfilter.nf_conntrack_max = 524288
net.netfilter.nf_conntrack_udp_timeout = 15
net.netfilter.nf_conntrack_udp_timeout_stream = 60

# Network Stack
net.core.netdev_max_backlog = 50000
net.core.somaxconn = 65535
net.ipv4.ip_forward = 1
net.ipv4.udp_mem = 8388608 12582912 16777216

# File Descriptors
fs.file-max = 2097152
```

**اعمال:**
```bash
sudo sysctl -p /etc/sysctl.d/viaDrConnect.conf
ulimit -n 1048576  # یا در /etc/security/limits.conf
```

جزئیات کامل: `docs/KERNEL-TUNING.md`

---

## 🔍 استراتژی Resolver

### اسکن اولیه
```bash
# از لیست ۱۰۰۰ IP ایرانی، فیلتر کن کدوما پورت ۵۳ جواب میدن
./scripts/resolver-scanner.sh /path/to/iran-ips.txt

# خروجی: resolvers/active-resolvers.txt
# فرمت: IP LATENCY_MS SUPPORTS_EDNS MAX_RESPONSE_SIZE
```

### معیارهای یک resolver خوب:
- **Latency:** زیر ۵۰۰ms
- **EDNS0 Support:** response بزرگ‌تر از ۵۱۲ بایت
- **Rate-limit:** حداقل ۱۰۰ QPS بدون throttle
- **Uptime:** جواب‌دهی پایدار در ۲۴ ساعت
- **Forward:** باید query رو به NS record ما forward کنه

### Healthcheck خودکار
```bash
# هر ۱۵ دقیقه
*/15 * * * * /root/dns-tunnel-megaprompt-v2/scripts/resolver-healthcheck.sh

# resolver های مرده رو حذف و جدیدها رو اضافه میکنه
# خروجی: resolvers/active-resolvers.txt (به‌روز)
```

جزئیات کامل: `docs/RESOLVER-STRATEGY.md`

---

## 📊 بنچمارک مورد انتظار

| فاز | Resolver تعداد | حالت | Throughput تخمینی |
|-----|---------------|------|------------------|
| ۱ | ۱۰۰ | recursive | ۵۰-۱۰۰ Mbps |
| ۲ | ۵۰۰ | authoritative | ۳۰۰-۵۰۰ Mbps |
| ۳ | ۱۰۰۰ (multi-instance) | authoritative | ۷۰۰-۱۰۰۰ Mbps |

**فاکتورهای محدودکننده:**
- کیفیت و تعداد resolver
- Latency شبکه ایران
- Rate-limit هر resolver
- EDNS0 max response size
- CPU overhead (picoquic encryption)

---

## 🆘 عیب‌یابی سریع

```bash
# اسکریپت خودکار
./scripts/troubleshoot.sh

# بررسی‌های دستی
systemctl status slipstream-*          # سرویس‌ها running هستن؟
dig @8.8.8.8 t.irihost.com NS          # DNS propagate شده؟
ss -ulpn | grep :53                    # port 53 باز هست؟
conntrack -C                           # conntrack پر نشده؟
journalctl -u slipstream-server -f     # لاگ real-time
```

جزئیات کامل: `docs/TROUBLESHOOTING.md`

---

## 🔄 مقایسه slipstream-rust vs slipstream-rust-plus

| ویژگی | اصلی (Mygod) | Plus (Fox-Fig) |
|--------|-------------|----------------|
| پایداری | بالا (اصلی) | جدید، کمتر تست‌شده |
| سازگاری | استاندارد | فقط با Plus سازگاره |
| ادعای سرعت | ~24 MB/s (auth, loopback) | ~512 MB/s (ادعایی) |
| Turbo Mode | ندارد | دارد |
| Adaptive MTU | ندارد | دارد |
| SIP003 | دارد | دارد |
| Android | plugin رسمی | client اختصاصی |
| توصیه | فاز ۱-۳ | فاز ۴ (تست و مقایسه) |

---

## 📞 اطلاعات

- **Domain:** irihost.com
- **Tunnel Subdomains:** t1-t4.irihost.com
- **Telegram:** @drconnect
- **Channels:** @drconnect, @viaDrConnect, @lvlRF

---

## ✅ Checklist استقرار

### فاز ۱
- [ ] DNS تنظیم شد (A + NS record)
- [ ] slipstream-rust روی سرور خارج build/نصب شد
- [ ] slipstream-rust روی سرور ایران build/نصب شد
- [ ] TLS certificate ساخته و کپی شد
- [ ] Reset seed ساخته شد
- [ ] systemd-resolved غیرفعال شد (سرور خارج)
- [ ] تک instance تست شد
- [ ] بنچمارک اولیه با iperf3 ثبت شد

### فاز ۲
- [ ] Authoritative mode تست شد
- [ ] Kernel tuning اعمال شد
- [ ] conntrack tuning اعمال شد
- [ ] ۵۰۰+ resolver فعال
- [ ] BBR congestion control فعال
- [ ] بنچمارک فاز ۲ ثبت شد

### فاز ۳
- [ ] DNS برای multi-subdomain تنظیم شد
- [ ] چند instance راه‌اندازی شد
- [ ] Resolver ها بین instance ها تقسیم شد
- [ ] HAProxy/bonding تنظیم شد
- [ ] ۱۰۰۰+ resolver فعال
- [ ] بنچمارک فاز ۳ ثبت شد

### فاز ۴ (اختیاری)
- [ ] slipstream-rust-plus build شد
- [ ] مقایسه head-to-head انجام شد
- [ ] بهترین گزینه انتخاب شد

---

**نسخه:** 2.0
**تاریخ:** ۱۴۰۴/۱۲/۱۰ (مارس ۲۰۲۶)
**نویسنده:** DrConnect (@drconnect)
