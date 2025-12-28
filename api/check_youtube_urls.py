#!/usr/bin/env python3
"""Check YouTube URLs and why video_id extraction fails"""
from app.database import SessionLocal
from app.models import Article
from app.services.article_fetcher import extract_video_id, extract_thumbnail_url
from sqlalchemy import desc

db = SessionLocal()

print("=" * 60)
print("Checking YouTube URLs")
print("=" * 60)

# Get YouTube articles without video_id
articles = db.query(Article).filter(
    Article.source_type == 'food_radar',
    Article.platform == 'youtube',
    Article.video_id.is_(None)
).order_by(desc(Article.fetched_at)).limit(10).all()

print(f"\nFound {len(articles)} YouTube articles without video_id\n")

for i, article in enumerate(articles, 1):
    print(f"{i}. {article.title[:50] if article.title else 'No title'}...")
    print(f"   URL: {article.url}")
    
    # Try to extract video_id
    video_id = extract_video_id(article.url, 'youtube')
    thumbnail_url = extract_thumbnail_url(article.url, 'youtube', video_id)
    
    print(f"   Extracted video_id: {video_id}")
    print(f"   Extracted thumbnail: {thumbnail_url}")
    
    # Check if it's a channel or playlist URL
    if '/channel/' in article.url or '/c/' in article.url or '/user/' in article.url or '/@' in article.url:
        print(f"   ⚠️  This is a channel/profile URL, not a video URL")
    elif '/playlist' in article.url:
        print(f"   ⚠️  This is a playlist URL, not a video URL")
    elif '/watch' not in article.url and 'youtu.be' not in article.url:
        print(f"   ⚠️  URL format not recognized")
    
    print()

# Also check articles WITH video_id
articles_with_id = db.query(Article).filter(
    Article.source_type == 'food_radar',
    Article.platform == 'youtube',
    Article.video_id.isnot(None)
).order_by(desc(Article.fetched_at)).limit(5).all()

print(f"\n{'='*60}")
print(f"Articles WITH video_id: {len(articles_with_id)}")
print(f"{'='*60}\n")

for i, article in enumerate(articles_with_id, 1):
    print(f"{i}. {article.title[:50] if article.title else 'No title'}...")
    print(f"   URL: {article.url}")
    print(f"   Video ID: {article.video_id}")
    print(f"   Thumbnail: {article.thumbnail_url}")
    print()

db.close()

