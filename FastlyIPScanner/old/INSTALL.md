# Fastly CDN Scanner - API Server Installation Guide

**Developed by: DrConnect**  
**Telegram:** https://t.me/drconnect  
**Phone:** +98 912 741 9412

---

## Prerequisites

- Ubuntu 22.04 Server
- Root or sudo access
- Port 8080 available

---

## Installation Steps

### 1. Install System Dependencies

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv
```

### 2. Create Application Directory

```bash
sudo mkdir -p /opt/fastly-collector
sudo chown -R www-data:www-data /opt/fastly-collector
cd /opt/fastly-collector
```

### 3. Copy Files

Copy the following files to `/opt/fastly-collector/`:
- `api.py`
- `requirements.txt`

```bash
# Example (adjust paths):
sudo cp /path/to/api.py /opt/fastly-collector/
sudo cp /path/to/requirements.txt /opt/fastly-collector/
```

### 4. Create Virtual Environment & Install Dependencies

```bash
cd /opt/fastly-collector
sudo -u www-data python3 -m venv venv
sudo -u www-data venv/bin/pip install -r requirements.txt
```

### 5. Test API Manually (Optional)

```bash
# Test run
sudo -u www-data venv/bin/python3 api.py

# You should see:
# Starting server on 0.0.0.0:80...

# Press Ctrl+C to stop
```

### 6. Install Systemd Service

```bash
# Copy service file
sudo cp /path/to/fastly-collector.service /etc/systemd/system/

# Edit service file to use venv
sudo nano /etc/systemd/system/fastly-collector.service
```

**Update the ExecStart line:**
```ini
ExecStart=/opt/fastly-collector/venv/bin/gunicorn --workers 4 --bind 0.0.0.0:8080 --timeout 120 api:app
```

### 7. Enable and Start Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable fastly-collector

# Start service
sudo systemctl start fastly-collector

# Check status
sudo systemctl status fastly-collector
```

### 8. Verify Installation

```bash
# Check if service is running
curl http://localhost:8080/health

# Should return:
# {"status":"healthy","timestamp":"..."}

# Get your IP
curl http://localhost:8080/myip

# Get timestamp
curl http://localhost:8080/timestamp

# Access dashboard (if dashboard.html exists in /opt/fastly-collector/)
# Open in browser: http://2.189.161.91:8080/
```

**Note:** The API server now serves the dashboard directly. No need for nginx unless you want to use port 80.

---

## Directory Structure

After installation, you should have:

```
/opt/fastly-collector/
├── api.py                    # Main API application
├── requirements.txt          # Python dependencies
├── venv/                     # Virtual environment
├── submissions/              # Submitted scan results (auto-created)
├── aggregated/               # Aggregated results (auto-created)
└── stats.json                # Statistics (auto-created)
```

---

## Service Management

### Start Service
```bash
sudo systemctl start fastly-collector
```

### Stop Service
```bash
sudo systemctl stop fastly-collector
```

### Restart Service
```bash
sudo systemctl restart fastly-collector
```

### Check Status
```bash
sudo systemctl status fastly-collector
```

### View Logs
```bash
# Real-time logs
sudo journalctl -u fastly-collector -f

# Last 100 lines
sudo journalctl -u fastly-collector -n 100

# Logs from today
sudo journalctl -u fastly-collector --since today
```

---

## Firewall Configuration

If you have UFW firewall enabled:

```bash
# Allow port 8080
sudo ufw allow 8080/tcp

# Reload firewall
sudo ufw reload

# Check status
sudo ufw status
```

---

## Testing API Endpoints

### 1. Health Check
```bash
curl http://2.189.161.91:8080/health
```

### 2. Get Timestamp
```bash
curl http://2.189.161.91:8080/timestamp
```

### 3. Get Public IP
```bash
curl http://2.189.161.91:8080/myip
```

### 4. Get Stats
```bash
curl http://2.189.161.91:8080/stats
```

### 5. Submit Results (with authentication)

**Step 1: Get timestamp**
```bash
TIMESTAMP=$(curl -s http://2.189.161.91:8080/timestamp | jq -r '.timestamp')
echo $TIMESTAMP
```

