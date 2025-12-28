#!/usr/bin/env python3
"""
Diagnose and fix food feed issues
"""
from app.database import SessionLocal
from app.models import Article, SourceQuery
from app.scheduler import run_search_jobs, calculate_scores
from sqlalchemy import desc

db = SessionLocal()

print("=" * 60)
print("Food Feed Diagnostic and Fix")
print("=" * 60)

# 1. Check if food_radar queries exist and are enabled
print("\n1. Checking food_radar queries...")
queries = db.query(SourceQuery).filter(
    SourceQuery.source_type == "food_radar",
    SourceQuery.enabled == True
).all()

if not queries:
    print("   ⚠️  No enabled food_radar queries found!")
    print("   → Run: python seed.py or python update_queries.py")
else:
    print(f"   ✓ Found {len(queries)} enabled food_radar queries")
    for q in queries[:3]:  # Show first 3
        print(f"      - {q.query[:60]}...")

# 2. Check if food_radar articles exist
print("\n2. Checking food_radar articles...")
all_articles = db.query(Article).filter(
    Article.source_type == "food_radar"
).count()

articles_with_score = db.query(Article).filter(
    Article.source_type == "food_radar",
    Article.final_score > 0
).count()

print(f"   Total food_radar articles: {all_articles}")
print(f"   Articles with final_score > 0: {articles_with_score}")

if all_articles == 0:
    print("   ⚠️  No food_radar articles found!")
    print("   → Need to run scheduler to fetch articles")
    
    # 3. Try to fix articles with score 0
    print("\n3. Fixing articles with score 0...")
    articles_with_zero_score = db.query(Article).filter(
        Article.source_type == "food_radar",
        Article.final_score == 0
    ).all()
    
    if articles_with_zero_score:
        print(f"   Found {len(articles_with_zero_score)} articles with score 0")
        print("   Recalculating scores...")
        for article in articles_with_zero_score:
            # Use a default search rank if not available
            calculate_scores(article, search_rank=50, max_rank=100)
        db.commit()
        print(f"   ✓ Recalculated scores for {len(articles_with_zero_score)} articles")
    else:
        print("   No articles with score 0 found")
    
    # 4. Suggest running scheduler
    print("\n4. Next steps:")
    print("   → Run scheduler to fetch food_radar articles:")
    print("     python trigger_scheduler.py")
    print("   → Or wait for automatic scheduler (runs every hour)")
else:
    # Show recent articles
    recent = db.query(Article).filter(
        Article.source_type == "food_radar"
    ).order_by(desc(Article.fetched_at)).limit(5).all()
    
    print("\n   Recent articles:")
    for a in recent:
        print(f"      - {a.title[:60] if a.title else 'No title'}...")
        print(f"        Score: {a.final_score}, Platform: {a.platform}")

# 5. Check if we should trigger scheduler
if all_articles == 0 and queries:
    print("\n5. Triggering scheduler to fetch food_radar articles...")
    try:
        run_search_jobs()
        print("   ✓ Scheduler completed")
        
        # Check again
        new_count = db.query(Article).filter(
            Article.source_type == "food_radar"
        ).count()
        print(f"   New food_radar articles: {new_count}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 60)
print("Done!")
print("=" * 60)

db.close()

