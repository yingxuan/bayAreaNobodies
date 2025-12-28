#!/usr/bin/env python3
"""Check YouTube articles in food feed"""
import httpx
import json

API_URL = "http://localhost:8000"

print("=" * 60)
print("Checking YouTube Articles in Food Feed")
print("=" * 60)

try:
    response = httpx.get(f"{API_URL}/feeds/food?limit=50", timeout=10.0)
    response.raise_for_status()
    data = response.json()
    
    articles = data.get('articles', [])
    youtube_articles = [a for a in articles if a.get('platform') == 'youtube']
    
    print(f"\nTotal articles: {len(articles)}")
    print(f"YouTube articles: {len(youtube_articles)}")
    
    if youtube_articles:
        print("\nYouTube articles with video_id:")
        for i, article in enumerate(youtube_articles[:10], 1):
            video_id = article.get('video_id')
            title = article.get('title', 'No title')[:50]
            print(f"  {i}. {title}...")
            print(f"     Video ID: {video_id}")
            print(f"     Thumbnail: {article.get('thumbnail_url', 'None')}")
    else:
        print("\n⚠️  No YouTube articles found in feed!")
        print("\nChecking database directly...")
        
        # Check database
        from app.database import SessionLocal
        from app.models import Article
        from sqlalchemy import desc
        
        db = SessionLocal()
        youtube_db = db.query(Article).filter(
            Article.source_type == 'food_radar',
            Article.platform == 'youtube'
        ).order_by(desc(Article.fetched_at)).limit(5).all()
        
        if youtube_db:
            print(f"\nFound {len(youtube_db)} YouTube articles in database:")
            for a in youtube_db:
                print(f"  - {a.title[:50] if a.title else 'No title'}...")
                print(f"    Video ID: {a.video_id}")
                print(f"    Fetched at: {a.fetched_at}")
                print(f"    Final score: {a.final_score}")
        else:
            print("\n⚠️  No YouTube articles in database!")
        
        db.close()
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)