**Step 2: Generate token (requires knowing SECRET_KEY)**
```python
import hashlib
timestamp = "1705123456"  # From step 1
secret_key = "DrConnect_Fastly_2025_Secure_Key_X793"
token = hashlib.sha256(f"{timestamp}{secret_key}".encode()).hexdigest()
print(token)
```

**Step 3: Submit**
```bash
curl -X POST http://2.189.161.91:8080/submit \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": 1705123456,
    "token": "your_generated_token",
    "public_ip": "1.2.3.4",
    "scan_duration": 123.45,
    "total_successful": 10,
    "results": [
      {"ip": "151.101.1.1", "port": 443, "success": true}
    ]
  }'
```

---

## Monitoring

### Check Submissions
```bash
ls -lh /opt/fastly-collector/submissions/
```

### View Latest Submission
```bash
ls -t /opt/fastly-collector/submissions/ | head -1 | xargs -I {} cat /opt/fastly-collector/submissions/{}
```

### View Stats
```bash
cat /opt/fastly-collector/stats.json
```

### Monitor Service Resource Usage
```bash
sudo systemctl status fastly-collector
```

---

## Backup

### Manual Backup
```bash
# Create backup directory
sudo mkdir -p /backup/fastly-collector

# Backup submissions
sudo tar -czf /backup/fastly-collector/submissions_$(date +%Y%m%d).tar.gz \
  /opt/fastly-collector/submissions/

# Backup stats
sudo cp /opt/fastly-collector/stats.json \
  /backup/fastly-collector/stats_$(date +%Y%m%d).json
```

### Automated Daily Backup (Optional)

Create cron job:
```bash
sudo crontab -e
```

Add:
```cron
0 2 * * * tar -czf /backup/fastly-collector/submissions_$(date +\%Y\%m\%d).tar.gz /opt/fastly-collector/submissions/
```

---

## Troubleshooting

### Service Won't Start

**Check logs:**
```bash
sudo journalctl -u fastly-collector -n 50
```

**Common issues:**
1. Port 8080 already in use
   ```bash
   sudo lsof -i :8080
   ```

2. Permission issues
   ```bash
   sudo chown -R www-data:www-data /opt/fastly-collector
   ```

3. Missing dependencies
   ```bash
   cd /opt/fastly-collector
   sudo -u www-data venv/bin/pip install -r requirements.txt
   ```

### High Memory Usage

Reduce number of workers in service file:
```ini
ExecStart=/opt/fastly-collector/venv/bin/gunicorn --workers 2 ...
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl restart fastly-collector
```

### Disk Space

**Check disk usage:**
```bash
df -h
du -sh /opt/fastly-collector/submissions/
```

**Clean old submissions:**
```bash
# Delete submissions older than 30 days
find /opt/fastly-collector/submissions/ -type f -mtime +30 -delete
```

---

## Security Notes

1. **SECRET_KEY:** The SECRET_KEY is embedded in `api.py`. Keep this file secure.

2. **Firewall:** Only open port 80. Do not expose other services.

3. **Rate Limiting:** The API has built-in rate limiting (10 submissions per hour per IP).

4. **File Permissions:** Ensure only www-data can write to submissions directory.

5. **Regular Updates:**
   ```bash
   sudo apt update && sudo apt upgrade
   ```

---

## Uninstallation

```bash
# Stop and disable service
sudo systemctl stop fastly-collector
sudo systemctl disable fastly-collector

# Remove service file
sudo rm /etc/systemd/system/fastly-collector.service
sudo systemctl daemon-reload

# Remove application (CAUTION: This deletes all data)
sudo rm -rf /opt/fastly-collector
```

---

## Support

For questions or issues:
- **Telegram:** https://t.me/drconnect
- **Phone:** +98 912 741 9412

---

## Notes

- Default SECRET_KEY: `DrConnect_Fastly_2025_Secure_Key_X793`
- This key is obfuscated in the code but viewable in source
- For production, consider regenerating with a unique random key
- Statistics are auto-updated with each submission
- Submissions are stored indefinitely (implement cleanup as needed)
