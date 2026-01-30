# Fastly CDN IP Scanner

**Version:** 1.0  
**Developer:** DrConnect  
**Channel:** https://t.me/drconnect

---

## 📖 Overview

An open-source project to help Iranians access the internet by scanning and identifying working Fastly CDN IP addresses. The scanner is distributed to volunteers who run scans, and results are automatically collected and shared through a public dashboard.

### Key Features

✅ **Distributed Scanning** - Multiple users can run scans simultaneously  
✅ **Automatic Collection** - Results automatically sent to central server  
✅ **Public Dashboard** - Working IPs shared with everyone  
✅ **Smart Scanning** - Two-stage verification (TCP + HTTP)  
✅ **Resume Capability** - Continue interrupted scans  
✅ **Privacy Focused** - User IPs not shown publicly  

---

## 📦 Project Structure

```
fastly-cdn-scanner/
│
├── Client Side (Scanner)
│   ├── scanner.py              # Main scanner script
│   ├── scan.sh                 # Bash wrapper
│   └── (auto-generated)
│       └── results/            # Local scan results
│
└── Server Side (Collector + Dashboard)
    ├── API Server
    │   ├── api.py              # Flask API for collecting results
    │   ├── requirements.txt    # Python dependencies
    │   ├── fastly-collector.service  # Systemd service
    │   └── INSTALL.md          # Server installation guide
    │
    ├── Dashboard
    │   ├── dashboard.html      # Web dashboard
    │   ├── aggregator.py       # Result aggregation script
    │   ├── dashboard_update.sh # Auto-update script
    │   └── DASHBOARD_SETUP.md  # Dashboard setup guide
    │
    └── Data Directories (auto-created)
        ├── submissions/        # Collected scan results
        ├── aggregated/         # Aggregated statistics
        └── results/            # (For reference)
```

---

## 🚀 Quick Start

### For Scan Volunteers (Users)

1. **Download scanner files:**
   - `scanner.py`
   - `scan.sh`

2. **Install dependencies:**
   ```bash
   pip install requests tqdm
   ```

3. **Run the scanner:**
   ```bash
   # Linux/Mac
   chmod +x scan.sh
   ./scan.sh
   
   # Or directly with Python
   python3 scanner.py
   ```

4. **Select scan type:**
   - Quick Scan (TCP only) - Faster
   - Full Scan (TCP + HTTP) - More accurate

5. **Results:**
   - Saved locally in `results/` directory
   - Automatically sent to collection server
   - Viewable on public dashboard

### For Server Administrator (DrConnect)

#### Setup Collection Server

1. **Install API Server:**
   ```bash
   # Follow instructions in INSTALL.md
   sudo mkdir -p /opt/fastly-collector
   # Copy api.py, requirements.txt, service file
   # Install and start service
   ```

2. **Setup Dashboard:**
   ```bash
   # Copy dashboard.html to /opt/fastly-collector/
   # Copy aggregator.py and dashboard_update.sh
   # Run initial aggregation
   # Dashboard is served by Flask automatically
   ```

3. **Access:**
   - API: `http://2.189.161.91:8080`
   - Dashboard: `http://2.189.161.91:8080/`
   - Admin Dashboard: `http://2.189.161.91:8080/?key=DrConnect2025Admin`
   
   **Optional:** Setup nginx to serve dashboard on port 80

---

## 🔧 How It Works

### Scanning Process

1. **User starts scanner** → Expands IP ranges from Fastly
2. **Stage 1: TCP Test** → Quickly tests port connectivity
3. **Stage 2: HTTP Verify** → Confirms CDN is responding (Full Scan only)
4. **Results collected** → Working IPs saved with metadata

### Data Flow

```
[Scanner] → Get Timestamp → [API Server]
          ↓
[Scanner] → Generate Token (with SECRET_KEY)
          ↓
[Scanner] → Submit Results (with Token) → [API Server]
          ↓
[API Server] → Validate & Store → submissions/
          ↓
[Aggregator] → Process All Submissions → aggregated/
          ↓
[Dashboard] → Display to Public
```

### Security

- **Challenge-Response Authentication** - Prevents unauthorized submissions
- **Rate Limiting** - 10 submissions per hour per IP
- **Token Expiry** - 24-hour validity window
- **Obfuscated SECRET_KEY** - Hidden in code

