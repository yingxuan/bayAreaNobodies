from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    preferred_city: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    email: str
    preferred_city: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ArticleResponse(BaseModel):
    id: int
    url: str
    title: Optional[str]
    summary: Optional[str]
    summary_bullets: Optional[str]
    tags: Optional[str]
    city_hints: Optional[str]
    company_tags: Optional[str]
    source_type: Optional[str]
    platform: Optional[str] = None  # youtube, tiktok, instagram, web
    video_id: Optional[str] = None  # Video ID for embedding
    thumbnail_url: Optional[str] = None  # Thumbnail image URL
    place_name: Optional[str] = None  # Extracted place/restaurant name (for food_radar)
    published_at: Optional[datetime]
    views: int
    saves: int
    final_score: float
    gossip_score: Optional[float] = None  # 老中八卦度 score

    class Config:
        from_attributes = True


class TrendingResponse(BaseModel):
    articles: List[ArticleResponse]
    source_type: str
    total: int


class HoldingCreate(BaseModel):
    ticker: str
    quantity: float
    cost_basis: float
    tags: Optional[str] = None


class AddPositionRequest(BaseModel):
    ticker: str
    quantity: float
    cost_basis_per_share: float


class ReducePositionRequest(BaseModel):
    ticker: str
    quantity: float


class HoldingResponse(BaseModel):
    id: int
    ticker: str
    quantity: float
    cost_basis: float
    tags: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class PortfolioSummary(BaseModel):
    total_cost: float
    total_value: float
    total_pnl: float
    total_pnl_percent: float
    holdings: List[dict]


class StockNewsItem(BaseModel):
    headline: str
    summary: str
    url: str
    published_at: Optional[datetime]
    source: str


class CouponResponse(BaseModel):
    id: int
    title: str
    code: Optional[str]
    source_url: Optional[str]
    image_url: Optional[str] = None  # Image URL for coupon/deal
    video_url: Optional[str] = None  # Video URL for coupon/deal
    start_at: Optional[datetime]
    end_at: Optional[datetime]
    city: Optional[str]
    category: Optional[str]
    terms: Optional[str]
    confidence: float
    chinese_friendliness_score: Optional[float] = None  # 老中友好度 score

    class Config:
        from_attributes = True


class DigestResponse(BaseModel):
    id: int
    digest_date: datetime
    content_json: str
    created_at: datetime

    class Config:
        from_attributes = True


class FoodRadarFeedResponse(BaseModel):
    articles: List[ArticleResponse]
    total: int
    filters: dict


class DealsFeedResponse(BaseModel):
    coupons: List[CouponResponse]
    total: int
    data_freshness: Optional[str] = None  # "fresh" or "stale_due_to_quota"
    usage_info: Optional[dict] = None
    filters: dict


class StockData(BaseModel):
    ticker: str
    current_price: Optional[float]
    change_percent: float
    change_amount: Optional[float] = None  # Daily change in dollars
    news: List[StockNewsItem]
    news_count: int
    financial_advice: Optional[str] = None  # Gemini AI financial advice
    error: Optional[str] = None


class WealthFeedResponse(BaseModel):
    articles: List[ArticleResponse]
    total: int
    updated_at: Optional[str] = None


class GossipFeedResponse(BaseModel):
    articles: List[ArticleResponse]
    total: int
    filters: dict

