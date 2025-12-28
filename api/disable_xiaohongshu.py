#!/usr/bin/env python3
"""
Disable all xiaohongshu (小红书) queries - app no longer uses xiaohongshu
"""
from app.database import SessionLocal
from app.models import SourceQuery

db = SessionLocal()

print("=" * 60)
print("Disabling All Xiaohongshu Queries")
print("=" * 60)

# Find all xiaohongshu queries (case insensitive)
xiaohongshu_queries = db.query(SourceQuery).filter(
    SourceQuery.query.ilike("%xiaohongshu%")
).all()

# Also check by site_domain
xiaohongshu_by_domain = db.query(SourceQuery).filter(
    SourceQuery.site_domain.ilike("%xiaohongshu%")
).all()

# Combine and deduplicate
all_xiaohongshu = {q.id: q for q in xiaohongshu_queries + xiaohongshu_by_domain}.values()

if not all_xiaohongshu:
    print("\n✓ No xiaohongshu queries found")
else:
    print(f"\nFound {len(all_xiaohongshu)} xiaohongshu queries:")
    
    for q in all_xiaohongshu:
        was_enabled = q.enabled
        q.enabled = False
        status = "disabled" if was_enabled else "already disabled"
        print(f"  - ID {q.id}: {q.query[:70]}...")
        print(f"    Site: {q.site_domain}")
        print(f"    Source type: {q.source_type}")
        print(f"    Status: {status}")
    
    db.commit()
    print(f"\n✓ Disabled {len(all_xiaohongshu)} xiaohongshu queries")

# Also check for any queries that might reference xiaohongshu in other ways
other_queries = db.query(SourceQuery).filter(
    SourceQuery.query.ilike("%小红书%")
).all()

if other_queries:
    print(f"\nFound {len(other_queries)} queries with Chinese name '小红书':")
    for q in other_queries:
        was_enabled = q.enabled
        q.enabled = False
        status = "disabled" if was_enabled else "already disabled"
        print(f"  - ID {q.id}: {q.query[:70]}...")
        print(f"    Status: {status}")
    db.commit()
    print(f"✓ Disabled {len(other_queries)} additional queries")

print("\n" + "=" * 60)
print("Done! All xiaohongshu queries have been disabled.")
print("=" * 60)

db.close()

