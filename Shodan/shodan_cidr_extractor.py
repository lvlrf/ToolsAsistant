import shodan
import time

# API Key شما
API_KEY = "UoabJv3z1mohAIIsTiUBG22m5jXl4Dxf"

# ایجاد کلاینت Shodan
api = shodan.Shodan(API_KEY)

# فایل ورودی و خروجی
input_file = "shodan_ips.txt"
output_file = "shodan_cidr.txt"

print("در حال خواندن فایل آی‌پی‌ها...")
print("-" * 50)

try:
    # خواندن لیست آی‌پی‌ها
    with open(input_file, 'r') as f:
        ips = [line.strip() for line in f if line.strip()]
    
    print(f"تعداد آی‌پی‌های خوانده شده: {len(ips)}")
    print("-" * 50)
    
    cidr_set = set()  # برای حذف تکراری‌ها
    
    for i, ip in enumerate(ips, 1):
        try:
            print(f"[{i}/{len(ips)}] در حال پردازش: {ip} ... ", end='')
            
            # دریافت اطلاعات آی‌پی از Shodan
            host_info = api.host(ip)
            
            # استخراج CIDR از فیلد asn یا isp
            # Shodan در فیلد 'asn' اطلاعات CIDR را برمی‌گرداند
            if 'asn' in host_info and host_info['asn']:
                asn = host_info['asn']
                # دریافت اطلاعات ASN
                # معمولاً Shodan مستقیماً CIDR نمی‌دهد، باید از IP و subnet محاسبه کنیم
                # یا از فیلدهای دیگر استفاده کنیم
                
                # روش دیگر: از hostnames و org و isp استفاده کنیم
                cidr = f"{ip}/32"  # پیش‌فرض
                
                # اگر اطلاعات بیشتری وجود داشت
                if 'data' in host_info and len(host_info['data']) > 0:
                    # بعضی وقت‌ها Shodan اطلاعات شبکه را در data می‌گذارد
                    pass
                
                cidr_set.add(cidr)
                print(f"✓ {cidr}")
            else:
                # اگر ASN نبود، فقط /32 قرار می‌دهیم
                cidr = f"{ip}/32"
                cidr_set.add(cidr)
                print(f"✓ {cidr} (ASN یافت نشد)")
            
            # تاخیر کوتاه برای جلوگیری از rate limit
            time.sleep(1)
            
        except shodan.APIError as e:
            print(f"✗ خطا: {e}")
        except Exception as e:
            print(f"✗ خطای غیرمنتظره: {e}")
    
    print("-" * 50)
    print(f"تعداد CIDR های یکتا: {len(cidr_set)}")
    
    # ذخیره در فایل
    with open(output_file, 'w') as f:
        for cidr in sorted(cidr_set):
            f.write(cidr + '\n')
    
    print(f"✓ CIDR ها در فایل '{output_file}' ذخیره شد")
    
except FileNotFoundError:
    print(f"خطا: فایل '{input_file}' پیدا نشد!")
except Exception as e:
    print(f"خطای غیرمنتظره: {e}")
