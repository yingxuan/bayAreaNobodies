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

# Create sample teamblind articles
blind_articles = [
    {
        'url': 'https://www.teamblind.com/post/layoff-2024-abc123',
        'title': 'Another round of layoffs at Meta - which teams are affected?',
        'summary': 'Discussion about Meta layoffs and which teams/roles are most impacted.',
        'cleaned_text': 'Meta just announced another round of layoffs. Engineering teams seem to be hit hard, especially in some product areas. Anyone know which specific teams are affected?',
        'source_type': 'blind',
        'published_at': datetime.now(pytz.UTC),
        'company_tags': ['Meta'],
        'city_hints': ['Menlo Park', 'San Francisco'],
        'tags': ['layoff'],
        'summary_bullets': [
            'Meta announces new layoff round',
            'Engineering teams heavily affected',
            'Product areas also impacted'
        ]
    },
    {
        'url': 'https://www.teamblind.com/post/comp-2024-xyz789',
        'title': 'Google L5 TC breakdown - is this competitive?',
        'summary': 'Sharing Google L5 total compensation breakdown and asking for market comparison.',
        'cleaned_text': 'Just got a Google L5 offer. Base: 250k, Equity: 400k over 4 years, Bonus: 20%. Total comp around 370k first year. Is this competitive for 2024?',
        'source_type': 'blind',
        'published_at': datetime.now(pytz.UTC),
        'company_tags': ['Google'],
        'city_hints': ['Mountain View'],
        'tags': ['comp', 'offer'],
        'summary_bullets': [
            'Google L5 offer breakdown',
            'Total comp ~370k first year',
            'Asking for market comparison'
        ]
    },
    {
        'url': 'https://www.teamblind.com/post/new-grad-2024-def456',
        'title': 'New grad 2024 - how is the job market?',
        'summary': 'Discussion about the 2024 new grad job market and interview experiences.',
        'cleaned_text': 'New grad here looking for jobs in 2024. Market seems tough. Getting interviews but competition is fierce. Anyone else experiencing this?',
        'source_type': 'blind',
        'published_at': datetime.now(pytz.UTC),
        'company_tags': ['Google', 'Meta', 'Amazon'],
        'city_hints': ['Mountain View', 'Seattle'],
        'tags': ['new grad', 'interview'],
        'summary_bullets': [
            '2024 new grad job market discussion',
            'Tough competition for roles',
            'Getting interviews but hard to convert'
        ]
    },
    {
        'url': 'https://www.teamblind.com/post/promo-2024-ghi789',
        'title': 'Promo promo promo - how to get promoted at FAANG?',
        'summary': 'Tips and strategies for getting promoted at FAANG companies.',
        'cleaned_text': 'Looking to get promoted from L4 to L5. What are the key things to focus on? Impact, scope, leadership? Any tips from those who recently got promoted?',
        'source_type': 'blind',
        'published_at': datetime.now(pytz.UTC),
        'company_tags': ['Google', 'Meta', 'Amazon'],
        'city_hints': ['Mountain View', 'Seattle'],
        'tags': ['promo', 'career'],
        'summary_bullets': [
            'Promotion strategies at FAANG',
            'Focus on impact and scope',
            'Leadership is key for L4 to L5'
        ]
    },
    {
        'url': 'https://www.teamblind.com/post/offer-2024-jkl012',
        'title': 'Amazon vs Google offer - which should I take?',
        'summary': 'Comparing Amazon and Google offers and asking for advice on which to choose.',
        'cleaned_text': 'Got offers from both Amazon and Google. Amazon: L5, 380k TC. Google: L4, 350k TC. Amazon team seems more interesting but Google has better WLB. What would you choose?',
        'source_type': 'blind',
        'published_at': datetime.now(pytz.UTC),
        'company_tags': ['Amazon', 'Google'],
        'city_hints': ['Seattle', 'Mountain View'],
        'tags': ['offer', 'comp'],
        'summary_bullets': [
            'Comparing Amazon L5 vs Google L4',
            'Amazon: 380k TC, interesting team',
            'Google: 350k TC, better WLB'
        ]
    }
]

blind_count = 0
for article_data in blind_articles:
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
    blind_count += 1

db.commit()
print(f'Created {blind_count} sample articles for teamblind')

