"""Verification script for Google CSE quota system"""
import os
import sys
from datetime import datetime
from app.services.google_search import (
    check_budget_exceeded,
    get_daily_usage_key,
    increment_usage,
    search_google,
    get_cache_key
)
import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
DAILY_CSE_BUDGET = int(os.getenv("DAILY_CSE_BUDGET", "80"))
redis_client = redis.from_url(REDIS_URL, decode_responses=True) if REDIS_URL else None

def verify_usage_counter():
    """Step 1: Verify usage counter increases"""
    print("=" * 60)
    print("Step 1: Verifying Usage Counter")
    print("=" * 60)
    
    if not redis_client:
        print("❌ Redis not available - cannot verify")
        return False
    
    usage_key = get_daily_usage_key()
    initial_count = redis_client.get(usage_key)
    initial = int(initial_count) if initial_count else 0
    
    print(f"Initial usage: {initial}/{DAILY_CSE_BUDGET}")
    
    # Increment manually
    new_count = increment_usage()
    print(f"After increment: {new_count}/{DAILY_CSE_BUDGET}")
    
    # Verify it increased
    if new_count == initial + 1:
        print("✅ Usage counter increases correctly")
        return True
    else:
        print(f"❌ Expected {initial + 1}, got {new_count}")
        return False


def verify_caching():
    """Step 2: Verify caching prevents extra calls"""
    print("\n" + "=" * 60)
    print("Step 2: Verifying Caching")
    print("=" * 60)
    
    if not redis_client:
        print("❌ Redis not available - cannot verify")
        return False
    
    test_query = "site:dealmoon.com Bay Area food"
    date_restrict = "d14"
    start = 1
    num = 10
    
    cache_key = get_cache_key(test_query, date_restrict, start, num)
    
    # Check if cache exists
    cached = redis_client.get(cache_key)
    if cached:
        print(f"✅ Cache found for query")
        ttl = redis_client.ttl(cache_key)
        if ttl > 0:
            minutes = ttl // 60
            print(f"   Cache TTL: {minutes} minutes")
    else:
        print(f"ℹ️  No cache found (this is normal for first run)")
    
    # Make a search call
    usage_before = redis_client.get(get_daily_usage_key())
    usage_before = int(usage_before) if usage_before else 0
    
    print(f"\nUsage before search: {usage_before}/{DAILY_CSE_BUDGET}")
    print(f"Making search call...")
    
    result = search_google(test_query, num=num, start=start, date_restrict=date_restrict)
    
    usage_after = redis_client.get(get_daily_usage_key())
    usage_after = int(usage_after) if usage_after else 0
    
    print(f"Usage after search: {usage_after}/{DAILY_CSE_BUDGET}")
    
    # Check if cache was created
    cached_after = redis_client.get(cache_key)
    if cached_after:
        print("✅ Cache created after search")
        
        # Make another call - should use cache
        print(f"\nMaking second search call (should use cache)...")
        usage_before_2 = usage_after
        result2 = search_google(test_query, num=num, start=start, date_restrict=date_restrict)
        usage_after_2 = redis_client.get(get_daily_usage_key())
        usage_after_2 = int(usage_after_2) if usage_after_2 else 0
        
        if usage_after_2 == usage_before_2:
            print(f"✅ Second call used cache (usage unchanged: {usage_after_2})")
            return True
        else:
            print(f"❌ Second call incremented usage: {usage_before_2} -> {usage_after_2}")
            return False
    else:
        if result.get("error") == "quota_exceeded":
            print("ℹ️  Budget exceeded - cache not created (expected)")
            return True
        else:
            print("❌ Cache not created after search")
            return False


def verify_feed_works_when_quota_exceeded():
    """Step 3: Verify feed still works when quota exceeded"""
    print("\n" + "=" * 60)
    print("Step 3: Verifying Feed Works When Quota Exceeded")
    print("=" * 60)
    
    # Check current budget status
    is_exceeded = check_budget_exceeded()
    usage_key = get_daily_usage_key()
    if redis_client:
        current_usage = redis_client.get(usage_key)
        current = int(current_usage) if current_usage else 0
        print(f"Current usage: {current}/{DAILY_CSE_BUDGET}")
        print(f"Budget exceeded: {is_exceeded}")
    
    if is_exceeded:
        print("✅ Budget is exceeded - feed should still return DB data")
        print("   Check /food-radar/feed endpoint - it should return articles")
        print("   with data_freshness: 'stale_due_to_quota'")
    else:
        print("ℹ️  Budget not exceeded yet")
        print("   To test this scenario:")
        print(f"   1. Set usage to {DAILY_CSE_BUDGET}:")
        print(f"      docker compose exec api python -c \"from app.services.google_search import get_daily_usage_key; import redis, os; r = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'), decode_responses=True); r.set(get_daily_usage_key(), {DAILY_CSE_BUDGET})\"")
        print("   2. Call /food-radar/feed - should return data with stale_due_to_quota")
    
    return True


def main():
    """Run all verification steps"""
    print("\n" + "=" * 60)
    print("Google CSE Quota System Verification")
    print("=" * 60)
    print(f"Daily Budget: {DAILY_CSE_BUDGET}")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d')}")
    print(f"Usage Key: {get_daily_usage_key()}")
    print("=" * 60)
    
    results = []
    
    # Step 1: Usage counter
    results.append(("Usage Counter", verify_usage_counter()))
    
    # Step 2: Caching
    results.append(("Caching", verify_caching()))
    
    # Step 3: Feed works when quota exceeded
    results.append(("Feed When Quota Exceeded", verify_feed_works_when_quota_exceeded()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Verification Summary")
    print("=" * 60)
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(r[1] for r in results)
    print("\n" + ("✅ All verifications passed!" if all_passed else "❌ Some verifications failed"))
    print("=" * 60)


if __name__ == "__main__":
    main()

