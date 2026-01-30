import shodan

# API Key شما
API_KEY = "UoabJv3z1mohAIIsTiUBG22m5jXl4Dxf"

# ایجاد کلاینت Shodan
api = shodan.Shodan(API_KEY)

# جستجوی مورد نظر
query = 'country:"IR" port:443 product:"CloudFlare"'

print(f"در حال جستجو: {query}")
print("-" * 50)

try:
    # انجام جستجو
    results = api.search(query)
    
    # تعداد کل نتایج
    print(f"تعداد کل نتایج: {results['total']}")
    print(f"تعداد نتایج دریافت شده: {len(results['matches'])}")
    print("-" * 50)
    
    # لیست آی‌پی‌ها
    ip_list = []
    
    for result in results['matches']:
        ip = result['ip_str']
        ip_list.append(ip)
        print(ip)
    
    # ذخیره در فایل
    output_file = "shodan_ips.txt"
    with open(output_file, 'w') as f:
        for ip in ip_list:
            f.write(ip + '\n')
    
    print("-" * 50)
    print(f"✓ آی‌پی‌ها در فایل '{output_file}' ذخیره شد")
    
except shodan.APIError as e:
    print(f"خطا: {e}")
except Exception as e:
    print(f"خطای غیرمنتظره: {e}")
