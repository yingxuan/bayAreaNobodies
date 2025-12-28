from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Article
from app.auth import get_current_user
from app.models import User

router = APIRouter()


@router.post("/view")
def record_view(article_id: int, db: Session = Depends(get_db)):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found"
        )
    article.views += 1
    # Update engagement score (simple: views * 0.1 + saves * 1.0)
    article.engagement_score = article.views * 0.1 + article.saves * 1.0
    # Recalculate final score
    article.final_score = (
        0.45 * article.search_rank_score +
        0.35 * article.freshness_score +
        0.20 * article.engagement_score
    )
    db.commit()
    return {"status": "ok"}


@router.post("/save")
def record_save(
    article_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found"
        )
    article.saves += 1
    article.engagement_score = article.views * 0.1 + article.saves * 1.0
    article.final_score = (
        0.45 * article.search_rank_score +
        0.35 * article.freshness_score +
        0.20 * article.engagement_score
    )
    db.commit()
    return {"status": "ok"}

