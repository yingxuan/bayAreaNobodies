#!/usr/bin/env python3
"""Seed sample articles for testing"""
from app.database import SessionLocal
from app.models import Article
from datetime import datetime
import hashlib
import json
import pytz

db = SessionLocal()

# Create sample 1point3acres articles
sample_articles = [
    {
        'url': 'https://www.1point3acres.com/bbs/thread-123456-1-1.html',
        'title': '2024 H1B抽签结果讨论 - 今年中签率如何？',
        'summary': '讨论2024年H1B抽签结果，分享中签经验和时间线。',
        'cleaned_text': '2024年H1B抽签已经结束，很多同学在等待结果。今年中签率似乎比去年略高。大家来分享一下自己的情况。',
        'source_type': 'di_li',
        'published_at': datetime.now(pytz.UTC),
        'company_tags': ['Google', 'Meta'],
        'city_hints': ['Sunnyvale', 'San Jose'],
        'tags': ['h1b', 'offer'],
        'summary_bullets': [
            '2024 H1B抽签结果陆续公布',
            '中签率相比去年略有提升',
            '建议尽早准备材料'
        ]
    },
    {
        'url': 'https://www.1point3acres.com/bbs/thread-123457-1-1.html',
        'title': 'Meta新一轮layoff - 哪些组受影响？',
        'summary': 'Meta宣布新一轮裁员，讨论哪些组和职位受影响最大。',
        'cleaned_text': 'Meta今天宣布了新一轮裁员计划，预计影响多个部门。Engineering和Product组都有影响。',
        'source_type': 'di_li',
        'published_at': datetime.now(pytz.UTC),
        'company_tags': ['Meta'],
        'city_hints': ['Menlo Park', 'San Francisco'],
        'tags': ['layoff'],
        'summary_bullets': [
            'Meta宣布新一轮裁员',
            'Engineering和Product组受影响',
            '建议关注内部转组机会'
        ]
    },
    {
        'url': 'https://www.1point3acres.com/bbs/thread-123458-1-1.html',
        'title': 'New Grad 2024求职经验分享 - 如何准备面试',
        'summary': '分享2024年new grad求职经验，包括简历准备、面试技巧等。',
        'cleaned_text': '作为2024年new grad，分享一下我的求职经验。简历很重要，要突出项目经验。面试时要多练习算法题。',
        'source_type': 'di_li',
        'published_at': datetime.now(pytz.UTC),
        'company_tags': ['Google', 'Amazon', 'Microsoft'],
        'city_hints': ['Mountain View', 'Seattle'],
        'tags': ['new grad', 'interview'],
        'summary_bullets': [
            'New grad求职竞争激烈',
            '简历要突出项目经验',
            '算法题练习很重要'
        ]
    },
    {
        'url': 'https://www.1point3acres.com/bbs/thread-123459-1-1.html',
        'title': 'Google L4 offer negotiation经验 - 如何争取更好的package',
        'summary': '分享Google L4 offer negotiation的经验和技巧。',
        'cleaned_text': '最近收到了Google L4的offer，分享一下negotiation的经验。最重要的是要有competing offers。',
        'source_type': 'di_li',
        'published_at': datetime.now(pytz.UTC),
        'company_tags': ['Google'],
        'city_hints': ['Mountain View'],
        'tags': ['offer', 'comp'],
        'summary_bullets': [
            'Google L4 offer negotiation',
            '需要有competing offers',
            '可以negotiate base和equity'
        ]
    },
    {
        'url': 'https://www.1point3acres.com/bbs/thread-123460-1-1.html',
        'title': 'Amazon SDE2面试经验 - 系统设计重点',
        'summary': '分享Amazon SDE2面试经验，重点讲解系统设计部分。',
        'cleaned_text': '刚面完Amazon SDE2，分享一下经验。系统设计部分很重要，要准备scalability和availability。',
        'source_type': 'di_li',
        'published_at': datetime.now(pytz.UTC),
        'company_tags': ['Amazon'],
        'city_hints': ['Seattle'],
        'tags': ['interview', 'offer'],
        'summary_bullets': [
            'Amazon SDE2面试重点',
            '系统设计要准备scalability',
            'Leadership Principles很重要'
        ]
    }
]

count = 0
for article_data in sample_articles:
    # Compute content hash
    content_hash = hashlib.sha256((article_data['title'] + article_data['cleaned_text'][:2000]).encode()).hexdigest()
    
    # Check if already exists
    existing = db.query(Article).filter(Article.content_hash == content_hash).first()
    if existing:
        continue
    
    article = Article(
        url=article_data['url'],
        normalized_url=article_data['url'],
        title=article_data['title'],
        cleaned_text=article_data['cleaned_text'],
        content_hash=content_hash,
        source_type=article_data['source_type'],
        published_at=article_data['published_at'],
        summary=article_data['summary'],
        summary_bullets=json.dumps(article_data['summary_bullets']),
        company_tags=json.dumps(article_data['company_tags']),
        city_hints=json.dumps(article_data['city_hints']),
        tags=json.dumps(article_data['tags']),
        views=0,
        saves=0,
        engagement_score=0.0,
        freshness_score=1.0,
        search_rank_score=0.8,
        final_score=0.8
    )
    db.add(article)
    count += 1

db.commit()
print(f'Created {count} sample articles for 1point3acres')

if __name__ == "__main__":
    pass

