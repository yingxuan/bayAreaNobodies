#!/usr/bin/env python3
"""Clean up articles with login prompts"""
from app.database import SessionLocal
from app.models import Article

db = SessionLocal()

# Login indicators
login_indicators = ['您需要 登录', '需要 登录', '没有帐号', '登录 才可以', 'login required', 'please log in']

print("=" * 60)
print("Cleaning up articles with login prompts")
print("=" * 60)

articles = db.query(Article).all()
print(f"Total articles: {len(articles)}")

deleted_count = 0
for article in articles:
    if article.cleaned_text:
        # Check if login prompt is significant
        has_login = any(indicator in article.cleaned_text for indicator in login_indicators)
        if has_login:
            # Check if it's mostly login prompt
            login_portion = sum(len(ind) for ind in login_indicators if ind in article.cleaned_text)
            if len(article.cleaned_text) < 500 or login_portion > len(article.cleaned_text) * 0.2:
                print(f"Deleting article {article.id}: {article.title[:50]}...")
                db.delete(article)
                deleted_count += 1

db.commit()
print(f"\nDeleted {deleted_count} articles with login prompts")
print(f"Remaining articles: {db.query(Article).count()}")

