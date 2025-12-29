"""
Risk API endpoints for daily reminders
"""
from fastapi import APIRouter, Query, HTTPException
from app.services.risk_service import fetch_risk_today

router = APIRouter()


@router.get("/today")
def get_risk_today(
    city: str = Query(default="cupertino", description="City name (e.g., cupertino, sunnyvale)")
):
    """
    Get today's risk reminders for Bay Area engineers
    
    Returns:
    - Gemini-generated reminders (if available)
    - Cached reminders (if within TTL)
    - Mock seed reminders (fallback)
    
    All responses include disclaimer and dataSource field.
    """
    try:
        return fetch_risk_today(city=city)
    except Exception as e:
        # Never return 500, always fallback to mock
        print(f"Error in /risk/today: {e}")
        from datetime import datetime
        import pytz
        today = datetime.now(pytz.UTC)
        from app.services.risk_service import get_daily_mock_seeds
        
        return {
            "updatedAt": today.isoformat(),
            "dataSource": "mock",
            "stale": True,
            "ttlSeconds": 43200,
            "items": get_daily_mock_seeds(),
            "disclaimer": "本信息仅供参考，不构成税务、投资或法律建议。请咨询专业人士获取个性化建议。"
        }

