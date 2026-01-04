# Backhaul Port Mapping
Generated: 2026-01-03 13:37:04
Token: `07b0fa76cd754d700d3944d68f5ce833`

---

## Port Assignments

| Version | Iran → Kharej | Transport | Tunnel Port | Web Port | iperf3 Port | TUN Subnet |
|---------|---------------|-----------|-------------|----------|-------------|------------|
| STANDARD | tehran-main → germany-hetzner | tcp       |         100 |      800 |        5001 | -          |
| STANDARD | tehran-main → germany-hetzner | tcpmux    |         101 |      801 |        5002 | -          |
| STANDARD | tehran-main → germany-hetzner | ws        |         102 |      802 |        5003 | -          |
| PREMIUM  | tehran-main → germany-hetzner | udp       |         103 |      803 |        5004 | -          |
| PREMIUM  | tehran-main → germany-hetzner | wsmux     |         104 |      804 |        5005 | -          |
| PREMIUM  | tehran-main → germany-hetzner | utcpmux   |         105 |      805 |        5006 | -          |
| STANDARD | tehran-main → france-ovh | tcp       |         106 |      806 |        5007 | -          |
| PREMIUM  | tehran-main → france-ovh | tcpmux    |         107 |      807 |        5008 | -          |
| PREMIUM  | tehran-main → france-ovh | uwsmux    |         108 |      808 |        5009 | -          |
| STANDARD | shiraz-backup → germany-hetzner | ws        |         109 |      809 |        5010 | -          |
| STANDARD | shiraz-backup → germany-hetzner | wsmux     |         110 |      810 |        5011 | -          |
| PREMIUM  | shiraz-backup → germany-hetzner | tcp       |         111 |      811 |        5012 | -          |
| PREMIUM  | shiraz-backup → germany-hetzner | udp       |         112 |      812 |        5013 | -          |


---

## iperf3 Testing Guide

### On Kharej Servers:
Start iperf3 server on localhost:
```bash
iperf3 -s -B 127.0.0.1 -p 5201
```

### On Iran Servers:
Test each tunnel individually:
```bash
iperf3 -c 127.0.0.1 -p 5001 -t 10  # tcp to germany-hetzner
iperf3 -c 127.0.0.1 -p 5002 -t 10  # tcpmux to germany-hetzner
iperf3 -c 127.0.0.1 -p 5003 -t 10  # ws to germany-hetzner
iperf3 -c 127.0.0.1 -p 5004 -t 10  # udp to germany-hetzner
iperf3 -c 127.0.0.1 -p 5005 -t 10  # wsmux to germany-hetzner
iperf3 -c 127.0.0.1 -p 5006 -t 10  # utcpmux to germany-hetzner
iperf3 -c 127.0.0.1 -p 5007 -t 10  # tcp to france-ovh
iperf3 -c 127.0.0.1 -p 5008 -t 10  # tcpmux to france-ovh
iperf3 -c 127.0.0.1 -p 5009 -t 10  # uwsmux to france-ovh
iperf3 -c 127.0.0.1 -p 5010 -t 10  # ws to germany-hetzner
iperf3 -c 127.0.0.1 -p 5011 -t 10  # wsmux to germany-hetzner
iperf3 -c 127.0.0.1 -p 5012 -t 10  # tcp to germany-hetzner
iperf3 -c 127.0.0.1 -p 5013 -t 10  # udp to germany-hetzner
```

---

## Web Interface Access

Access the web sniffer interface at:

### Iran Servers:

**tehran-main** (`1.2.3.4`):
- tcp: http://1.2.3.4:800
- tcpmux: http://1.2.3.4:801
- ws: http://1.2.3.4:802
- udp: http://1.2.3.4:803
- wsmux: http://1.2.3.4:804
- utcpmux: http://1.2.3.4:805
- tcp: http://1.2.3.4:806
- tcpmux: http://1.2.3.4:807
- uwsmux: http://1.2.3.4:808

**shiraz-backup** (`5.6.7.8`):
- ws: http://5.6.7.8:809
- wsmux: http://5.6.7.8:810
- tcp: http://5.6.7.8:811
- udp: http://5.6.7.8:812

### Kharej Servers:

**germany-hetzner** (`20.30.40.50`):
- tcp: http://20.30.40.50:800
- tcpmux: http://20.30.40.50:801
- ws: http://20.30.40.50:802
- udp: http://20.30.40.50:803
- wsmux: http://20.30.40.50:804
- utcpmux: http://20.30.40.50:805
- ws: http://20.30.40.50:809
- wsmux: http://20.30.40.50:810
- tcp: http://20.30.40.50:811
- udp: http://20.30.40.50:812

**france-ovh** (`21.31.41.51`):
- tcp: http://21.31.41.51:806
- tcpmux: http://21.31.41.51:807
- uwsmux: http://21.31.41.51:808
