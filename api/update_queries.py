#!/usr/bin/env python3
"""Update existing queries to new configuration"""
from app.database import SessionLocal
from app.models import SourceQuery

db = SessionLocal()

print("=" * 60)
print("Updating Search Queries")
print("=" * 60)

# Disable old generic blind query
old_blind = db.query(SourceQuery).filter(
    SourceQuery.source_type == "blind",
    SourceQuery.query.like("%layoff OR promo OR comp%"),
    ~SourceQuery.query.like("%Google%"),
    ~SourceQuery.query.like("%Meta%"),
    ~SourceQuery.query.like("%LinkedIn%"),
    ~SourceQuery.query.like("%Pinterest%"),
    ~SourceQuery.query.like("%OpenAI%")
).all()

for q in old_blind:
    print(f"Disabling old blind query: {q.query}")
    q.enabled = False

# Add new food_radar queries if they don't exist
# Including queries for Chinese food bloggers' content
new_food_queries = [
    {
        "query": "site:youtube.com Bay Area Chinese restaurant review",
        "site_domain": "youtube.com"
    },
    {
        "query": "site:youtube.com Bay Area dim sum hot pot boba",
        "site_domain": "youtube.com"
    },
    {
        "query": "site:youtube.com 探店 湾区 中餐",
        "site_domain": "youtube.com"
    },
    {
        "query": "site:youtube.com 美食 湾区 火锅 奶茶",
        "site_domain": "youtube.com"
    },
    {
        "query": "site:tiktok.com Bay Area Chinese food",
        "site_domain": "tiktok.com"
    },
    {
        "query": "site:tiktok.com Bay Area boba dim sum",
        "site_domain": "tiktok.com"
    },
    {
        "query": "site:tiktok.com 探店 湾区",
        "site_domain": "tiktok.com"
    },
    {
        "query": "site:instagram.com Bay Area Chinese restaurant",
        "site_domain": "instagram.com"
    },
    {
        "query": "site:instagram.com Bay Area boba dim sum",
        "site_domain": "instagram.com"
    },
    {
        "query": "site:instagram.com 探店 湾区 美食",
        "site_domain": "instagram.com"
    },
    {
        "query": "湾区 探店 中餐 美食博主",
        "site_domain": None
    },
    {
        "query": "Bay Area 探店 火锅 奶茶 美食",
        "site_domain": None
    },
]

for q_data in new_food_queries:
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
            interval_min=180
        )
        db.add(new_query)
        print(f"Added food_radar query: {q_data['query']}")

# Add new blind queries for major tech companies
tech_companies = ["Google", "Meta Facebook", "LinkedIn", "Pinterest", "OpenAI"]

for company in tech_companies:
    query_str = f'site:teamblind.com {company} (layoff OR promo OR comp OR "new grad" OR offer)'
    existing = db.query(SourceQuery).filter(
        SourceQuery.source_type == "blind",
        SourceQuery.query == query_str
    ).first()
    
    if not existing:
        new_query = SourceQuery(
            source_type="blind",
            query=query_str,
            site_domain="teamblind.com",
            city=None,
            enabled=True,
            interval_min=60
        )
        db.add(new_query)
        print(f"Added blind query: {company}")

db.commit()
print("\n✅ Queries updated successfully!")
print("\nNext steps:")
print("  1. Run: docker compose exec api python trigger_scheduler.py")
print("  2. Or wait for the scheduler to run automatically")

db.close()

