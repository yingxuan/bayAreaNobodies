from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum
from datetime import datetime


class SourceType(str, enum.Enum):
    DI_LI = "di_li"
    BLIND = "blind"
    XHS = "xhs"


class SourceQuery(Base):
    __tablename__ = "source_queries"

    id = Column(Integer, primary_key=True, index=True)
    source_type = Column(String, nullable=False, index=True)
    query = Column(Text, nullable=False)
    site_domain = Column(String, nullable=True)
    city = Column(String, nullable=True)
    enabled = Column(Boolean, default=True)
    interval_min = Column(Integer, default=60)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class SearchResultRaw(Base):
    __tablename__ = "search_results_raw"

    id = Column(Integer, primary_key=True, index=True)
    query_id = Column(Integer, ForeignKey("source_queries.id"))
    url = Column(Text, nullable=False)
    title = Column(Text, nullable=True)
    snippet = Column(Text, nullable=True)
    raw_json = Column(Text, nullable=True)
    search_rank = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    query = relationship("SourceQuery")


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(Text, nullable=False, unique=True, index=True)
    normalized_url = Column(Text, nullable=False, index=True)
    title = Column(Text, nullable=True)
    cleaned_text = Column(Text, nullable=True)
    content_hash = Column(String(64), nullable=False, unique=True, index=True)
    source_type = Column(String, nullable=True, index=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    fetched_at = Column(DateTime(timezone=True), server_default=func.now())
    summary = Column(Text, nullable=True)
    summary_bullets = Column(Text, nullable=True)
    tags = Column(Text, nullable=True)  # JSON array as string
    city_hints = Column(Text, nullable=True)  # JSON array as string
    company_tags = Column(Text, nullable=True)  # JSON array as string
    views = Column(Integer, default=0)
    saves = Column(Integer, default=0)
    engagement_score = Column(Float, default=0.0)
    freshness_score = Column(Float, default=0.0)
    search_rank_score = Column(Float, default=0.0)
    final_score = Column(Float, default=0.0, index=True)

    __table_args__ = (
        Index('idx_articles_source_score', 'source_type', 'final_score'),
    )


class TrendingSnapshot(Base):
    __tablename__ = "trending_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    source_type = Column(String, nullable=False, index=True)
    article_id = Column(Integer, ForeignKey("articles.id"))
    rank = Column(Integer, nullable=False)
    snapshot_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    article = relationship("Article")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    preferred_city = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Holding(Base):
    __tablename__ = "holdings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ticker = Column(String, nullable=False, index=True)
    quantity = Column(Float, nullable=False)
    cost_basis = Column(Float, nullable=False)
    tags = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User")


class Coupon(Base):
    __tablename__ = "coupons"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(Text, nullable=False)
    code = Column(String, nullable=True)
    source_url = Column(Text, nullable=True)
    start_at = Column(DateTime(timezone=True), nullable=True)
    end_at = Column(DateTime(timezone=True), nullable=True)
    city = Column(String, nullable=True, index=True)
    category = Column(String, nullable=True, index=True)
    terms = Column(Text, nullable=True)
    confidence = Column(Float, default=0.5)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Digest(Base):
    __tablename__ = "digests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    digest_date = Column(DateTime(timezone=True), nullable=False, index=True)
    content_json = Column(Text, nullable=False)  # JSON string
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")

