#!/usr/bin/env python3
"""
Test different YouTube query formats to see which works
"""
import os
from app.services.google_search import search_google

GOOGLE_CSE_API_KEY = os.getenv("GOOGLE_CSE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")

print("=" * 60)
print("Testing Different YouTube Query Formats")
print("=" * 60)

# Test queries
test_queries = [
    {
        "name": "Original query with site: in query",
        "query": "site:youtube.com Bay Area Chinese restaurant review",
        "site_domain": "youtube.com"
    },
    {
        "name": "Query without site:, using siteSearch param",
        "query": "Bay Area Chinese restaurant review",
        "site_domain": "youtube.com"
    },
    {
        "name": "Simpler query",
        "query": "Bay Area Chinese food",
        "site_domain": "youtube.com"
    },
    {
        "name": "Chinese keywords",
        "query": "湾区 中餐 探店",
        "site_domain": "youtube.com"
    },
    {
        "name": "No site restriction (test if CSE works at all)",
        "query": "Bay Area Chinese restaurant",
        "site_domain": None
    }
]

for i, test in enumerate(test_queries, 1):
    print(f"\n{i}. {test['name']}")
    print(f"   Query: {test['query']}")
    print(f"   Site Domain: {test['site_domain']}")
    print("   Testing...")
    
    try:
        results = search_google(
            query=test['query'],
            site_domain=test['site_domain'],
            num=5,
            date_restrict=None  # No date restriction for testing
        )
        
        items = results.get("items", [])
        total = results.get("searchInformation", {}).get("totalResults", "0")
        
        print(f"   ✓ Results: {len(items)} items, Total: {total}")
        
        if items:
            print(f"   ✓ First result: {items[0].get('title', 'No title')[:50]}...")
        else:
            print(f"   ⚠️  No results")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")

print("\n" + "=" * 60)
print("Recommendations:")
print("=" * 60)
print("1. If all queries return 0 results, your CSE may not include youtube.com")
print("2. Go to https://programmablesearchengine.google.com/")
print("3. Edit your CSE and add 'youtube.com' to the sites to search")
print("4. Or create a new CSE specifically for YouTube content")
print("=" * 60)

