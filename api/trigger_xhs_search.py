#!/usr/bin/env python3
"""Manually trigger xiaohongshu search"""
from app.database import SessionLocal
from app.models import SourceQuery, Article
from app.scheduler import process_search_query

db = SessionLocal()

# Get xiaohongshu query
query = db.query(SourceQuery).filter(SourceQuery.source_type == 'xhs').first()

if not query:
    print("❌ No xiaohongshu query found in database")
    exit(1)

print("=" * 60)
print("Triggering Xiaohongshu Search")
print("=" * 60)
print(f"Query ID: {query.id}")
print(f"Query: {query.query}")
print(f"Site Domain: {query.site_domain}")
print()

# Count articles before
count_before = db.query(Article).filter(Article.source_type == 'xhs').count()
print(f"Articles before: {count_before}")

# Process the query
print("\nProcessing search query...")
process_search_query(query, db)

# Count articles after
count_after = db.query(Article).filter(Article.source_type == 'xhs').count()
print(f"\nArticles after: {count_after}")
print(f"New articles added: {count_after - count_before}")

# Show recent articles
if count_after > count_before:
    print("\nRecent articles:")
    recent = db.query(Article).filter(Article.source_type == 'xhs').order_by(Article.id.desc()).limit(5).all()
    for i, article in enumerate(recent, 1):
        print(f"  {i}. {article.title[:60]}...")

print("\n" + "=" * 60)
print("Done!")
print("=" * 60)

