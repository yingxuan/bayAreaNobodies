#!/usr/bin/env python3
"""Test media fields in articles"""
from app.database import SessionLocal
from app.models import Article

db = SessionLocal()

print("=" * 60)
print("Testing Media Fields")
print("=" * 60)

# Check YouTube articles
youtube = db.query(Article).filter(
    Article.platform == 'youtube',
    Article.video_id.isnot(None)
).first()

if youtube:
    print(f"\n✓ YouTube article found:")
    print(f"  Title: {youtube.title[:50] if youtube.title else 'No title'}...")
    print(f"  Video ID: {youtube.video_id}")
    print(f"  Thumbnail: {youtube.thumbnail_url}")
else:
    print("\n⚠️  No YouTube articles with video_id found")

# Check counts
youtube_count = db.query(Article).filter(
    Article.platform == 'youtube',
    Article.video_id.isnot(None)
).count()

tiktok_count = db.query(Article).filter(
    Article.platform == 'tiktok',
    Article.video_id.isnot(None)
).count()

instagram_count = db.query(Article).filter(
    Article.platform == 'instagram',
    Article.video_id.isnot(None)
).count()

print(f"\nArticles with media info:")
print(f"  YouTube: {youtube_count}")
print(f"  TikTok: {tiktok_count}")
print(f"  Instagram: {instagram_count}")

print("\n" + "=" * 60)

db.close()

