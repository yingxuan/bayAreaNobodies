"""
Market API endpoints for unified market snapshot
"""
from fastapi import APIRouter
from app.services.market_snapshot_service import fetch_market_snapshot

router = APIRouter()


@router.get("/snapshot")
def get_market_snapshot():
    """
    Get unified market snapshot with all 5 banner KPIs:
    - Gold price (USD per oz)
    - BTC price (USD)
    - Powerball jackpot (USD)
    - CA Jumbo 7/1 ARM rate (%)
    - T-bill 3-month rate (%)
    
    Returns cached data with 15-minute TTL.
    Per-field fallback to last-known-good values if a source fails.
    """
    return fetch_market_snapshot()