---

## 📊 Dashboard Features

### Public View

- Total scans performed
- Working IP:port combinations
- Success rates and counts
- Filter by port
- Sort by various criteria
- Auto-refresh every 5 minutes

### Admin View (with key)

- All public features plus:
- Detailed submission history
- User public IPs (for analysis)
- Manual aggregation trigger
- Extended statistics

**Admin URL:** `http://2.189.161.91/?key=DrConnect2025Admin`

---

## 🛠️ Configuration

### Scanner Settings

Edit `scanner.py`:

```python
# Telemetry server
TELEMETRY_SERVER = "http://2.189.161.91:8080"

# Developer channel
DEVELOPER_CHANNEL = "https://t.me/drconnect"

# Fastly IP ranges (embedded)
FASTLY_IP_RANGES = [...]
```

### API Server Settings

Edit `api.py`:

```python
# Rate limiting
MAX_SUBMISSIONS_PER_HOUR = 10

# File size limit
MAX_SUBMISSION_SIZE = 5 * 1024 * 1024  # 5MB

# Token validity
TOKEN_VALIDITY = 86400  # 24 hours
```

### Dashboard Settings

Edit `dashboard.html`:

```javascript
// Admin key
const ADMIN_KEY = 'DrConnect2025Admin';

// Auto-refresh interval
setInterval(loadData, 5 * 60 * 1000);  // 5 minutes
```

---

## 📋 Requirements

### Client (Scanner)

- Python 3.7+
- `requests` library
- `tqdm` library
- Internet connection (for submitting results)

### Server (Collector + Dashboard)

- Ubuntu 22.04 (or similar Linux)
- Python 3.7+
- Flask
- Gunicorn
- Port 8080 available
- Nginx (optional - for serving dashboard on port 80)

---

## 🔒 Security & Privacy

### User Privacy

- ✅ Public IPs collected only for analysis
- ✅ Not displayed on public dashboard
- ✅ Only admin can view (for operator statistics)
- ✅ No personal information collected
- ✅ Open source - anyone can audit

### Data Collection Transparency

**What we collect:**
- Your public IP address
- Working Fastly IPs you found
- Ports that worked
- Scan timestamp and duration

**What we DON'T collect:**
- Personal information
- Browsing history
- System information
- Private network details

**Users are informed:**
- Welcome message explains data collection
- Purpose: Improve internet access for Iranians
- Results shared publicly in dashboard

---

## 🤝 Contributing

This is an open-source project. Ways to help:

1. **Run scans** - Help discover working IPs
2. **Share results** - Post working IPs in channel
3. **Report issues** - Found a bug? Let us know
4. **Suggest features** - Ideas welcome
5. **Improve code** - Submit improvements

Contact: https://t.me/drconnect

---

## 📞 Support

**Telegram Channel:** https://t.me/drconnect

**Common Issues:**

1. **"Missing packages" error**
   ```bash
   pip install requests tqdm
   ```

2. **"Failed to submit" warning**
   - Normal if server is temporarily offline
   - Results still saved locally
   - No problem!

3. **Scanner is slow**
   - Normal - scanning thousands of IPs
   - Use Quick Scan for faster results
   - Adjust thread count in Settings

---

## 📄 License

This project is open source and free to use for helping Iranians access the internet.

---

## 🙏 Acknowledgments

- Thanks to all volunteers running scans
- Fastly CDN for infrastructure
- Iranian internet freedom community

---

## 📝 Version History

### v1.0 (2025-01-12)
- Initial release
- Basic scanner with two-stage verification
- Telemetry collection with challenge-response
- Public dashboard with admin mode
- Smart scan mode (subnet prioritization)
- Resume capability
- Auto-update every 30 minutes

---

## 🎯 Roadmap

**Planned Features:**

- [ ] Telegram bot for notifications
- [ ] Mobile app version
- [ ] Automatic VPN configuration
- [ ] GeoIP operator detection
- [ ] Performance benchmarking
- [ ] Historical success rate tracking
- [ ] Export to various VPN formats

---

## ⚠️ Disclaimer

This tool is provided as-is for educational and humanitarian purposes. Use responsibly and in accordance with local laws.

---

**Made with ❤️ by DrConnect for Iranian internet freedom**

**Join us:** https://t.me/drconnect
