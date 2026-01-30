# 📋 مستند نصب و راه‌اندازی Slipstream DNS Tunnel

## 🎯 هدف
ایجاد تانل DNS بین سرور ایران (بدون دسترسی مستقیم به اینترنت) و سرور خارج از طریق DNS resolver مشترک.

---

## 📦 پیش‌نیازها

**سرور خارج:**
- Ubuntu 22.04
- دسترسی به اینترنت
- IP مثال: `51.89.168.87`

**سرور ایران:**
- Ubuntu 22.04  
- بدون دسترسی مستقیم به اینترنت
- دسترسی به DNS resolver مثال: `2.189.1.2:53`

**DNS:**
- دامنه: `a.pars-media.com`
- A Record → `51.89.168.87`

---

## 🔧 مرحله 1: نصب روی سرور خارج
```bash
# 1.1 - نصب dependencies
sudo apt update && sudo apt upgrade -y
sudo apt install -y build-essential cmake pkg-config libssl-dev python3 git curl

# 1.2 - نصب Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source $HOME/.cargo/env

# 1.3 - Clone و Build
cd ~
git clone https://github.com/Mygod/slipstream-rust.git
cd slipstream-rust
git submodule update --init --recursive
cargo build --release -p slipstream-client -p slipstream-server

# 1.4 - نصب باینری‌ها
sudo cp target/release/slipstream-{client,server} /usr/local/bin/
sudo chmod +x /usr/local/bin/slipstream-*

# 1.5 - ساخت TLS Certificate
cd ~
openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout slipstream-key.pem -out slipstream-cert.pem -days 3650 \
  -subj "/CN=tunnel.local"
```

---

## 📦 مرحله 2: آماده‌سازی Bundle آفلاین
```bash
cd ~
mkdir -p slipstream-offline/rust-toolchain
cd slipstream-offline

# 2.1 - دانلود Rust toolchain آفلاین
cd rust-toolchain
curl -O https://static.rust-lang.org/rustup/dist/x86_64-unknown-linux-gnu/rustup-init
curl -O https://static.rust-lang.org/dist/rust-1.93.0-x86_64-unknown-linux-gnu.tar.gz
curl -O https://static.rust-lang.org/dist/cargo-1.93.0-x86_64-unknown-linux-gnu.tar.gz
curl -O https://static.rust-lang.org/dist/rust-std-1.93.0-x86_64-unknown-linux-gnu.tar.gz
chmod +x rustup-init

# 2.2 - دانلود Backhaul (اختیاری)
cd ~/slipstream-offline
wget https://github.com/Musixal/Backhaul/releases/latest/download/backhaul_linux_amd64.tar.gz
tar -xzf backhaul_linux_amd64.tar.gz

# 2.3 - کپی باینری‌های compiled
cp ~/slipstream-rust/target/release/slipstream-client .
cp ~/slipstream-rust/target/release/slipstream-server .

# 2.4 - کپی source code (برای compile روی ایران)
cp -r ~/slipstream-rust/vendor .
cp ~/slipstream-rust/Cargo.{toml,lock} .
cp -r ~/slipstream-rust/crates .

# 2.5 - فشرده‌سازی
cd ~
tar -czf slipstream-offline.tar.gz slipstream-offline/
ls -lh slipstream-offline.tar.gz
```

**حجم تقریبی:** ~430MB

---

## 📤 مرحله 3: انتقال به سرور ایران
```bash
# از طریق scp یا FTP یا کپی دستی
scp slipstream-offline.tar.gz root@IRAN_IP:/root/
```

---

## 🔧 مرحله 4: نصب روی سرور ایران
```bash
# 4.1 - Extract
cd ~
tar -xzf slipstream-offline.tar.gz
cd slipstream-offline

# 4.2 - تنظیم Ubuntu repositories (میرور ایران)
sudo cp /etc/apt/sources.list /etc/apt/sources.list.backup
cat | sudo tee /etc/apt/sources.list << 'EOF'
deb http://ir.ubuntu.sindad.cloud/ubuntu/ jammy main restricted universe multiverse
deb http://ir.ubuntu.sindad.cloud/ubuntu/ jammy-updates main restricted universe multiverse
deb http://ir.ubuntu.sindad.cloud/ubuntu/ jammy-security main restricted universe multiverse
EOF

# 4.3 - نصب dependencies
sudo apt update
sudo apt install -y build-essential cmake pkg-config libssl-dev git

# 4.4 - نصب Rust
cd ~/slipstream-offline/rust-toolchain
./rustup-init -y --default-toolchain none

tar -xzf rust-1.93.0-x86_64-unknown-linux-gnu.tar.gz
cd rust-1.93.0-x86_64-unknown-linux-gnu
./install.sh --prefix=$HOME/.cargo
cd ..

tar -xzf cargo-1.93.0-x86_64-unknown-linux-gnu.tar.gz
cd cargo-1.93.0-x86_64-unknown-linux-gnu
./install.sh --prefix=$HOME/.cargo
cd ..

tar -xzf rust-std-1.93.0-x86_64-unknown-linux-gnu.tar.gz
cd rust-std-1.93.0-x86_64-unknown-linux-gnu
./install.sh --prefix=$HOME/.cargo
cd ../..

source $HOME/.cargo/env

# 4.5 - Build slipstream
cd ~/slipstream-offline
cargo build --release -p slipstream-client -p slipstream-server

# 4.6 - نصب باینری‌ها
sudo cp target/release/slipstream-{client,server} /usr/local/bin/
sudo chmod +x /usr/local/bin/slipstream-*

# 4.7 - کپی Certificate از سرور خارج
# محتوای slipstream-cert.pem از سرور خارج رو اینجا بچسبون
cat > ~/slipstream-cert.pem << 'EOF'
-----BEGIN CERTIFICATE-----
[PASTE YOUR CERTIFICATE HERE]
-----END CERTIFICATE-----
EOF
```

