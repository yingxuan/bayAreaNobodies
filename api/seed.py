from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import SourceQuery

def seed_queries():
    """Seed default search queries"""
    db = SessionLocal()
    try:
        # Check if queries already exist
        existing = db.query(SourceQuery).first()
        if existing:
            print("Queries already seeded, skipping")
            return
        
        queries = [
            # Gossip feed: 1point3acres.com
            SourceQuery(
                source_type="di_li",
                query="site:1point3acres.com (h1b OR layoff OR ng OR offer)",
                site_domain="1point3acres.com",
                city=None,
                enabled=True,
                interval_min=60
            ),
            # Gossip feed: huaren.us
            SourceQuery(
                source_type="di_li",
                query="site:huaren.us (h1b OR layoff OR ng OR offer)",
                site_domain="huaren.us",
                city=None,
                enabled=True,
                interval_min=60
            ),
            # Gossip feed: teamblind.com
            SourceQuery(
                source_type="blind",
                query="site:teamblind.com (layoff OR promo OR comp OR \"new grad\" OR offer)",
                site_domain="teamblind.com",
                city=None,
                enabled=True,
                interval_min=60
            ),
            # Food feed: YouTube Chinese food bloggers (探店博主) only
            SourceQuery(
                source_type="food_radar",
                query="site:youtube.com 探店 湾区 中餐",
                site_domain="youtube.com",
                city=None,
                enabled=True,
                interval_min=180
            ),
            SourceQuery(
                source_type="food_radar",
                query="site:youtube.com 美食 湾区 火锅 奶茶",
                site_domain="youtube.com",
                city=None,
                enabled=True,
                interval_min=180
            ),
            # Food feed: 1point3acres.com popular food posts in Bay Area
            SourceQuery(
                source_type="food_radar",
                query="site:1point3acres.com (湾区 OR \"Bay Area\" OR \"San Francisco\" OR \"San Jose\") (美食 OR 中餐 OR 火锅 OR 奶茶 OR food OR restaurant)",
                site_domain="1point3acres.com",
                city=None,
                enabled=True,
                interval_min=180
            ),
            # Food feed: huaren.us popular food posts in Bay Area
            SourceQuery(
                source_type="food_radar",
                query="site:huaren.us (湾区 OR \"Bay Area\" OR \"San Francisco\" OR \"San Jose\") (美食 OR 中餐 OR 火锅 OR 奶茶 OR food OR restaurant)",
                site_domain="huaren.us",
                city=None,
                enabled=True,
                interval_min=180
            ),
        ]
        
        for query in queries:
            db.add(query)
        
        db.commit()
        print(f"Seeded {len(queries)} search queries")
    except Exception as e:
        print(f"Error seeding queries: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_queries()

