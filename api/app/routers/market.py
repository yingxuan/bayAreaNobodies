"""
Market API endpoints for unified market snapshot
"""
from fastapi import APIRouter
from app.services.market_snapshot_service import fetch_market_snapshot

router = APIRouter()


@router.get("/snapshot")
def get_market_snapshot():
    """
    Get unified market snapshot with all banner KPIs:
    - S&P 500 price with 24h change
    - Gold price (USD per oz) with 24h change
    - BTC price (USD) with 24h change
    - Powerball jackpot (USD) with draw date
    - CA Jumbo 7/1 ARM rate (%) with week date
    - T-bill 3-month rate (%) (backward compatibility)
    
    Returns cached data with 15-minute TTL for full snapshot.
    Per-field TTLs:
    - S&P 500: 5 minutes
    - BTC/Gold: 10 minutes
    - Mortgage: 12 hours
    - Lottery: 30 minutes
    
    Per-field fallback to last-known-good values if a source fails.
    Fields marked with `stale: true` indicate cached/placeholder data.
    """
    return fetch_market_snapshot()