---

## 🌐 مرحله 5: تنظیم DNS

**روی Panel DNS (مثلا Cloudflare):**
```
Type: A
Name: a
Content: 51.89.168.87
Proxy: DNS only (خاکستری - نه نارنجی)
TTL: Auto
```

**تست DNS resolution:**
```bash
# روی سرور خارج
dig @8.8.8.8 a.pars-media.com

# روی سرور ایران - تست با DNS resolver مشترک
dig @2.189.1.2 a.pars-media.com
```

**DNS resolvers رایج در ایران:**
- `2.189.1.2:53` (شبکه ملی ایران)
- `2.188.21.50:53`
- `151.246.41.30:53`

---

## 🚀 مرحله 6: راه‌اندازی تانل

### سرور خارج:
```bash
# Stop systemd-resolved (چون پورت 53 میخواهیم)
sudo systemctl stop systemd-resolved

# اجرای slipstream-server
sudo slipstream-server \
  --dns-listen-port 53 \
  --target-address 127.0.0.1:8080 \
  --domain a.pars-media.com \
  --cert ~/slipstream-cert.pem \
  --key ~/slipstream-key.pem
```

**خروجی موفق:**
```
WARN Reset seed not configured; stateless resets will not survive server restarts
```

### سرور ایران:
```bash
# اجرای slipstream-client
slipstream-client \
  --tcp-listen-port 7000 \
  --resolver 2.189.1.2:53 \
  --domain a.pars-media.com \
  --cert ~/slipstream-cert.pem
```

**خروجی موفق:**
```
INFO Listening on TCP port 7000 (host ::)
```

---

## ✅ مرحله 7: تست تانل با iperf3

**روی سرور خارج (پنجره جدید):**
```bash
sudo apt install -y iperf3
iperf3 -s -p 8080
```

**روی سرور ایران (پنجره جدید):**
```bash
# نصب iperf3 اگه نیست
sudo apt install -y iperf3

# تست throughput
iperf3 -c 127.0.0.1 -p 7000 -t 10
```

**خروجی موفق:** باید throughput نشون بده (مثال: 10-100 Mbps بسته به شرایط شبکه)

---

## 🔄 مرحله 8: استفاده با Backhaul (اختیاری)

### کانفیگ Server (سرور خارج):
```toml
# /root/backhaul-server.toml
[server]
bind_addr = "0.0.0.0:8080"
transport = "tcp"
token = "YOUR_SECRET_TOKEN_HERE"

[[tunnels]]
name = "iran-to-foreign"
local_addr = "127.0.0.1:5201"  # iperf3 یا xray
```
```bash
# اجرا
backhaul -c /root/backhaul-server.toml
```

### کانفیگ Client (سرور ایران):
```toml
# /root/backhaul-client.toml
[client]
remote_addr = "127.0.0.1:7000"  # slipstream local port
transport = "tcp"
token = "YOUR_SECRET_TOKEN_HERE"

[[tunnels]]
name = "iran-to-foreign"
local_addr = "0.0.0.0:5201"  # listen locally
```
```bash
# اجرا
backhaul -c /root/backhaul-client.toml
```

---

## 📊 بنچمارک عملکرد

بر اساس مستندات پروژه slipstream-rust:

| Scenario | Throughput (Mbps) |
|----------|-------------------|
| Local loopback (بدون شبکه) | ~500-1000 |
| Over real DNS (با latency) | ~50-200 |
| با authoritative mode | بهتر از حالت عادی |

**فاکتورهای تاثیرگذار:**
- Latency به DNS resolver
- Packet loss شبکه
- CPU سرورها
- تنظیمات `--keep-alive-interval`

---

## 📝 نکات مهم

### امنیت:
1. **Certificate Pinning:** همیشه cert روی client هم باید باشه تا MITM جلوگیری بشه
2. **Domain matching:** باید روی server و client دقیقا یکسان باشه
3. **Firewall:** فقط پورت 53 UDP/TCP رو باز کن

