#!/bin/bash
# Fastly Scanner Dashboard - Troubleshooting Script
# Created by: DrConnect

echo "════════════════════════════════════════════════════════════"
echo "🔍 Fastly Scanner Dashboard - عیب‌یابی"
echo "════════════════════════════════════════════════════════════"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Set working directory
cd /opt/fastly-collector 2>/dev/null || cd .

echo "📁 مرحله 1: بررسی فایل‌ها"
echo "────────────────────────────────────────────────────────────"

# Check api.py
if [ -f "api.py" ]; then
    echo -e "${GREEN}✅${NC} api.py موجود است"
else
    echo -e "${RED}❌${NC} api.py موجود نیست!"
fi

# Check aggregator.py
if [ -f "aggregator.py" ]; then
    echo -e "${GREEN}✅${NC} aggregator.py موجود است"
else
    echo -e "${RED}❌${NC} aggregator.py موجود نیست!"
fi

# Check dashboard.html
if [ -f "dashboard.html" ]; then
    echo -e "${GREEN}✅${NC} dashboard.html موجود است"
else
    echo -e "${RED}❌${NC} dashboard.html موجود نیست!"
fi

echo ""
echo "📂 مرحله 2: بررسی دایرکتوری‌ها"
echo "────────────────────────────────────────────────────────────"

# Check submissions directory
if [ -d "submissions" ]; then
    file_count=$(find submissions -name "*.json" 2>/dev/null | wc -l)
    echo -e "${GREEN}✅${NC} submissions/ موجود است (${file_count} فایل)"
else
    echo -e "${YELLOW}⚠️${NC} submissions/ موجود نیست - ایجاد میشود"
    mkdir -p submissions
fi

# Check aggregated directory
if [ -d "aggregated" ]; then
    file_count=$(find aggregated -name "*.json" 2>/dev/null | wc -l)
    echo -e "${GREEN}✅${NC} aggregated/ موجود است (${file_count} فایل)"
else
    echo -e "${YELLOW}⚠️${NC} aggregated/ موجود نیست - ایجاد میشود"
    mkdir -p aggregated
fi

echo ""
echo "🔄 مرحله 3: اجرای Aggregator"
echo "────────────────────────────────────────────────────────────"

if [ -f "aggregator.py" ]; then
    echo "در حال اجرای aggregator.py..."
    python3 aggregator.py
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅${NC} Aggregator با موفقیت اجرا شد"
    else
        echo -e "${RED}❌${NC} Aggregator با خطا مواجه شد"
    fi
else
    echo -e "${RED}❌${NC} aggregator.py موجود نیست!"
fi

echo ""
echo "📊 مرحله 4: بررسی فایل‌های خروجی"
echo "────────────────────────────────────────────────────────────"

# Check results.json
if [ -f "aggregated/results.json" ]; then
    size=$(stat -f%z "aggregated/results.json" 2>/dev/null || stat -c%s "aggregated/results.json" 2>/dev/null)
    echo -e "${GREEN}✅${NC} aggregated/results.json موجود است (${size} bytes)"
else
    echo -e "${RED}❌${NC} aggregated/results.json موجود نیست!"
fi

# Check admin_results.json
if [ -f "aggregated/admin_results.json" ]; then
    size=$(stat -f%z "aggregated/admin_results.json" 2>/dev/null || stat -c%s "aggregated/admin_results.json" 2>/dev/null)
    echo -e "${GREEN}✅${NC} aggregated/admin_results.json موجود است (${size} bytes)"
else
    echo -e "${RED}❌${NC} aggregated/admin_results.json موجود نیست!"
fi

# Check stats.json
if [ -f "stats.json" ]; then
    size=$(stat -f%z "stats.json" 2>/dev/null || stat -c%s "stats.json" 2>/dev/null)
    echo -e "${GREEN}✅${NC} stats.json موجود است (${size} bytes)"
    echo "محتوای stats.json:"
    cat stats.json
else
    echo -e "${RED}❌${NC} stats.json موجود نیست!"
fi

echo ""
echo "🌐 مرحله 5: تست API"
echo "────────────────────────────────────────────────────────────"

# Test /stats endpoint
echo "تست /stats endpoint..."
response=$(curl -s http://localhost:8080/stats 2>/dev/null)

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅${NC} /stats پاسخ داد"
    echo "پاسخ: $response"
else
    echo -e "${RED}❌${NC} /stats پاسخ نداد"
fi

echo ""
echo "🔍 مرحله 6: بررسی سرویس"
echo "────────────────────────────────────────────────────────────"

# Check if service is running
if systemctl is-active --quiet fastly-collector 2>/dev/null; then
    echo -e "${GREEN}✅${NC} سرویس fastly-collector در حال اجراست"
else
    echo -e "${YELLOW}⚠️${NC} سرویس fastly-collector فعال نیست"
    echo "برای شروع سرویس: sudo systemctl start fastly-collector"
fi

# Check service status
echo ""
echo "وضعیت سرویس:"
systemctl status fastly-collector 2>/dev/null | head -10

echo ""
echo "📋 مرحله 7: بررسی لاگ‌ها"
echo "────────────────────────────────────────────────────────────"

if [ -f "/var/log/fastly-collector.log" ]; then
    echo "آخرین 10 خط لاگ:"
    tail -10 /var/log/fastly-collector.log
else
    echo "فایل لاگ موجود نیست"
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo "✅ عیب‌یابی تمام شد"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "📝 گزارش خلاصه:"
echo ""
echo "اگه مشکل برطرف نشد، این موارد رو چک کن:"
echo "1. مطمئن شو api.py در حال اجراست"
echo "2. دایرکتوری submissions/ فایل داره"
echo "3. aggregator.py رو دستی اجرا کن: python3 aggregator.py"
echo "4. سرویس رو ری‌استارت کن: sudo systemctl restart fastly-collector"
echo "5. dashboard.html رو توی مرورگر باز کن: http://194.36.174.102:8080/"
echo ""
