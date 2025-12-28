#!/usr/bin/env python3
"""
Debug why a query returns no results
"""
import os
import sys
from app.database import SessionLocal
from app.models import SourceQuery
from app.services.google_search import search_google, fetch_multiple_pages

# Get query ID from command line or use default
query_id = int(sys.argv[1]) if len(sys.argv) > 1 else 26

db = SessionLocal()

print("=" * 60)
print(f"Debugging Query ID {query_id}")
print("=" * 60)

# Get the query
query_obj = db.query(SourceQuery).filter(SourceQuery.id == query_id).first()

if not query_obj:
    print(f"❌ Query ID {query_id} not found!")
    db.close()
    sys.exit(1)

print(f"\nQuery: {query_obj.query}")
print(f"Site Domain: {query_obj.site_domain}")
print(f"Source Type: {query_obj.source_type}")
print(f"Enabled: {query_obj.enabled}")
print(f"Interval: {query_obj.interval_min} min")

# Check API configuration
print("\n" + "-" * 60)
print("Checking Google CSE Configuration")
print("-" * 60)

GOOGLE_CSE_API_KEY = os.getenv("GOOGLE_CSE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")

if not GOOGLE_CSE_API_KEY:
    print("❌ GOOGLE_CSE_API_KEY not set!")
elif not GOOGLE_CSE_ID:
    print("❌ GOOGLE_CSE_ID not set!")
else:
    print(f"✓ API Key: {GOOGLE_CSE_API_KEY[:10]}...{GOOGLE_CSE_API_KEY[-4:]}")
    print(f"✓ CSE ID: {GOOGLE_CSE_ID[:20]}...{GOOGLE_CSE_ID[-10:]}")

# Test the search
print("\n" + "-" * 60)
print("Testing Google Search API")
print("-" * 60)

try:
    # Test without date restriction first
    print("\n1. Testing without date restriction...")
    results_no_date = search_google(
        query=query_obj.query,
        site_domain=query_obj.site_domain,
        num=10,
        date_restrict=None
    )
    
    items_no_date = results_no_date.get("items", [])
    total_no_date = results_no_date.get("searchInformation", {}).get("totalResults", "0")
    
    print(f"   Results: {len(items_no_date)} items")
    print(f"   Total available: {total_no_date}")
    
    if items_no_date:
        print(f"   First result: {items_no_date[0].get('title', 'No title')[:60]}...")
        print(f"   URL: {items_no_date[0].get('link', 'No URL')[:60]}...")
    
    # Test with date restriction (as used in scheduler)
    print("\n2. Testing with date restriction (d14 - last 14 days)...")
    results_with_date = search_google(
        query=query_obj.query,
        site_domain=query_obj.site_domain,
        num=10,
        date_restrict="d14"
    )
    
    items_with_date = results_with_date.get("items", [])
    total_with_date = results_with_date.get("searchInformation", {}).get("totalResults", "0")
    
    print(f"   Results: {len(items_with_date)} items")
    print(f"   Total available: {total_with_date}")
    
    if items_with_date:
        print(f"   First result: {items_with_date[0].get('title', 'No title')[:60]}...")
        print(f"   URL: {items_with_date[0].get('link', 'No URL')[:60]}...")
    else:
        print("   ⚠️  No results with date restriction!")
        print("   → This is why the scheduler finds no content")
        print("   → Try removing date restriction or using a longer period")
    
    # Test fetch_multiple_pages (as used in scheduler)
    print("\n3. Testing fetch_multiple_pages (as used in scheduler)...")
    all_results = fetch_multiple_pages(
        query=query_obj.query,
        site_domain=query_obj.site_domain,
        max_results=30,
        date_restrict="d14"
    )
    
    print(f"   Total results fetched: {len(all_results)}")
    
    if all_results:
        print("\n   Sample results:")
        for i, item in enumerate(all_results[:5], 1):
            url = item.get("link", "")
            title = item.get("title", "No title")
            print(f"   {i}. {title[:60]}...")
            print(f"      {url[:70]}...")
    else:
        print("   ⚠️  No results returned!")
        print("\n   Possible reasons:")
        print("   1. Google CSE doesn't include youtube.com in search")
        print("   2. No content matching query in last 14 days")
        print("   3. API quota exceeded")
        print("   4. CSE configuration issue")
        
        # Check if CSE includes the site
        if query_obj.site_domain:
            print(f"\n   → Check if your CSE includes: {query_obj.site_domain}")
            print("   → Go to Google CSE settings and verify the site is added")
    
except Exception as e:
    print(f"❌ Error testing search: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Debug Complete")
print("=" * 60)

db.close()

