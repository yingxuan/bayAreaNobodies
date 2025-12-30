"""
Huaren Forum API endpoints (Generic)
Supports any forumid (e.g., 395 for deals, 398 for gossip)
"""
from fastapi import APIRouter, Query
from app.services.huaren_forum_service import fetch_huaren_forum, fetch_gossip_forum

router = APIRouter()


@router.get("/forum")
def get_huaren_forum(
    forumid: int = Query(..., description="Forum ID (e.g., 395 for deals, 398 for gossip)"),
    page: int = Query(default=1, ge=1, description="Page number"),
    limit: int = Query(default=30, ge=1, le=100, description="Number of threads to return")
):
    """
    Get threads from any Huaren.us forum
    
    Returns:
    - Parsed forum threads
    - Cached results (if within TTL)
    - Empty list on error (graceful fallback)
    
    Never returns 500.
    """
    try:
        threads = fetch_huaren_forum(forumid=forumid, page=page)
        
        # Add source info
        for thread in threads:
            thread['source'] = 'huaren'
            thread['forumid'] = forumid
        
        return {
            "items": threads[:limit],
            "total": len(threads),
            "forumid": forumid,
            "page": page
        }
    except Exception as e:
        print(f"Error in /huaren/forum: {e}")
        import traceback
        traceback.print_exc()
        # Return empty list on error (graceful fallback)
        return {
            "items": [],
            "total": 0,
            "forumid": forumid,
            "page": page,
            "error": "Failed to fetch threads"
        }


@router.get("/gossip")
def get_huaren_gossip(
    forumid: int = Query(default=398, description="Forum ID (default 398 for gossip)"),
    page: int = Query(default=1, ge=1, description="Page number"),
    limit: int = Query(default=10, ge=1, le=50, description="Number of threads to return")
):
    """
    Get gossip threads from Huaren forum (forumid=398)
    Includes ranking by engagement and recency, quality filtering
    
    Returns:
    - Ranked and filtered gossip threads
    - Cached results (if within TTL)
    - Empty list on error (graceful fallback)
    
    Never returns 500.
    """
    try:
        threads = fetch_gossip_forum(forumid=forumid, page=page, limit=limit)
        
        return {
            "items": threads,
            "total": len(threads),
            "forumid": forumid,
            "page": page
        }
    except Exception as e:
        print(f"Error in /huaren/gossip: {e}")
        import traceback
        traceback.print_exc()
        # Return empty list on error (graceful fallback)
        return {
            "items": [],
            "total": 0,
            "forumid": forumid,
            "page": page,
            "error": "Failed to fetch gossip threads"
        }

