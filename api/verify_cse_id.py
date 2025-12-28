#!/usr/bin/env python3
"""Helper script to verify CSE ID format"""
import os
import re

def verify_cse_id_format(cse_id: str) -> bool:
    """
    Google CSE IDs typically have one of these formats:
    - Numbers:letters (e.g., 017576662512468239146:omuauf_lfve)
    - Just numbers (e.g., 017576662512468239146)
    - Some newer formats may vary
    """
    if not cse_id:
        return False
    
    # Common pattern: numbers followed by colon and alphanumeric
    pattern1 = r'^\d+:[a-zA-Z0-9_-]+$'
    # Or just numbers
    pattern2 = r'^\d+$'
    # Some newer formats
    pattern3 = r'^[a-zA-Z0-9_-]+:[a-zA-Z0-9_-]+$'
    
    return bool(re.match(pattern1, cse_id) or 
                re.match(pattern2, cse_id) or 
                re.match(pattern3, cse_id))

if __name__ == "__main__":
    cse_id = os.getenv("GOOGLE_CSE_ID", "")
    api_key = os.getenv("GOOGLE_CSE_API_KEY", "")
    
    print("=" * 60)
    print("CSE ID Format Verification")
    print("=" * 60)
    print()
    
    if not cse_id:
        print("❌ CSE ID is not set")
    else:
        print(f"CSE ID: {cse_id}")
        print(f"Length: {len(cse_id)} characters")
        print()
        
        if verify_cse_id_format(cse_id):
            print("✓ CSE ID format looks valid")
        else:
            print("⚠ WARNING: CSE ID format looks unusual")
            print()
            print("Expected formats:")
            print("  - Numbers:letters (e.g., 017576662512468239146:omuauf_lfve)")
            print("  - Just numbers (e.g., 017576662512468239146)")
            print()
            print("Your CSE ID starts with 'AQ.' which is unusual.")
            print("Please verify you copied the correct Search Engine ID from:")
            print("  https://programmablesearchengine.google.com/")
            print()
            print("To find your CSE ID:")
            print("  1. Go to https://programmablesearchengine.google.com/")
            print("  2. Click on your search engine")
            print("  3. Go to 'Setup' > 'Basics'")
            print("  4. Look for 'Search engine ID' (it's the 'cx' parameter)")
    
    print()
    print("=" * 60)
    
    if api_key:
        if api_key.startswith("AIzaSy"):
            print("✓ API Key format looks correct (starts with AIzaSy)")
        else:
            print("⚠ API Key format looks unusual")
    else:
        print("❌ API Key is not set")

