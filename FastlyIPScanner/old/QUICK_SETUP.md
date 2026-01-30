# Quick Setup Guide - Without nginx

**Fastly CDN Scanner - Minimal Setup**  
**Developer:** DrConnect  
**Channel:** https://t.me/drconnect

---

## For Quick Deployment (No nginx Required)

This guide helps you get everything running on port 8080 without nginx.

---

## Step 1: Install API Server

```bash
# 1. Create directory
sudo mkdir -p /opt/fastly-collector
cd /opt/fastly-collector

# 2. Copy files
sudo cp /path/to/api.py .
sudo cp /path/to/requirements.txt .
sudo cp /path/to/fastly-collector.service /etc/systemd/system/

# 3. Create virtual environment
sudo python3 -m venv venv
sudo venv/bin/pip install -r requirements.txt

# 4. Set permissions
sudo chown -R www-data:www-data /opt/fastly-collector

# 5. Start service
sudo systemctl daemon-reload
sudo systemctl enable fastly-collector
sudo systemctl start fastly-collector

# 6. Check status
sudo systemctl status fastly-collector
```

---

## Step 2: Setup Dashboard

```bash
cd /opt/fastly-collector

# 1. Copy dashboard files
sudo cp /path/to/dashboard.html .
sudo cp /path/to/aggregator.py .
sudo cp /path/to/dashboard_update.sh .

# 2. Make executable
sudo chmod +x aggregator.py dashboard_update.sh

# 3. Run initial aggregation
sudo -u www-data venv/bin/python3 aggregator.py

# 4. Setup auto-update (every 30 minutes)
sudo crontab -e
# Add: */30 * * * * /opt/fastly-collector/dashboard_update.sh
```

---

## Step 3: Open Firewall

```bash
# Allow port 8080
sudo ufw allow 8080/tcp
sudo ufw reload
sudo ufw status
```

---

## Step 4: Test Everything

```bash
# Test API
curl http://localhost:8080/health
curl http://localhost:8080/myip
curl http://localhost:8080/timestamp
curl http://localhost:8080/stats

# Test from outside
curl http://2.189.161.91:8080/health
```

**Open in browser:**
- Dashboard: `http://2.189.161.91:8080/`
- Admin: `http://2.189.161.91:8080/?key=DrConnect2025Admin`

---

## Complete File Structure

```
/opt/fastly-collector/
├── api.py                      # API server (serves dashboard too)
├── requirements.txt            # Python dependencies
├── dashboard.html              # Dashboard interface
├── aggregator.py               # Aggregation script
├── dashboard_update.sh         # Auto-update script
├── venv/                       # Virtual environment
├── submissions/                # Collected results (auto-created)
├── aggregated/                 # Aggregated data (auto-created)
│   ├── results.json           # Public results
│   └── admin_results.json     # Admin results
└── stats.json                  # Statistics (auto-created)
```

---

## URLs

**All on port 8080:**

| Endpoint | URL |
|----------|-----|
| API Info | http://2.189.161.91:8080/ |
| Dashboard | http://2.189.161.91:8080/ (if dashboard.html exists) |
| Admin Dashboard | http://2.189.161.91:8080/?key=DrConnect2025Admin |
| Health Check | http://2.189.161.91:8080/health |
| Get IP | http://2.189.161.91:8080/myip |
| Get Timestamp | http://2.189.161.91:8080/timestamp |
| Submit Results | http://2.189.161.91:8080/submit (POST) |
| Stats | http://2.189.161.91:8080/stats |

---

## Management Commands

### View Logs
```bash
# Service logs
sudo journalctl -u fastly-collector -f

# Aggregation logs
tail -f /opt/fastly-collector/aggregator.log
```

### Restart Service
```bash
sudo systemctl restart fastly-collector
```

### Manual Aggregation
```bash
cd /opt/fastly-collector
sudo -u www-data venv/bin/python3 aggregator.py
```

### View Submissions
```bash
ls -lh /opt/fastly-collector/submissions/
```

### View Latest Results
```bash
cat /opt/fastly-collector/aggregated/results.json | jq
```

---

## Troubleshooting

### Dashboard shows API info instead

**Problem:** Opening `http://2.189.161.91:8080/` shows API endpoints, not dashboard.

**Solution:** Make sure `dashboard.html` exists in `/opt/fastly-collector/`

```bash
ls -l /opt/fastly-collector/dashboard.html
```

If missing, copy it:
```bash
sudo cp /path/to/dashboard.html /opt/fastly-collector/
sudo systemctl restart fastly-collector
```

### "File not found" for aggregated files

**Problem:** Dashboard loads but shows "Failed to load data"

**Solution:** Run aggregation:

```bash
cd /opt/fastly-collector
sudo -u www-data venv/bin/python3 aggregator.py
```

Check files exist:
```bash
ls -l /opt/fastly-collector/aggregated/
```

### Service won't start

**Check logs:**
```bash
sudo journalctl -u fastly-collector -n 50
```

**Common fixes:**
```bash
# Port already in use
sudo lsof -i :8080

# Permission issues
sudo chown -R www-data:www-data /opt/fastly-collector

# Missing dependencies
cd /opt/fastly-collector
sudo venv/bin/pip install -r requirements.txt
```

---

## Optional: Add nginx Later

If you want to serve on port 80 later, follow `DASHBOARD_SETUP.md` section 4.

---

## Security Notes

1. **Change Admin Key** in `dashboard.html`:
   ```javascript
   const ADMIN_KEY = 'YourNewSecureKey';
   ```

2. **Enable HTTPS** (recommended for production):
   ```bash
   # Install certbot
   sudo apt install certbot
   
   # Get certificate (requires domain)
   sudo certbot certonly --standalone -d yourdomain.com
   
   # Configure gunicorn with SSL (advanced)
   ```

3. **Restrict Access** with firewall:
   ```bash
   # Allow only specific IP
   sudo ufw allow from YOUR_IP to any port 8080
   ```

---

## Monitoring

### Check Service Status
```bash
sudo systemctl status fastly-collector
```

### Monitor Resource Usage
```bash
# CPU and Memory
top -p $(pgrep -f gunicorn)

# Disk usage
df -h
du -sh /opt/fastly-collector/submissions/
```

### Clean Old Submissions
```bash
# Delete submissions older than 30 days
find /opt/fastly-collector/submissions -type f -mtime +30 -delete
```

---

## Backup

```bash
# Backup submissions
sudo tar -czf /backup/submissions_$(date +%Y%m%d).tar.gz \
  /opt/fastly-collector/submissions/

# Backup aggregated data
sudo cp /opt/fastly-collector/aggregated/*.json /backup/
```

---

## Support

**Issues or Questions:**  
Channel: https://t.me/drconnect

---

**That's it! Everything runs on port 8080. No nginx needed.**
