from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database import get_db
from app.models import Coupon
from app.schemas import CouponResponse
from typing import Optional

router = APIRouter()


@router.get("", response_model=list[CouponResponse])
def get_coupons(
    city: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(Coupon)
    
    if city:
        query = query.filter(Coupon.city.ilike(f"%{city}%"))
    
    if category:
        query = query.filter(Coupon.category == category)
    
    coupons = query.order_by(desc(Coupon.confidence), desc(Coupon.created_at)).limit(limit).all()
    return coupons

