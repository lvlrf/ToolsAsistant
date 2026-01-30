# Fastly CDN Scanner - Dashboard Setup Guide

**Developed by: DrConnect**  
**Channel:** https://t.me/drconnect

---

## Overview

The dashboard provides a web interface to view aggregated scan results from all users. It has two modes:

1. **Public Mode**: Shows statistics and working IPs (without user information)
2. **Admin Mode**: Shows detailed statistics including user IPs

---

## Files Included

- `dashboard.html` - Main dashboard interface
- `aggregator.py` - Script to aggregate results from submissions
- `dashboard_update.sh` - Automated update script for cron

---

## Installation

### 1. Copy Dashboard Files

```bash
cd /opt/fastly-collector

# Copy dashboard files
sudo cp /path/to/dashboard.html /opt/fastly-collector/
sudo cp /path/to/aggregator.py /opt/fastly-collector/
sudo cp /path/to/dashboard_update.sh /opt/fastly-collector/

# Make scripts executable
sudo chmod +x aggregator.py dashboard_update.sh

# Set ownership
sudo chown -R www-data:www-data /opt/fastly-collector/
```

### 2. Run Initial Aggregation

```bash
cd /opt/fastly-collector
sudo -u www-data venv/bin/python3 aggregator.py
```

This creates:
- `aggregated/results.json` (public)
- `aggregated/admin_results.json` (admin)

### 3. Restart API Service

The API server (api.py) now serves the dashboard directly.

```bash
sudo systemctl restart fastly-collector
```

**Access the dashboard:**
```
http://2.189.161.91:8080/
```

### 4. (Optional) Setup nginx for Port 80

If you want the dashboard on port 80 instead of 8080, install nginx:

```bash
sudo apt install nginx
```

Create nginx configuration:

```bash
sudo nano /etc/nginx/sites-available/fastly-dashboard
```

Add this configuration:

```nginx
server {
    listen 80;
    server_name 2.189.161.91;  # Your server IP
    
    root /opt/fastly-collector;
    index dashboard.html;
    
    location / {
        try_files $uri $uri/ =404;
    }
    
    location /aggregated/ {
        alias /opt/fastly-collector/aggregated/;
        add_header Cache-Control "no-cache, must-revalidate";
    }
    
    # Proxy API requests to port 8080
    location /api/ {
        proxy_pass http://127.0.0.1:8080/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/fastly-dashboard /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 4. Setup Automatic Updates (Cron)

Edit crontab:

```bash
sudo crontab -e
```

Add this line to update every 30 minutes:

```cron
*/30 * * * * /opt/fastly-collector/dashboard_update.sh
```

Or update every hour:

```cron
0 * * * * /opt/fastly-collector/dashboard_update.sh
```

Save and exit.

Verify cron is scheduled:

```bash
sudo crontab -l
```

---

## Usage

### Direct Access (Without nginx)

```
http://2.189.161.91:8080/
```

### With nginx (Port 80)

```
http://2.189.161.91/
```

### Public View

Anyone can view:
- Total number of scans
- Total tests performed
- List of working IPs with success counts
- Filter by port
- Sort by different criteria

### Admin Access

**Without nginx:**
```
http://2.189.161.91:8080/?key=DrConnect2025Admin
```

**With nginx:**
```
http://2.189.161.91/?key=DrConnect2025Admin
```

Admin can additionally see:
- User public IPs who submitted scans
- Detailed statistics per submission
- Manual trigger for aggregation update

**Security Note:** Change the admin key in `dashboard.html` before deployment:

```javascript
const ADMIN_KEY = 'YourSecureKeyHere123';
```

---

## Manual Operations

### Run Aggregation Manually

```bash
cd /opt/fastly-collector
sudo -u www-data venv/bin/python3 aggregator.py
```

### View Aggregation Logs

```bash
tail -f /opt/fastly-collector/aggregator.log
```

### Check Cron Execution

```bash
sudo grep CRON /var/log/syslog | grep aggregat
```

---

## Customization

### Change Update Frequency

Edit cron schedule:
- Every 15 minutes: `*/15 * * * *`
- Every hour: `0 * * * *`
- Every 6 hours: `0 */6 * * *`

### Customize Dashboard Appearance

Edit `dashboard.html`:
- Colors: Modify CSS gradient values
- Layout: Adjust grid columns in `.stats-grid`
- Filters: Add more port options

### Add Custom Statistics

Edit `aggregator.py` to calculate additional metrics:

```python
# Example: Calculate average success rate
avg_success_rate = sum(r['success_rate'] for r in public_results) / len(public_results)

