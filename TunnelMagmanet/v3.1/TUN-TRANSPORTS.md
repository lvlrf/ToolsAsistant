# راهنمای Transport های TUN و Subnet ها

## 🌐 Transport های TUN-based

در نسخه Premium، دو transport از TUN interface استفاده می‌کنند:

- **tcptun** - TCP Tunnel با TUN interface
- **faketcptun** - Fake TCP Tunnel

این transport ها نیاز به تنظیمات اضافی دارند.

---

## 📊 Subnet Management (مدیریت خودکار)

### چطور کار می‌کنه؟

هر transport از نوع TUN یک **subnet جداگانه** می‌گیره:

```
تانل 1 (tcptun)     → 10.10.10.0/24
تانل 2 (faketcptun) → 10.10.20.0/24
تانل 3 (tcptun)     → 10.10.30.0/24
تانل 4 (faketcptun) → 10.10.40.0/24
```

### ✅ تضمین عدم تداخل

- هر تانل TUN یک subnet یکتا دریافت می‌کند
- Server و Client از **همان subnet** استفاده می‌کنند
- هیچ تداخلی رخ نمی‌دهد

---

## ⚙️ تنظیمات TUN

### MTU (Maximum Transmission Unit)
```
پیش‌فرض: 1400 بایت
```

این مقدار برای جلوگیری از fragmentation بهینه شده است.

### نمونه کانفیگ Server (Iran):
```toml
[server]
bind_addr = "0.0.0.0:107"
transport = "tcptun"
token = "your_token"

tun_name = "backhaul107"
tun_subnet = "10.10.10.0/24"
mtu = 1400
```

### نمونه کانفیگ Client (Kharej):
```toml
[client]
remote_addr = "1.2.3.4:107"
transport = "tcptun"
token = "your_token"

tun_name = "backhaul107"
tun_subnet = "10.10.10.0/24"  ← همان subnet
mtu = 1400
```

---

## 🎯 استفاده از همه Transport های Premium

می‌توانید **همه** transport های premium را همزمان استفاده کنید:

```json
{
  "connections": [
    {
      "iran": "tehran",
      "kharej": "germany",
      "premium_transports": [
        "tcp",
        "tcpmux",
        "utcpmux",
        "udp",
        "ws",
        "wsmux",
        "uwsmux",
        "tcptun",      ← نیاز به TUN
        "faketcptun"   ← نیاز به TUN
      ]
    }
  ]
}
```

### نتیجه:
- 7 تانل عادی (بدون TUN)
- 2 تانل TUN با subnet های جداگانه

---

## 📋 بررسی Subnet ها

بعد از generate، در فایل `port-mapping.md` می‌توانید subnet ها را ببینید:

```markdown
| Version  | Iran → Kharej | Transport  | Tunnel Port | TUN Subnet     |
|----------|---------------|------------|-------------|----------------|
| PREMIUM  | iran → kharej | tcptun     | 107         | 10.10.10.0/24  |
| PREMIUM  | iran → kharej | faketcptun | 108         | 10.10.20.0/24  |
```

---

## 🔍 بررسی کانفیگ‌ها

### چک کردن MTU:
```bash
grep "mtu" output/premium/iran-servers/*/config-*-tcptun.toml
```

خروجی:
```
mtu = 1400
```

### چک کردن Subnet ها:
```bash
grep "tun_subnet" output/premium/iran-servers/*/config-*-*.toml
```

خروجی:
```
tun_subnet = "10.10.10.0/24"
tun_subnet = "10.10.20.0/24"
```

---

## ⚠️ نکات مهم

### ✅ درست:
- هر تانل TUN یک subnet یکتا دارد
- Server و Client همیشه همان subnet را دارند
- MTU برای همه تانل‌های TUN 1400 است

### ❌ اشتباه:
- دستی subnet ها را تغییر ندهید
- MTU server و client باید یکسان باشد
- از subnet های تکراری استفاده نکنید

---

## 🧪 تست

بعد از نصب، می‌توانید TUN interface را چک کنید:

```bash
# روی سرور
ip addr show backhaul107
ifconfig backhaul107
```

باید TUN interface با subnet مشخص شده را ببینید.

---

## 📚 لیست کامل Transport ها

### Standard:
- tcp, tcpmux, udp, ws, wsmux

### Premium (اضافه):
- **utcpmux** - UDP over TCP Multiplexing
- **uwsmux** - UDP over WebSocket Multiplexing
- **tcptun** - TCP Tunnel با TUN ⭐
- **faketcptun** - Fake TCP Tunnel ⭐

⭐ = نیاز به TUN interface و subnet جداگانه

---

**نتیجه:** همه چیز خودکار است! فقط transport ها را در config.json تعیین کنید، بقیه کارها انجام می‌شود.
