#!/usr/bin/env python3
"""Manually trigger the scheduler to fetch articles from all sources"""
from app.database import SessionLocal
from app.models import SourceQuery, Article
from app.scheduler import run_search_jobs

db = SessionLocal()

print("=" * 60)
print("Manually Triggering Scheduler")
print("=" * 60)

# Count articles before
count_before = db.query(Article).count()
print(f"\nArticles before: {count_before}")

# Get enabled queries
queries = db.query(SourceQuery).filter(SourceQuery.enabled == True).all()
print(f"\nEnabled queries: {len(queries)}")
for query in queries:
    print(f"  - {query.source_type}: {query.query}")

print("\n" + "-" * 60)
print("Running search jobs...")
print("-" * 60)

# Run the search jobs
try:
    run_search_jobs()
    print("\n✓ Search jobs completed")
except Exception as e:
    print(f"\n✗ Error running search jobs: {e}")

# Count articles after
count_after = db.query(Article).count()
print(f"\nArticles after: {count_after}")
print(f"New articles added: {count_after - count_before}")

# Show recent articles by source
if count_after > count_before:
    print("\n" + "-" * 60)
    print("Recent articles by source:")
    print("-" * 60)
    for source_type in ['di_li', 'blind']:
        recent = db.query(Article).filter(
            Article.source_type == source_type
        ).order_by(Article.id.desc()).limit(3).all()
        if recent:
            print(f"\n{source_type.upper()}:")
            for i, article in enumerate(recent, 1):
                print(f"  {i}. {article.title[:60]}...")

print("\n" + "=" * 60)
print("Done!")
print("=" * 60)