public_output['metadata']['avg_success_rate'] = round(avg_success_rate, 2)
```

---

## Troubleshooting

### Dashboard Shows "Failed to load data"

**Check if aggregation has run:**

```bash
ls -l /opt/fastly-collector/aggregated/
```

Should show `results.json` and `admin_results.json`.

**If missing, run:**

```bash
cd /opt/fastly-collector
sudo -u www-data venv/bin/python3 aggregator.py
```

### Nginx 403 Forbidden Error

**Check file permissions:**

```bash
sudo chown -R www-data:www-data /opt/fastly-collector/
sudo chmod -R 755 /opt/fastly-collector/
```

### Cron Not Running

**Check cron service:**

```bash
sudo systemctl status cron
```

**Check cron logs:**

```bash
sudo grep CRON /var/log/syslog | tail -20
```

**Verify script is executable:**

```bash
sudo chmod +x /opt/fastly-collector/dashboard_update.sh
```

### Admin Mode Not Working

**Verify admin key matches in URL and code:**

In `dashboard.html`:
```javascript
const ADMIN_KEY = 'DrConnect2025Admin';
```

URL:
```
http://2.189.161.91/?key=DrConnect2025Admin
```

---

## Performance Optimization

### For Large Number of Submissions

**1. Add pagination to dashboard:**

Edit `dashboard.html` to show results in pages (100 per page).

**2. Limit stored submissions:**

Create cleanup script to archive old submissions:

```bash
#!/bin/bash
# cleanup_old.sh

find /opt/fastly-collector/submissions -type f -mtime +30 -exec mv {} /opt/fastly-collector/archive/ \;
```

**3. Use database instead of JSON:**

For thousands of submissions, consider migrating to SQLite or PostgreSQL.

---

## Security Recommendations

1. **Change Admin Key:**
   ```javascript
   const ADMIN_KEY = 'YourUniqueSecureKey2025';
   ```

2. **Add HTTPS (recommended):**
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d yourdomain.com
   ```

3. **Restrict Admin Access by IP:**
   
   In nginx config:
   ```nginx
   location / {
       if ($arg_key = "DrConnect2025Admin") {
           # Allow only specific IP
           allow 1.2.3.4;
           deny all;
       }
   }
   ```

4. **Enable Rate Limiting:**
   
   In nginx config:
   ```nginx
   limit_req_zone $binary_remote_addr zone=dashboard:10m rate=10r/m;
   
   location / {
       limit_req zone=dashboard burst=5;
   }
   ```

---

## Monitoring

### Check Dashboard Access Logs

```bash
sudo tail -f /var/log/nginx/access.log | grep dashboard
```

### Monitor Aggregation Performance

```bash
# Add timing to aggregator.py
import time
start = time.time()
# ... aggregation code ...
print(f"Completed in {time.time() - start:.2f}s")
```

---

## Backup

### Backup Aggregated Data

```bash
# Create backup directory
sudo mkdir -p /backup/fastly-collector/aggregated

# Backup aggregated results
sudo cp /opt/fastly-collector/aggregated/*.json /backup/fastly-collector/aggregated/
```

### Automated Daily Backup

Add to crontab:

```cron
0 3 * * * cp /opt/fastly-collector/aggregated/*.json /backup/fastly-collector/aggregated/backup_$(date +\%Y\%m\%d).json
```

---

## API Integration

### Trigger Aggregation via API (Admin)

The dashboard includes a manual trigger button for admin users.

To implement server-side:

Edit `/etc/nginx/sites-available/fastly-dashboard`:

```nginx
location /api/aggregate {
    if ($request_method = POST) {
        # Execute aggregation script
        content_by_lua_block {
            os.execute("/opt/fastly-collector/dashboard_update.sh &")
        }
        return 200;
    }
    return 405;
}
```

Requires: `nginx-extras` or compile with Lua support.

**Simple alternative:** Create a web endpoint in Flask API.

---

## Exporting Data

### Export to CSV

Add this to `aggregator.py`:

```python
import csv

def export_to_csv(results):
    with open('aggregated/results.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['ip', 'port', 'success_count', 'success_rate'])
        writer.writeheader()
        writer.writerows(results)
```

### Download from Dashboard

Add download button in `dashboard.html`:

```html
<button onclick="downloadCSV()">📥 Download CSV</button>
```

```javascript
function downloadCSV() {
    // Convert results to CSV and trigger download
    let csv = 'IP,Port,Success Count,Success Rate\n';
    allResults.forEach(r => {
        csv += `${r.ip},${r.port},${r.success_count},${r.success_rate}\n`;
    });
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'fastly_results.csv';
    a.click();
}
```

---

## Support

For questions or issues:
- **Channel:** https://t.me/drconnect
- **Issues:** Check logs in `/var/log/nginx/` and `aggregator.log`

---

## Notes

- Dashboard auto-refreshes every 5 minutes
- Cron updates data every 30 minutes (configurable)
- Admin key should be kept secure
- For production use, enable HTTPS
- Consider adding authentication for sensitive deployments
