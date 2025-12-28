#!/usr/bin/env python3
"""Test the food feed API endpoint"""
import httpx
import json

API_URL = "http://localhost:8000"

print("=" * 60)
print("Testing Food Feed API")
print("=" * 60)

try:
    # Test the food feed endpoint
    response = httpx.get(f"{API_URL}/feeds/food?limit=10", timeout=10.0)
    response.raise_for_status()
    data = response.json()
    
    print(f"\n✓ API Response successful")
    print(f"  Total articles: {data.get('total', 0)}")
    print(f"  Articles returned: {len(data.get('articles', []))}")
    
    articles = data.get('articles', [])
    if articles:
        print(f"\n  Sample articles:")
        for i, article in enumerate(articles[:5], 1):
            title = article.get('title', 'No title')
            platform = article.get('platform', 'unknown')
            score = article.get('final_score', 0)
            print(f"    {i}. {title[:50]}...")
            print(f"       Platform: {platform}, Score: {score:.3f}")
    else:
        print("\n  ⚠️  No articles returned!")
    
    print("\n" + "=" * 60)
    print("API Test Complete")
    print("=" * 60)
    
except Exception as e:
    print(f"\n✗ Error testing API: {e}")
    import traceback
    traceback.print_exc()

