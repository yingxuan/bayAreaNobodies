#!/usr/bin/env python3
"""Add Yelp as a data source for food_radar queries"""
from app.database import SessionLocal
from app.models import SourceQuery

db = SessionLocal()

print("=" * 60)
print("Adding Yelp Queries for Food & Boba")
print("=" * 60)

# Yelp queries for Chinese food and boba in Bay Area
yelp_queries = [
    {
        "query": "site:yelp.com Bay Area Chinese restaurant",
        "site_domain": "yelp.com",
        "description": "Bay Area Chinese restaurants on Yelp"
    },
    {
        "query": "site:yelp.com Bay Area boba milk tea",
        "site_domain": "yelp.com",
        "description": "Bay Area boba shops on Yelp"
    },
    {
        "query": "site:yelp.com San Francisco Chinese food",
        "site_domain": "yelp.com",
        "description": "SF Chinese food on Yelp"
    },
    {
        "query": "site:yelp.com San Jose Chinese restaurant",
        "site_domain": "yelp.com",
        "description": "San Jose Chinese restaurants on Yelp"
    },
    {
        "query": "site:yelp.com Cupertino boba",
        "site_domain": "yelp.com",
        "description": "Cupertino boba on Yelp"
    },
    {
        "query": "site:yelp.com Bay Area dim sum",
        "site_domain": "yelp.com",
        "description": "Bay Area dim sum on Yelp"
    },
    {
        "query": "site:yelp.com Bay Area hot pot",
        "site_domain": "yelp.com",
        "description": "Bay Area hot pot on Yelp"
    },
    {
        "query": "site:yelp.com 湾区 中餐",
        "site_domain": "yelp.com",
        "description": "Bay Area Chinese food (Chinese query)"
    },
    {
        "query": "site:yelp.com 湾区 奶茶",
        "site_domain": "yelp.com",
        "description": "Bay Area boba (Chinese query)"
    },
]

added_count = 0
for q_data in yelp_queries:
    existing = db.query(SourceQuery).filter(
        SourceQuery.source_type == "food_radar",
        SourceQuery.query == q_data["query"]
    ).first()
    
    if not existing:
        new_query = SourceQuery(
            source_type="food_radar",
            query=q_data["query"],
            site_domain=q_data["site_domain"],
            city=None,
            enabled=True,
            interval_min=180  # Run every 3 hours
        )
        db.add(new_query)
        print(f"✅ Added: {q_data['description']}")
        print(f"   Query: {q_data['query']}")
        added_count += 1
    else:
        print(f"⏭️  Skipped (already exists): {q_data['query']}")

db.commit()

print("\n" + "=" * 60)
print(f"✅ Added {added_count} new Yelp queries!")
print("=" * 60)
print("\nNext steps:")
print("  1. Run: docker exec bayareanobodies_api python trigger_scheduler.py")
print("  2. Or wait for the scheduler to run automatically")

db.close()

