"""Test script to check Google CSE quota status and cache behavior"""
import os
import sys
from app.database import SessionLocal
from app.services.google_search import check_quota_exceeded, search_google
import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(REDIS_URL, decode_responses=True) if REDIS_URL else None

def test_quota_check():
    """Test quota check functionality"""
    print("=" * 60)
    print("Testing Google CSE API Quota Management")
    print("=" * 60)
    
    # Check current quota status
    quota_exceeded = check_quota_exceeded()
    print(f"\n1. Quota Status: {'EXCEEDED' if quota_exceeded else 'OK'}")
    
    if quota_exceeded:
        print("   ⚠️  API quota has been exceeded. All search queries will be skipped.")
        if redis_client:
            quota_key = "google_cse:quota_exceeded"
            ttl = redis_client.ttl(quota_key)
            if ttl > 0:
                hours = ttl // 3600
                minutes = (ttl % 3600) // 60
                print(f"   ⏰ Quota flag will expire in {hours}h {minutes}m")
    else:
        print("   ✅ API quota is available. Search queries will proceed.")
    
    # Test cache behavior
    print("\n2. Testing Cache Behavior:")
    test_query = "site:dealmoon.com Bay Area food"
    
    if redis_client:
        # Generate cache key using same method as google_search.py
        import hashlib
        key_str = f"google_search:{test_query}:1"
        cache_key = hashlib.md5(key_str.encode()).hexdigest()
        
        cached = redis_client.get(cache_key)
        if cached:
            print(f"   ✅ Cache found for query: {test_query}")
            ttl = redis_client.ttl(cache_key)
            if ttl > 0:
                hours = ttl // 3600
                minutes = (ttl % 3600) // 60
                print(f"   ⏰ Cache expires in {hours}h {minutes}m")
        else:
            print(f"   ℹ️  No cache found for query: {test_query}")
    else:
        print("   ⚠️  Redis not available - caching disabled")
    
    # Test search (only if quota not exceeded)
    if not quota_exceeded:
        print("\n3. Testing Search Query:")
        print(f"   Query: {test_query}")
        try:
            results = search_google(test_query, num=5)
            if results.get("error"):
                print(f"   ❌ Error: {results.get('error')}")
            else:
                items = results.get("items", [])
                print(f"   ✅ Found {len(items)} results")
                if items:
                    print(f"   📄 First result: {items[0].get('title', 'N/A')[:50]}...")
        except Exception as e:
            print(f"   ❌ Exception: {e}")
    else:
        print("\n3. Skipping search test (quota exceeded)")
    
    print("\n" + "=" * 60)
    print("Test completed")
    print("=" * 60)

if __name__ == "__main__":
    test_quota_check()

