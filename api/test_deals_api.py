#!/usr/bin/env python3
"""Test deals API"""
import httpx

try:
    r = httpx.get('http://localhost:8000/feeds/deals?limit=5', timeout=10.0)
    print(f"API Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        coupons = data.get('coupons', [])
        print(f"Coupons returned: {len(coupons)}")
        if coupons:
            print("\nSample coupons:")
            for c in coupons[:3]:
                print(f"  - {c.get('title', 'No title')[:50]}...")
                print(f"    Code: {c.get('code')}, City: {c.get('city')}")
        else:
            print("\n⚠️  No coupons returned!")
    else:
        print(f"Error: {r.text[:200]}")
except Exception as e:
    print(f"Error: {e}")

