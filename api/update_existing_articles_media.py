#!/usr/bin/env python3
"""Update existing articles with video_id and thumbnail_url"""
from app.database import SessionLocal
from app.models import Article
from app.services.article_fetcher import extract_video_id, extract_thumbnail_url

db = SessionLocal()

print("=" * 60)
print("Updating Existing Articles with Media Info")
print("=" * 60)

# Get all articles that need updating (have platform but no video_id/thumbnail_url)
articles = db.query(Article).filter(
    Article.platform.in_(['youtube', 'tiktok', 'instagram']),
    Article.video_id.is_(None)
).all()

print(f"\nFound {len(articles)} articles to update\n")

updated = 0
for article in articles:
    try:
        video_id = extract_video_id(article.url, article.platform)
        thumbnail_url = extract_thumbnail_url(article.url, article.platform, video_id)
        
        if video_id or thumbnail_url:
            article.video_id = video_id
            article.thumbnail_url = thumbnail_url
            updated += 1
            if updated % 10 == 0:
                print(f"Updated {updated} articles...")
    except Exception as e:
        print(f"Error updating article {article.id}: {e}")

db.commit()
print(f"\n✓ Updated {updated} articles with media info")
print("=" * 60)

db.close()

