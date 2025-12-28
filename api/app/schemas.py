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
    published_at: Optional[datetime]
    views: int
    saves: int
    final_score: float

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
    start_at: Optional[datetime]
    end_at: Optional[datetime]
    city: Optional[str]
    category: Optional[str]
    terms: Optional[str]
    confidence: float

    class Config:
        from_attributes = True


class DigestResponse(BaseModel):
    id: int
    digest_date: datetime
    content_json: str
    created_at: datetime

    class Config:
        from_attributes = True

