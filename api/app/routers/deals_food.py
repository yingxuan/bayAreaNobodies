"""
Food Deals API endpoints
"""
from fastapi import APIRouter, Query
from app.services.food_deals_service import fetch_food_deals

router = APIRouter()


@router.get("/food")
def get_food_deals(
    city: str = Query(default="cupertino", description="City name"),
    limit: int = Query(default=10, ge=1, le=20, description="Number of deals to return")
):
    """
    Get fast food deals (Burger King, Subway, McDonald's, etc.)
    
    Returns:
    - Google CSE search results (if available)
    - Cached results (if within TTL)
    - Mock deals (fallback)
    
    Never returns 500.
    """
    try:
        deals = fetch_food_deals(city=city, limit=limit)
        return {
            "items": deals,
            "total": len(deals),
            "city": city,
            "dataSource": "cse" if len(deals) > 0 and deals[0].get("id", "").startswith("food-") else "mock"
        }
    except Exception as e:
        print(f"Error in /deals/food: {e}")
        import traceback
        traceback.print_exc()
        # Return mock on error
        from app.services.food_deals_service import MOCK_FOOD_DEALS
        return {
            "items": MOCK_FOOD_DEALS[:limit],
            "total": min(len(MOCK_FOOD_DEALS), limit),
            "city": city,
            "dataSource": "mock"
        }

