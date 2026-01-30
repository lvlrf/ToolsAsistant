#!/bin/bash
# Fastly Scanner Dashboard - Quick Fix
# Created by: DrConnect

echo "════════════════════════════════════════════════════════════"
echo "🔧 رفع سریع مشکلات Dashboard"
echo "════════════════════════════════════════════════════════════"
echo ""

# Set working directory
cd /opt/fastly-collector 2>/dev/null || cd .

echo "1️⃣ ساخت دایرکتوری‌های لازم..."
mkdir -p submissions
mkdir -p aggregated
mkdir -p dl
echo "✅ دایرکتوری‌ها ایجاد شدند"

echo ""
echo "2️⃣ تنظیم مجوزها..."
chmod 755 submissions aggregated dl
chmod +x aggregator.py dashboard_update.sh 2>/dev/null
echo "✅ مجوزها تنظیم شدند"

echo ""
echo "3️⃣ اجرای Aggregator..."
if [ -f "aggregator.py" ]; then
    python3 aggregator.py
    echo "✅ Aggregator اجرا شد"
else
    echo "❌ aggregator.py موجود نیست!"
    exit 1
fi

echo ""
echo "4️⃣ بررسی خروجی..."
if [ -f "aggregated/results.json" ]; then
    echo "✅ results.json ساخته شد"
else
    echo "⚠️ results.json ساخته نشد - احتمالاً submission فایلی موجود نیست"
    echo "   یک تست اسکن انجام بده تا فایل ساخته بشه"
fi

if [ -f "stats.json" ]; then
    echo "✅ stats.json ساخته شد"
    echo "محتوا:"
    cat stats.json
else
    echo "⚠️ stats.json ساخته نشد"
fi

echo ""
echo "5️⃣ ری‌استارت سرویس..."
if systemctl is-active --quiet fastly-collector 2>/dev/null; then
    sudo systemctl restart fastly-collector
    echo "✅ سرویس ری‌استارت شد"
    sleep 2
else
    echo "⚠️ سرویس در حال اجرا نیست"
    echo "برای شروع: sudo systemctl start fastly-collector"
fi

echo ""
echo "6️⃣ تست API..."
sleep 1
response=$(curl -s http://localhost:8080/stats 2>/dev/null)

if [ $? -eq 0 ] && [ ! -z "$response" ]; then
    echo "✅ API کار میکنه"
    echo "پاسخ: $response"
else
    echo "❌ API پاسخ نمیده"
    echo "چک کن که سرویس در حال اجراست:"
    echo "sudo systemctl status fastly-collector"
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo "✅ رفع مشکلات تمام شد!"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "📝 مراحل بعدی:"
echo ""
echo "1. اگه هنوز داده نداری، یک تست اسکن انجام بده:"
echo "   python3 scanner.py"
echo ""
echo "2. بعد از اسکن، دوباره aggregator رو اجرا کن:"
echo "   python3 aggregator.py"
echo ""
echo "3. Dashboard رو باز کن:"
echo "   http://194.36.174.102:8080/"
echo ""
echo "4. برای Admin Mode:"
echo "   http://194.36.174.102:8080/?key=DrConnect2025Admin"
echo ""
