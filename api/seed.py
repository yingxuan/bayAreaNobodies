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
            SourceQuery(
                source_type="di_li",
                query="site:1point3acres.com (h1b OR layoff OR ng OR offer)",
                site_domain="1point3acres.com",
                city=None,
                enabled=True,
                interval_min=60
            ),
            SourceQuery(
                source_type="blind",
                query="site:teamblind.com (layoff OR promo OR comp OR \"new grad\")",
                site_domain="teamblind.com",
                city=None,
                enabled=True,
                interval_min=60
            ),
            SourceQuery(
                source_type="xhs",
                query="site:xiaohongshu.com (奶茶 OR boba OR 新开) (Sunnyvale OR Cupertino OR San Jose)",
                site_domain="xiaohongshu.com",
                city="Sunnyvale",
                enabled=True,
                interval_min=120
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

