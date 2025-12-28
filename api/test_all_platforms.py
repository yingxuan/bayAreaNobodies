#!/usr/bin/env python3
"""
Test all food_radar platform queries (YouTube, TikTok, Instagram)
"""
from app.database import SessionLocal
from app.models import SourceQuery
from app.services.google_search import search_google

db = SessionLocal()

print("=" * 60)
print("Testing All Food Radar Platform Queries")
print("=" * 60)

# Get all enabled food_radar queries
queries = db.query(SourceQuery).filter(
    SourceQuery.source_type == "food_radar",
    SourceQuery.enabled == True
).all()

print(f"\nFound {len(queries)} enabled food_radar queries\n")

platforms = {}
for q in queries:
    platform = q.site_domain or "web"
    if platform not in platforms:
        platforms[platform] = []
    platforms[platform].append(q)

for platform, platform_queries in platforms.items():
    print("-" * 60)
    print(f"Platform: {platform.upper() if platform else 'WEB (no site restriction)'}")
    print("-" * 60)
    
    # Test first query for each platform
    test_query = platform_queries[0]
    print(f"Testing: {test_query.query[:70]}...")
    
    try:
        results = search_google(
            query=test_query.query,
            site_domain=test_query.site_domain,
            num=5,
            date_restrict=None  # No date restriction for testing
        )
        
        items = results.get("items", [])
        total = results.get("searchInformation", {}).get("totalResults", "0")
        
        if items:
            print(f"  ✓ SUCCESS: {len(items)} results, Total: {total}")
            print(f"  ✓ First result: {items[0].get('title', 'No title')[:60]}...")
        else:
            print(f"  ✗ FAILED: 0 results")
            print(f"  → CSE may not include {platform}")
            print(f"  → Go to Google CSE settings and add '{platform}' to sites to search")
        
        print(f"  Total queries for this platform: {len(platform_queries)}")
        
    except Exception as e:
        print(f"  ✗ ERROR: {e}")

print("\n" + "=" * 60)
print("Summary")
print("=" * 60)
print("If a platform shows 0 results, you need to:")
print("1. Go to https://programmablesearchengine.google.com/")
print("2. Edit your CSE")
print("3. Add the platform domain to 'Sites to search'")
print("4. Wait a few minutes for indexing")
print("=" * 60)

db.close()

