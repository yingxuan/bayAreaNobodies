#!/usr/bin/env python3
"""Test script to verify Google CSE credentials are working"""
import os
import sys
import httpx
from app.services.google_search import search_google

def test_google_cse():
    """Test Google CSE API connection"""
    api_key = os.getenv("GOOGLE_CSE_API_KEY")
    cse_id = os.getenv("GOOGLE_CSE_ID")
    
    print("=" * 60)
    print("Google CSE Credentials Test")
    print("=" * 60)
    
    if not api_key or not cse_id:
        print("❌ ERROR: Google CSE credentials not set!")
        print("\nPlease set the following environment variables:")
        print("  - GOOGLE_CSE_API_KEY")
        print("  - GOOGLE_CSE_ID")
        print("\nYou can set them in a .env file or export them in your shell.")
        return False
    
    print(f"✓ API Key: {api_key[:10]}...{api_key[-4:] if len(api_key) > 14 else '***'}")
    print(f"✓ CSE ID: {cse_id}")
    print()
    
    # Test with a simple query
    print("Testing search query: 'site:1point3acres.com h1b'")
    print("-" * 60)
    
    try:
        results = search_google(
            query="site:1point3acres.com h1b",
            site_domain="1point3acres.com",
            num=3,
            use_cache=False  # Don't use cache for testing
        )
        
        items = results.get("items", [])
        total_results = results.get("searchInformation", {}).get("totalResults", "0")
        
        print(f"✓ Search successful!")
        print(f"✓ Total results found: {total_results}")
        print(f"✓ Results returned: {len(items)}")
        print()
        
        if items:
            print("Sample results:")
            for i, item in enumerate(items[:3], 1):
                print(f"\n  {i}. {item.get('title', 'No title')}")
                print(f"     URL: {item.get('link', 'No URL')}")
                print(f"     Snippet: {item.get('snippet', 'No snippet')[:100]}...")
        else:
            print("⚠ Warning: No results returned. This might mean:")
            print("  - Your CSE doesn't include 1point3acres.com")
            print("  - The search query returned no results")
            print("  - There's an issue with your CSE configuration")
        
        print()
        print("=" * 60)
        print("✅ Google CSE credentials are working!")
        print("=" * 60)
        return True
        
    except httpx.HTTPStatusError as e:
        print(f"❌ ERROR: HTTP {e.response.status_code} - {e.response.reason_phrase}")
        print(f"   URL: {e.request.url}")
        try:
            error_data = e.response.json()
            print(f"   Error details: {error_data}")
        except:
            print(f"   Response text: {e.response.text[:500]}")
        print()
        print("Common issues:")
        if e.response.status_code == 400:
            print("  - Invalid CSE ID format (should be like: 017576662512468239146:omuauf_lfve)")
            print("  - CSE ID doesn't exist or is incorrect")
            print("  - Query parameters are malformed")
        elif e.response.status_code == 401:
            print("  - Invalid API key")
            print("  - API key not enabled for Custom Search API")
        elif e.response.status_code == 403:
            print("  - API quota exceeded")
            print("  - API key restrictions preventing access")
        print()
        print("=" * 60)
        return False
    except Exception as e:
        print(f"❌ ERROR: Failed to search Google CSE")
        print(f"   Error: {str(e)}")
        print()
        print("Common issues:")
        print("  - Invalid API key or CSE ID")
        print("  - API key not enabled for Custom Search API")
        print("  - CSE doesn't include the sites you're searching")
        print("  - API quota exceeded")
        print()
        print("=" * 60)
        return False


if __name__ == "__main__":
    success = test_google_cse()
    sys.exit(0 if success else 1)

