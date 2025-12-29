"""
Risk API endpoints for daily reminders
"""
from fastapi import APIRouter, Query, HTTPException
from app.services.risk_service import fetch_risk_today, fetch_today_actions

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


@router.get("/today-actions")
def get_today_actions(
    city: str = Query(default="cupertino", description="City name (e.g., cupertino, sunnyvale)")
):
    """
    Get today's actions (今日必做 3 件事) for Bay Area engineers
    
    Returns:
    - Gemini-generated actions (if available)
    - Cached actions (if within TTL)
    - Mock actions (fallback)
    
    All responses include disclaimer and dataSource field.
    Never returns 500.
    """
    try:
        return fetch_today_actions(city=city)
    except Exception as e:
        # Never return 500, always fallback to mock
        print(f"Error in /risk/today-actions: {e}")
        import traceback
        traceback.print_exc()
        from datetime import datetime
        import pytz
        today = datetime.now(pytz.UTC)
        date_str = today.strftime("%Y-%m-%d")
        from app.services.risk_service import get_mock_actions_response
        
        return get_mock_actions_response(city, date_str)

