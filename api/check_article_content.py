#!/usr/bin/env python3
"""Check article content for login prompts"""
from app.database import SessionLocal
from app.models import Article

db = SessionLocal()

# Check for login prompts
login_keywords = ['登录', '需要 登录', '没有帐号', 'login', 'sign in', 'register']

articles = db.query(Article).filter(Article.source_type == 'di_li').limit(5).all()

print("=" * 60)
print("Checking 1point3acres Article Content")
print("=" * 60)

for article in articles:
    print(f"\nArticle ID: {article.id}")
    print(f"Title: {article.title[:60]}...")
    print(f"URL: {article.url[:80]}...")
    
    if article.cleaned_text:
        text_preview = article.cleaned_text[:300]
        print(f"Content preview: {text_preview}...")
        
        # Check for login prompts
        has_login_prompt = any(keyword in article.cleaned_text for keyword in login_keywords)
        if has_login_prompt:
            print("⚠ WARNING: Contains login prompt!")
    else:
        print("Content: None")

