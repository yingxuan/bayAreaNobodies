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
    source_type: Optional[str] = Query(None, description="Source type: di_li or blind"),
    city: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    from sqlalchemy import not_, or_
    
    # Filter out sample articles by URL patterns
    sample_patterns = [
        Article.url.like('%thread-123%'),
        Article.url.like('%post/layoff-2024%'),
        Article.url.like('%post/comp-2024%'),
        Article.url.like('%post/new-grad-2024%'),
        Article.url.like('%post/promo-2024%'),
        Article.url.like('%post/offer-2024%'),
        Article.url.like('%example.com%'),
    ]
    
    query = db.query(Article).filter(
        Article.final_score > 0,
        not_(or_(*sample_patterns))  # Exclude sample articles
    )
    
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

