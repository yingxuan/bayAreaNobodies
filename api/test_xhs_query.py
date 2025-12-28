#!/usr/bin/env python3
"""Test different xiaohongshu queries"""
from app.services.google_search import search_google, fetch_multiple_pages

queries = [
    "site:xiaohongshu.com boba",
    "site:xiaohongshu.com Sunnyvale",
    "site:xiaohongshu.com 奶茶",
    "xiaohongshu.com boba Sunnyvale",
]

print("=" * 60)
print("Testing Xiaohongshu Search Queries")
print("=" * 60)

for query in queries:
    print(f"\nQuery: {query}")
    print("-" * 60)
    try:
        results = search_google(
            query=query,
            site_domain="xiaohongshu.com",
            num=5,
            use_cache=False
        )
        items = results.get("items", [])
        total = results.get("searchInformation", {}).get("totalResults", "0")
        print(f"  Total results: {total}")
        print(f"  Items returned: {len(items)}")
        if items:
            for i, item in enumerate(items[:3], 1):
                print(f"    {i}. {item.get('title', 'No title')[:50]}...")
    except Exception as e:
        print(f"  Error: {e}")

print("\n" + "=" * 60)
print("Testing fetch_multiple_pages with simple query")
print("=" * 60)
try:
    results = fetch_multiple_pages(
        query="site:xiaohongshu.com boba",
        site_domain="xiaohongshu.com",
        max_results=10
    )
    print(f"Found {len(results)} results")
    if results:
        for i, r in enumerate(results[:3], 1):
            print(f"  {i}. {r.get('title', 'No title')[:60]}")
except Exception as e:
    print(f"Error: {e}")

