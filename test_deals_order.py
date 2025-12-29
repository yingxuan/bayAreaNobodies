import requests

r = requests.get('http://localhost:8000/feeds/deals?limit=10')
data = r.json()
print("前10个deal的类别顺序:")
for i, coupon in enumerate(data.get('coupons', [])[:10], 1):
    print(f"{i}. {coupon.get('category')} - {coupon.get('title', '')[:60]}")

