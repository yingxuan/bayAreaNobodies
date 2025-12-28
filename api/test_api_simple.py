#!/usr/bin/env python3
"""Simple API test"""
import httpx

try:
    r = httpx.get('http://localhost:8000/feeds/food?limit=3', timeout=5.0)
    print(f"API Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        articles = data.get('articles', [])
        print(f"Articles returned: {len(articles)}")
        if articles:
            first = articles[0]
            print(f"First article platform: {first.get('platform')}")
            print(f"First article video_id: {first.get('video_id')}")
    else:
        print(f"Error: {r.text[:200]}")
except Exception as e:
    print(f"Error: {e}")

