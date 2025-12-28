#!/usr/bin/env python3
"""Check 1point3acres article content"""
from app.database import SessionLocal
from app.models import Article

db = SessionLocal()

articles = db.query(Article).filter(Article.source_type == 'di_li').limit(5).all()

print("=" * 60)
print(f"Checking {len(articles)} 1point3acres articles")
print("=" * 60)

for article in articles:
    print(f"\n{'='*60}")
    print(f"ID: {article.id}")
    print(f"Title: {article.title}")
    print(f"URL: {article.url[:80]}...")
    print(f"Content length: {len(article.cleaned_text) if article.cleaned_text else 0} characters")
    print(f"Summary: {article.summary[:100] if article.summary else 'None'}...")
    
    if article.cleaned_text:
        preview = article.cleaned_text[:500]
        print(f"\nContent preview:\n{preview}...")
        
        # Check for common issues
        if len(article.cleaned_text) < 200:
            print("⚠ WARNING: Content is very short!")
        if '登录' in article.cleaned_text or 'login' in article.cleaned_text.lower():
            print("⚠ WARNING: Contains login text!")
    else:
        print("\n⚠ ERROR: No content stored!")

print("\n" + "=" * 60)