### عملکرد:
1. **DNS Resolver:** باید از ایران و خارج accessible باشه و reliable باشه
2. **Port 53:** اگه systemd-resolved پورت 53 رو گرفته، باید stop بشه
3. **MTU:** در صورت مشکل packet loss، MTU رو کاهش بده

### Build:
1. **Static vs Dynamic:** Static build روی kernel/glibc های مختلف کار نمیکنه
2. **Dependencies:** هر سرور باید dependencies خودش رو داشته باشه
3. **Compile time:** اولین بار 5-10 دقیقه طول میکشه

---

## 🐛 عیب‌یابی رایج

### مشکل: `Connection refused` روی client

**علت:** DNS resolver query ها رو forward نمیکنه یا server down هست

**راه حل:**
```bash
# تست DNS resolution
dig @2.189.1.2 a.pars-media.com

# چک کردن server
sudo lsof -i :53  # روی سرور خارج
```

---

### مشکل: `Segmentation fault`

**علت:** Static build به درستی compile نشده

**راه حل:**
- باینری dynamic بگیر (بدون RUSTFLAGS)
- یا dependencies کامل نصب کن
```bash
# چک dependencies
ldd slipstream-client
```

---

### مشکل: `Cannot resolve hostname`

**علت:** Domain مچ نمیکنه یا DNS record غلطه

**راه حل:**
```bash
# تست از چند DNS resolver
dig @8.8.8.8 a.pars-media.com
dig @2.189.1.2 a.pars-media.com

# مطمئن شو domain روی server و client یکسانه
```

---

### مشکل: `Address already in use (port 53)`

**علت:** systemd-resolved یا DNS دیگه‌ای پورت 53 رو گرفته

**راه حل:**
```bash
# چک کردن
sudo lsof -i :53

# Stop کردن systemd-resolved
sudo systemctl stop systemd-resolved

# یا استفاده از پورت دیگه (مثلا 8853)
```

---

### مشکل: Throughput خیلی پایینه

**راه حل:**
1. DNS resolver دیگه‌ای تست کن
2. `--authoritative true` رو امتحان کن
3. Latency به resolver رو چک کن: `ping 2.189.1.2`
4. MTU رو کاهش بده

---

## 🎯 Use Cases

### 1. VPN Tunneling
```
User → xray/v2ray → Backhaul → Slipstream (DNS) → Internet
```

### 2. SSH Tunneling
```bash
# روی سرور خارج
ssh -D 1080 -N -f user@localhost -p 8080
```

### 3. HTTP Proxy
```bash
# با squid یا 3proxy روی پورت 8080
```

---

## 📚 منابع

- **پروژه اصلی:** https://github.com/Mygod/slipstream-rust
- **Backhaul:** https://github.com/Musixal/Backhaul
- **DNS over QUIC:** RFC 9250
- **QUIC Protocol:** RFC 9000

---

## 🔧 پارامترهای پیشرفته

### Server Options:
```bash
slipstream-server \
  --dns-listen-host :: \              # Listen on all interfaces
  --dns-listen-port 53 \
  --target-address 127.0.0.1:8080 \
  --domain a.pars-media.com \
  --cert ./cert.pem \
  --key ./key.pem \
  --max-connections 256 \              # Default: 256
  --idle-timeout-seconds 1200 \        # Default: 1200 (20 min)
  --reset-seed /path/to/seed           # برای stateless resets
```

### Client Options:
```bash
slipstream-client \
  --tcp-listen-host :: \
  --tcp-listen-port 7000 \
  --resolver 2.189.1.2:53 \
  --domain a.pars-media.com \
  --cert ./cert.pem \
  --authoritative true \               # برای عملکرد بهتر
  --keep-alive-interval 400 \          # Default: 400ms
  --congestion-control bbr             # یا dcubic
```

---

## 🚀 مرحله بعدی

بعد از تست موفق با iperf3:

1. **نصب Backhaul** برای tunnel management بهتر
2. **نصب xray/v2ray** برای VPN
3. **تنظیم monitoring** با systemd service
4. **Auto-restart** در صورت قطع connection

---

## 📄 License

- **Slipstream:** Apache-2.0
- **این مستند:** MIT License

---

**تاریخ:** 26 ژانویه 2026  
**نسخه:** 1.0  
**نویسنده:** DrConnect (@drconnect)

---

## ✅ Checklist نصب

- [ ] نصب dependencies روی سرور خارج
- [ ] Build slipstream روی سرور خارج
- [ ] ساخت TLS certificate
- [ ] آماده‌سازی bundle آفلاین
- [ ] انتقال bundle به سرور ایران
- [ ] نصب dependencies روی سرور ایران
- [ ] Build slipstream روی سرور ایران
- [ ] تنظیم DNS record
- [ ] تست DNS resolution
- [ ] اجرای server روی سرور خارج
- [ ] اجرای client روی سرور ایران
- [ ] تست تانل با iperf3
- [ ] تنظیم Backhaul (اختیاری)
- [ ] تست نهایی با traffic واقعی