# Create sample xiaohongshu articles
xhs_articles = [
    {
        'url': 'https://www.xiaohongshu.com/explore/1234567890abcdef',
        'title': '湾区新开的奶茶店！Sunnyvale这家boba绝了 🧋',
        'summary': '分享Sunnyvale新开的奶茶店，推荐几款好喝的boba。',
        'cleaned_text': '今天在Sunnyvale发现了一家新开的奶茶店！他们家的boba真的太好喝了。推荐招牌奶茶和芒果冰沙，甜度刚刚好。位置在El Camino Real上，停车很方便。',
        'source_type': 'xhs',
        'published_at': datetime.now(pytz.UTC),
        'company_tags': [],
        'city_hints': ['Sunnyvale'],
        'tags': ['boba', '奶茶', '新开'],
        'summary_bullets': [
            'Sunnyvale新开奶茶店',
            '推荐招牌奶茶和芒果冰沙',
            '位置在El Camino Real'
        ]
    },
    {
        'url': 'https://www.xiaohongshu.com/explore/2345678901bcdefg',
        'title': 'Cupertino美食探店 | 这家餐厅的性价比太高了！',
        'summary': '分享Cupertino一家性价比很高的餐厅，适合日常用餐。',
        'cleaned_text': '在Cupertino发现了一家性价比超高的餐厅！人均$20左右，分量很足，味道也不错。推荐他们的招牌面和炒饭。环境干净，服务态度也很好。',
        'source_type': 'xhs',
        'published_at': datetime.now(pytz.UTC),
        'company_tags': [],
        'city_hints': ['Cupertino'],
        'tags': ['美食', '探店', '餐厅'],
        'summary_bullets': [
            'Cupertino性价比餐厅',
            '人均$20左右',
            '推荐招牌面和炒饭'
        ]
    },
    {
        'url': 'https://www.xiaohongshu.com/explore/3456789012cdefgh',
        'title': 'San Jose周末好去处 | 这家咖啡店太适合工作了 ☕',
        'summary': '推荐San Jose一家适合工作的咖啡店，环境安静，WiFi稳定。',
        'cleaned_text': '周末在San Jose找到了一家超适合工作的咖啡店！环境很安静，WiFi速度很快，座位也很舒服。咖啡味道不错，价格也合理。适合需要安静环境工作或学习的朋友。',
        'source_type': 'xhs',
        'published_at': datetime.now(pytz.UTC),
        'company_tags': [],
        'city_hints': ['San Jose'],
        'tags': ['咖啡', '工作', '周末'],
        'summary_bullets': [
            'San Jose适合工作的咖啡店',
            '环境安静，WiFi稳定',
            '适合学习和工作'
        ]
    },
    {
        'url': 'https://www.xiaohongshu.com/explore/4567890123defghi',
        'title': '湾区新开的日料店 | Cupertino这家值得一试 🍣',
        'summary': '分享Cupertino新开的日料店，食材新鲜，价格合理。',
        'cleaned_text': 'Cupertino新开了一家日料店，今天去试了一下，真的很不错！食材很新鲜，三文鱼和tuna都很棒。价格也比较合理，人均$30-40。环境装修很有日式风格，服务也很周到。',
        'source_type': 'xhs',
        'published_at': datetime.now(pytz.UTC),
        'company_tags': [],
        'city_hints': ['Cupertino'],
        'tags': ['日料', '新开', '美食'],
        'summary_bullets': [
            'Cupertino新开日料店',
            '食材新鲜，价格合理',
            '人均$30-40'
        ]
    },
    {
        'url': 'https://www.xiaohongshu.com/explore/5678901234efghij',
        'title': 'Sunnyvale周末好去处 | 这家甜品店太治愈了 🍰',
        'summary': '推荐Sunnyvale一家甜品店，适合周末放松。',
        'cleaned_text': '周末在Sunnyvale发现了一家超治愈的甜品店！他们家的蛋糕和提拉米苏都很好吃，不会太甜。环境很温馨，适合和朋友聊天或者一个人放松。价格也还可以，一块蛋糕$8-12。',
        'source_type': 'xhs',
        'published_at': datetime.now(pytz.UTC),
        'company_tags': [],
        'city_hints': ['Sunnyvale'],
        'tags': ['甜品', '周末', '治愈'],
        'summary_bullets': [
            'Sunnyvale甜品店推荐',
            '蛋糕和提拉米苏不错',
            '适合周末放松'
        ]
    },
    {
        'url': 'https://www.xiaohongshu.com/explore/6789012345fghijk',
        'title': '湾区生活 | San Jose这家超市的亚洲食材很全 🛒',
        'summary': '分享San Jose一家亚洲超市，食材种类很丰富。',
        'cleaned_text': '在San Jose找到了一家亚洲超市，食材真的很全！各种调料、蔬菜、肉类都有，价格也比较合理。特别推荐他们的冷冻区和调料区，很多国内常见的食材都能找到。',
        'source_type': 'xhs',
        'published_at': datetime.now(pytz.UTC),
        'company_tags': [],
        'city_hints': ['San Jose'],
        'tags': ['超市', '亚洲食材', '生活'],
        'summary_bullets': [
            'San Jose亚洲超市',
            '食材种类丰富',
            '价格合理'
        ]
    }
]

xhs_count = 0
for article_data in xhs_articles:
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
    xhs_count += 1

db.commit()
print(f'Created {xhs_count} sample articles for xiaohongshu')

if __name__ == "__main__":
    pass

