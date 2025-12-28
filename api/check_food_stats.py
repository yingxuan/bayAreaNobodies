#!/usr/bin/env python3
"""Check food_radar article statistics"""
from app.database import SessionLocal
from app.models import Article
from sqlalchemy import func

db = SessionLocal()

print("=" * 60)
print("Food Radar Article Statistics")
print("=" * 60)

# Total count
total = db.query(Article).filter(Article.source_type == 'food_radar').count()
print(f"\nTotal food_radar articles: {total}")

# By platform
print("\nBy platform:")
by_platform = db.query(
    Article.platform,
    func.count(Article.id).label('count')
).filter(
    Article.source_type == 'food_radar'
).group_by(Article.platform).all()

for platform, count in by_platform:
    print(f"  {platform or 'unknown'}: {count}")

# By score
print("\nBy score range:")
high_score = db.query(Article).filter(
    Article.source_type == 'food_radar',
    Article.final_score > 0.5
).count()
medium_score = db.query(Article).filter(
    Article.source_type == 'food_radar',
    Article.final_score > 0.2,
    Article.final_score <= 0.5
).count()
low_score = db.query(Article).filter(
    Article.source_type == 'food_radar',
    Article.final_score > 0,
    Article.final_score <= 0.2
).count()
zero_score = db.query(Article).filter(
    Article.source_type == 'food_radar',
    Article.final_score == 0
).count()

print(f"  High (>0.5): {high_score}")
print(f"  Medium (0.2-0.5): {medium_score}")
print(f"  Low (0-0.2): {low_score}")
print(f"  Zero: {zero_score}")

# Recent articles
print("\nRecent articles (last 5):")
recent = db.query(Article).filter(
    Article.source_type == 'food_radar'
).order_by(Article.id.desc()).limit(5).all()

for a in recent:
    print(f"  - {a.title[:60] if a.title else 'No title'}...")
    print(f"    Platform: {a.platform}, Score: {a.final_score:.3f}")

print("\n" + "=" * 60)

db.close()

