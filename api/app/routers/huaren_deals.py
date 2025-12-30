"""
Huaren Deals API endpoints
"""
from fastapi import APIRouter, Query
from app.services.huaren_deals_service import fetch_huaren_deals

router = APIRouter()


@router.get("/huaren")
def get_huaren_deals(
    limit: int = Query(default=30, ge=1, le=100, description="Number of deals to return")
):
    """
    Get deals from Huaren.us forum (forumid=395)
    
    Returns:
    - Parsed forum threads mapped to deal model
    - Cached results (if within TTL)
    - Empty list on error (graceful fallback)
    
    Never returns 500.
    """
    try:
        deals = fetch_huaren_deals(limit=limit)
        return {
            "items": deals,
            "total": len(deals),
            "source": "huaren_forum_395"
        }
    except Exception as e:
        print(f"Error in /deals/huaren: {e}")
        import traceback
        traceback.print_exc()
        # Return empty list on error (graceful fallback)
        return {
            "items": [],
            "total": 0,
            "source": "huaren_forum_395",
            "error": "Failed to fetch deals"
        }

