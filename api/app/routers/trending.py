from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database import get_db
from app.models import Article, SourceType
from app.schemas import TrendingResponse, ArticleResponse
from typing import Optional

router = APIRouter()


@router.get("", response_model=TrendingResponse)
def get_trending(
    source_type: Optional[str] = Query(None, description="Source type: di_li, blind, or xhs"),
    city: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(Article).filter(Article.final_score > 0)
    
    if source_type:
        try:
            source_enum = SourceType(source_type)
            query = query.filter(Article.source_type == source_enum.value)
        except ValueError:
            pass
    
    if city:
        query = query.filter(Article.city_hints.ilike(f"%{city}%"))
    
    articles = query.order_by(desc(Article.final_score)).limit(limit).all()
    
    return TrendingResponse(
        articles=[ArticleResponse.model_validate(a) for a in articles],
        source_type=source_type or "all",
        total=len(articles)
    )

