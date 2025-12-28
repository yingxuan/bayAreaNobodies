#!/usr/bin/env python3
"""Check coupons in database"""
from app.database import SessionLocal
from app.models import Coupon

db = SessionLocal()

print("=" * 60)
print("Checking Coupons")
print("=" * 60)

count = db.query(Coupon).count()
print(f"\nTotal coupons in database: {count}")

if count > 0:
    recent = db.query(Coupon).order_by(Coupon.id.desc()).limit(10).all()
    print(f"\nRecent coupons:")
    for c in recent:
        print(f"  - ID {c.id}: {c.title[:60] if c.title else 'No title'}...")
        print(f"    City: {c.city}, Category: {c.category}, Confidence: {c.confidence}")
        print(f"    Code: {c.code}, URL: {c.source_url[:50] if c.source_url else 'None'}...")
else:
    print("\n⚠️  No coupons found!")
    print("→ Need to run coupon search scheduler")
    print("→ Run: docker compose exec api python trigger_scheduler.py")
    print("→ Or wait for automatic scheduler (runs daily at 6 AM)")

db.close()

