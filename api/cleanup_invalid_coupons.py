#!/usr/bin/env python3
"""Clean up invalid coupons"""
from app.database import SessionLocal
from app.models import Coupon

db = SessionLocal()

print("=" * 60)
print("Cleaning Up Invalid Coupons")
print("=" * 60)

# Remove coupons that are not from dealmoon or dealnews
invalid = db.query(Coupon).filter(
    ~Coupon.source_url.ilike('%dealmoon.com%'),
    ~Coupon.source_url.ilike('%dealnews.com%')
).all()

print(f"\nFound {len(invalid)} invalid coupons (not from dealmoon/dealnews)")

for coupon in invalid:
    print(f"  Deleting: {coupon.title[:50]}... (URL: {coupon.source_url[:50] if coupon.source_url else 'None'}...)")
    db.delete(coupon)

db.commit()
print(f"\n✓ Deleted {len(invalid)} invalid coupons")

# Check remaining
remaining = db.query(Coupon).count()
print(f"Remaining coupons: {remaining}")

db.close()

