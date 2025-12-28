from fastapi import APIRouter, Depends, Query
from app.schemas import StockNewsItem
from app.services.stock_service import get_stock_news
from typing import List

router = APIRouter()


@router.get("/news", response_model=List[StockNewsItem])
def get_stock_news_endpoint(
    ticker: str = Query(..., description="Stock ticker symbol"),
    range_hours: int = Query(24, ge=1, le=168, description="Time range in hours")
):
    return get_stock_news(ticker, range_hours)

