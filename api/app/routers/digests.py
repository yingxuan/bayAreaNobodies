from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database import get_db
from app.models import Digest
from app.schemas import DigestResponse
from app.auth import get_current_user
from app.models import User
from datetime import datetime, date

router = APIRouter()


@router.get("/today", response_model=DigestResponse)
def get_today_digest(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    today = datetime.now().date()
    digest = db.query(Digest).filter(
        Digest.user_id == current_user.id,
        Digest.digest_date >= datetime.combine(today, datetime.min.time()),
        Digest.digest_date < datetime.combine(today, datetime.max.time())
    ).order_by(desc(Digest.created_at)).first()
    
    if not digest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No digest found for today"
        )
    
    return digest

