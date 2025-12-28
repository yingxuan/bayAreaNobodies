# Google CSE Quota System Verification Guide

This guide explains how to verify that the quota-aware logic is working correctly.

## Quick Verification

Run the automated verification script:

```bash
docker compose exec api python verify_quota_system.py
```

This will test:
1. Usage counter increases
2. Caching prevents extra calls
3. Feed still works when quota exceeded

## Step-by-Step Manual Verification

### Step 1: Verify Usage Counter Increases

**What to check**: Each CSE API call increments the daily usage counter.

**How to verify**:

```bash
# Check current usage
docker compose exec api python -c "
from app.services.google_search import get_daily_usage_key
import redis, os
r = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'), decode_responses=True)
key = get_daily_usage_key()
usage = r.get(key) or '0'
print(f'Current usage: {usage}/80')
"

# Make a test search call
docker compose exec api python -c "
from app.services.google_search import search_google
result = search_google('site:dealmoon.com Bay Area food', num=5)
print('Search completed')
"

# Check usage again (should be +1)
docker compose exec api python -c "
from app.services.google_search import get_daily_usage_key
import redis, os
r = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'), decode_responses=True)
key = get_daily_usage_key()
usage = r.get(key) or '0'
print(f'Usage after search: {usage}/80')
"
```

**Expected result**: Usage counter increases by 1 after each API call.

### Step 2: Verify Caching Prevents Extra Calls

**What to check**: Repeated queries within 30 minutes use cache and don't consume budget.

**How to verify**:

```bash
# Make first search call (will consume budget)
docker compose exec api python -c "
from app.services.google_search import search_google, get_daily_usage_key
import redis, os
r = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'), decode_responses=True)
key = get_daily_usage_key()
usage_before = int(r.get(key) or '0')
print(f'Usage before: {usage_before}/80')
result = search_google('test query', num=5)
usage_after = int(r.get(key) or '0')
print(f'Usage after: {usage_after}/80')
print(f'Budget consumed: {usage_after - usage_before}')
"

# Make same search call again immediately (should use cache)
docker compose exec api python -c "
from app.services.google_search import search_google, get_daily_usage_key
import redis, os
r = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'), decode_responses=True)
key = get_daily_usage_key()
usage_before = int(r.get(key) or '0')
print(f'Usage before (2nd call): {usage_before}/80')
result = search_google('test query', num=5)  # Same query
usage_after = int(r.get(key) or '0')
print(f'Usage after (2nd call): {usage_after}/80')
print(f'Budget consumed: {usage_after - usage_before}')
if usage_after == usage_before:
    print('✅ Cache used - no budget consumed')
else:
    print('❌ Cache not working - budget was consumed')
"
```

**Expected result**: Second call uses cache, usage counter doesn't increase.

### Step 3: Verify Feed Still Works When Quota Exceeded

**What to check**: `/food-radar/feed` returns DB data even when budget is exceeded, with `data_freshness: "stale_due_to_quota"`.

**How to verify**:

```bash
# 1. Set usage to budget limit (simulate quota exceeded)
docker compose exec api python -c "
from app.services.google_search import get_daily_usage_key
import redis, os
r = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'), decode_responses=True)
key = get_daily_usage_key()
r.set(key, 80)  # Set to budget limit
print(f'Usage set to: {r.get(key)}/80')
"

# 2. Call the feed endpoint
curl http://localhost:8000/food-radar/feed | jq '.data_freshness'

# Or using Python:
docker compose exec api python -c "
import requests
response = requests.get('http://localhost:8000/food-radar/feed')
data = response.json()
print(f\"Data freshness: {data.get('data_freshness')}\")
print(f\"Articles returned: {data.get('total', 0)}\")
if data.get('data_freshness') == 'stale_due_to_quota':
    print('✅ Feed works correctly when quota exceeded')
else:
    print('❌ Feed not indicating stale data')
"
```

**Expected result**: 
- Feed returns articles from database
- `data_freshness` is `"stale_due_to_quota"`
- No errors in response

### Step 4: Verify Scheduler Behavior

**What to check**: Scheduler skips remaining CSE queries when budget exceeded, but continues other jobs.

**How to verify**:

```bash
# 1. Set usage to budget limit
docker compose exec api python -c "
from app.services.google_search import get_daily_usage_key
import redis, os
r = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'), decode_responses=True)
key = get_daily_usage_key()
r.set(key, 80)
print('Usage set to budget limit')
"

# 2. Check scheduler logs
docker compose logs api | grep -i "budget\|quota\|skipping"

# 3. Manually trigger search jobs
docker compose exec api python -c "
from app.scheduler import run_search_jobs
run_search_jobs()
"
```

**Expected result**: 
- Log shows "WARNING: Daily CSE budget exceeded. Skipping remaining X queries."
- Scheduler completes without errors
- Other non-CSE jobs continue normally

## Monitoring Daily Usage

Check current usage anytime:

```bash
docker compose exec api python -c "
from app.services.google_search import get_daily_usage_key, check_budget_exceeded
import redis, os
r = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'), decode_responses=True)
key = get_daily_usage_key()
usage = int(r.get(key) or '0')
budget = int(os.getenv('DAILY_CSE_BUDGET', '80'))
exceeded = check_budget_exceeded()
print(f'Usage: {usage}/{budget}')
print(f'Budget exceeded: {exceeded}')
print(f'Remaining: {budget - usage}')
"
```

## Resetting Usage Counter (for testing)

To reset the daily counter (e.g., for testing):

```bash
docker compose exec api python -c "
from app.services.google_search import get_daily_usage_key
import redis, os
r = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'), decode_responses=True)
key = get_daily_usage_key()
r.delete(key)
print('Usage counter reset')
"
```

## Troubleshooting

### Cache not working

- Check Redis is running: `docker compose ps redis`
- Check cache TTL: Cache expires after 30 minutes
- Verify cache key format matches

### Usage counter not incrementing

- Check Redis connection
- Verify `DAILY_CSE_BUDGET` env var is set
- Check logs for errors

### Feed returns empty when quota exceeded

- Verify database has articles: `docker compose exec api python -c "from app.database import SessionLocal; from app.models import Article; db = SessionLocal(); print(db.query(Article).filter(Article.source_type == 'food_radar').count())"`
- Check `data_freshness` field in response

