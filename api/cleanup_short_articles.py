#!/usr/bin/env python3
"""Clean up articles with very short content"""
from app.database import SessionLocal
from app.models import Article
from sqlalchemy import func

db = SessionLocal()

print("=" * 60)
print("Cleaning up articles with short content")
print("=" * 60)

# Find articles with content < 500 chars
short_articles = db.query(Article).filter(
    Article.source_type == 'di_li',
    Article.cleaned_text != None,
    func.length(Article.cleaned_text) < 500
).all()

print(f"Found {len(short_articles)} articles with content < 500 chars")

for article in short_articles:
    print(f"  Deleting: {article.id} - {article.title[:50]}... ({len(article.cleaned_text) if article.cleaned_text else 0} chars)")
    db.delete(article)

db.commit()
print(f"\nDeleted {len(short_articles)} short articles")
print(f"Remaining di_li articles: {db.query(Article).filter(Article.source_type == 'di_li').count()}")

