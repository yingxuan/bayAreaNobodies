#!/usr/bin/env python3
import requests

API_URL = "http://localhost:8000"

print("Testing /feeds/food endpoint...")
r = requests.get(f"{API_URL}/feeds/food?limit=5")
print(f"Status: {r.status_code}")

if r.status_code == 200:
    data = r.json()
    articles = data.get("articles", [])
    print(f"Articles count: {len(articles)}")
    print("\nFirst 3 articles:")
    for i, article in enumerate(articles[:3], 1):
        print(f"  {i}. {article.get('title', 'N/A')[:60]}")
else:
    print(f"Error: {r.text}")

