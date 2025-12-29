"""
Market Snapshot Service - unified service for banner KPIs
Aggregates data from multiple sources with per-field caching and stale tracking
"""
import os
import redis
import json
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import pytz

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(REDIS_URL, decode_responses=True) if REDIS_URL else None

# Cache TTL: 15 minutes for snapshot, per-field TTLs for last-known-good values
SNAPSHOT_CACHE_TTL = 900  # 15 minutes
# Per-field TTLs (in seconds)
FIELD_TTL_BTC = 600  # 10 minutes
FIELD_TTL_GOLD = 600  # 10 minutes
FIELD_TTL_SP500 = 300  # 5 minutes (more frequent updates for market)
FIELD_TTL_MORTGAGE = 43200  # 12 hours
FIELD_TTL_LOTTERY = 1800  # 30 minutes

# Lock key to prevent cache stampede
LOCK_KEY = "market:snapshot:lock"
LOCK_TTL = 30  # 30 seconds

# Field-specific lock keys
FIELD_LOCK_TTL = 30  # 30 seconds


def get_snapshot_cache_key() -> str:
    """Get Redis key for full snapshot cache"""
    return "market:snapshot:full"


def get_field_cache_key(field: str) -> str:
    """Get Redis key for individual field last-known-good value"""
    return f"market:snapshot:field:{field}"


def get_field_lock_key(field: str) -> str:
    """Get Redis key for field-specific lock"""
    return f"market:snapshot:lock:{field}"


def get_field_ttl(field: str) -> int:
    """Get TTL for a specific field"""
    field_ttl_map = {
        "btc": FIELD_TTL_BTC,
        "gold": FIELD_TTL_GOLD,
        "sp500": FIELD_TTL_SP500,
        "jumbo_loan": FIELD_TTL_MORTGAGE,
        "powerball": FIELD_TTL_LOTTERY,
    }
    return field_ttl_map.get(field, 3600)  # Default 1 hour


def acquire_lock() -> bool:
    """Acquire distributed lock to prevent cache stampede"""
    if not redis_client:
        return True
    return redis_client.set(LOCK_KEY, "1", nx=True, ex=LOCK_TTL)


def acquire_field_lock(field: str) -> bool:
    """Acquire field-specific lock"""
    if not redis_client:
        return True
    lock_key = get_field_lock_key(field)
    return redis_client.set(lock_key, "1", nx=True, ex=FIELD_LOCK_TTL)


def release_lock():
    """Release distributed lock"""
    if redis_client:
        redis_client.delete(LOCK_KEY)


def release_field_lock(field: str):
    """Release field-specific lock"""
    if redis_client:
        lock_key = get_field_lock_key(field)
        redis_client.delete(lock_key)


def get_last_known_value(field: str) -> Optional[Dict]:
    """Get last known good value for a field from cache (full structure)"""
    if not redis_client:
        return None
    cached = redis_client.get(get_field_cache_key(field))
    if cached:
        try:
            return json.loads(cached)
        except:
            # Try legacy format (just float)
            try:
                value = float(cached)
                return {"value": value}
            except:
                pass
    return None


def store_field_value(field: str, value: Dict):
    """Store last known good value for a field with field-specific TTL"""
    if redis_client and value:
        ttl = get_field_ttl(field)
        redis_client.setex(get_field_cache_key(field), ttl, json.dumps(value, default=str))


def parse_jackpot_amount(text: str) -> Optional[float]:
    """
    Parse jackpot amount from text (supports billion/million/B/M)
    Returns amount in USD (integer)
    """
    # More comprehensive patterns
    patterns = [
        r'\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(billion|B)\b',  # $1.08B, 1.08 billion
        r'\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(million|M)\b',  # $330M, 330 million
        r'jackpot[:\s]+\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*([BMbm])?',  # jackpot: $108
        r'\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*([BMbm])\b',  # $108B, $330M
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            amount_str = match.group(1).replace(',', '')
            try:
                amount = float(amount_str)
                unit = match.group(2) if len(match.groups()) > 1 else None
                
                if unit:
                    unit = unit.upper()
                    if unit in ['B', 'BILLION']:
                        return int(amount * 1_000_000_000)
                    elif unit in ['M', 'MILLION']:
                        return int(amount * 1_000_000)
                
                # If no unit but amount is large, assume billions if >= 1000
                if amount >= 1000:
                    return int(amount * 1_000_000_000)
                else:
                    return int(amount * 1_000_000)
            except (ValueError, IndexError):
                continue
    
    return None


def parse_draw_date(text: str, la_tz: pytz.BaseTzInfo) -> Optional[str]:
    """
    Parse next drawing date from text
    Returns YYYY-MM-DD format or None
    """
    now_la = datetime.now(la_tz)
    
    # Try explicit date formats first
    date_patterns = [
        r'(Jan|January|Feb|February|Mar|March|Apr|April|May|Jun|June|Jul|July|Aug|August|Sep|September|Oct|October|Nov|November|Dec|December)\s+(\d{1,2})(?:st|nd|rd|th)?(?:\s*,?\s*(\d{4}))?',  # January 6, 2026
        r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # 1/6/2026, 01-06-2026
        r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',  # 2026/1/6
    ]
    
    month_map = {
        'jan': 1, 'january': 1, 'feb': 2, 'february': 2, 'mar': 3, 'march': 3,
        'apr': 4, 'april': 4, 'may': 5, 'jun': 6, 'june': 6, 'jul': 7, 'july': 7,
        'aug': 8, 'august': 8, 'sep': 9, 'september': 9, 'oct': 10, 'october': 10,
        'nov': 11, 'november': 11, 'dec': 12, 'december': 12
    }
    
    for pattern in date_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                if len(match.groups()) == 3:
                    # Month name format
                    month_str = match.group(1).lower()
                    day = int(match.group(2))
                    year = int(match.group(3)) if match.group(3) else now_la.year
                    month = month_map.get(month_str)
                    if month:
                        draw_date = datetime(year, month, day, tzinfo=la_tz)
                        return draw_date.strftime("%Y-%m-%d")
                elif len(match.groups()) == 3:
                    # Numeric format
                    parts = [int(g) for g in match.groups()]
                    if parts[0] > 12:  # YYYY-MM-DD
                        year, month, day = parts
                    else:  # MM/DD/YYYY or DD/MM/YYYY (assume MM/DD/YYYY)
                        month, day, year = parts
                    draw_date = datetime(year, month, day, tzinfo=la_tz)
                    return draw_date.strftime("%Y-%m-%d")
            except (ValueError, IndexError):
                continue
    
    # Try weekday format (Mon/Wed/Sat) - Powerball draws on these days
    weekday_patterns = [
        r'(Monday|Mon|Tuesday|Tue|Wednesday|Wed|Thursday|Thu|Friday|Fri|Saturday|Sat|Sunday|Sun)',
        r'(next\s+)?(Mon|Wed|Sat)',
    ]
    
    weekday_map = {
        'mon': 0, 'monday': 0, 'tue': 1, 'tuesday': 1, 'wed': 2, 'wednesday': 2,
        'thu': 3, 'thursday': 3, 'fri': 4, 'friday': 4, 'sat': 5, 'saturday': 5,
        'sun': 6, 'sunday': 6
    }
    
    powerball_days = [0, 2, 5]  # Mon, Wed, Sat
    
    for pattern in weekday_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            weekday_str = match.group(len(match.groups())).lower()
            target_weekday = weekday_map.get(weekday_str)
            if target_weekday is not None:
                # Find next Powerball draw day
                days_ahead = 0
                current_weekday = now_la.weekday()
                
                # If today is a draw day and it's before draw time (usually 10:59 PM ET = 7:59 PM PT)
                # Assume draws happen in the evening, so if it's before 8 PM PT, today might still be valid
                if current_weekday in powerball_days and now_la.hour < 20:
                    # Could be today, but for safety, go to next draw day
                    days_ahead = 1
                
                # Find next draw day
                while days_ahead < 7:
                    check_date = now_la + timedelta(days=days_ahead)
                    if check_date.weekday() in powerball_days:
                        return check_date.strftime("%Y-%m-%d")
                    days_ahead += 1
    
    return None


def fetch_powerball_jackpot_and_next_draw() -> Dict:
    """
    Fetch Powerball jackpot and next draw date using Google CSE
    Returns unified structure with caching, locking, and fallback
    
    Returns:
    {
        "game": "Powerball",
        "jackpot": 1080000000,  # integer USD
        "drawDate": "2026-01-06",  # YYYY-MM-DD or null
        "sourceUrl": "https://...",
        "dataSource": "google_cse|live|mock",
        "stale": false,
        "ttlSeconds": 1800,
        "updatedAt": "ISO timestamp"
    }
    """
    field = "powerball"
    cache_key = get_field_cache_key(field)
    la_tz = pytz.timezone("America/Los_Angeles")
    refresh_timestamp = datetime.now(pytz.UTC)
    
    # Check cache first
    if redis_client:
        cached = redis_client.get(cache_key)
        if cached:
            try:
                data = json.loads(cached)
                # Check if still fresh (within TTL)
                if "updatedAt" in data:
                    updated = datetime.fromisoformat(data["updatedAt"].replace("Z", "+00:00"))
                    age = (refresh_timestamp - updated).total_seconds()
                    if age < FIELD_TTL_LOTTERY:
                        return data
            except:
                pass
    
    # Acquire field lock
    if not acquire_field_lock(field):
        # If lock exists, return cached data
        if redis_client:
            cached = redis_client.get(cache_key)
            if cached:
                try:
                    return json.loads(cached)
                except:
                    pass
        # If no cache, return mock
        return {
            "game": "Powerball",
            "jackpot": 33_000_000,
            "drawDate": None,
            "sourceUrl": None,
            "dataSource": "mock",
            "stale": True,
            "ttlSeconds": FIELD_TTL_LOTTERY,
            "updatedAt": refresh_timestamp.isoformat()
        }
    
    try:
        from app.services.google_search import search_google, check_budget_exceeded
        
        # Check budget
        if check_budget_exceeded():
            # Return last known good or mock
            last_known = get_last_known_value(field)
            if last_known and "jackpot" in last_known:
                result = last_known.copy()
                result["stale"] = True
                result["dataSource"] = "mock"
                result["updatedAt"] = refresh_timestamp.isoformat()
                return result
            
            return {
                "game": "Powerball",
                "jackpot": 33_000_000,
                "drawDate": None,
                "sourceUrl": None,
                "dataSource": "mock",
                "stale": True,
                "ttlSeconds": FIELD_TTL_LOTTERY,
                "updatedAt": refresh_timestamp.isoformat()
            }
        
        # Trusted domain whitelist (weighted)
        trusted_domains = [
            "powerball.com",
            "musl.com",
            "wikipedia.org",
            "cnn.com",
            "bbc.com",
            "nbcnews.com",
            "abcnews.com",
            "usatoday.com",
        ]
        
        # Multiple query strategies
        queries = [
            "Powerball jackpot next drawing",
            "Powerball estimated jackpot next draw date",
            "Powerball next draw date jackpot",
            "site:powerball.com current jackpot",
        ]
        
        best_result = None
        best_confidence = 0
        
        for query in queries:
            try:
                # Timeout: 3 seconds, retry once
                results = search_google(query, num=10, date_restrict="d1", use_cache=True)
                
                if results.get("error"):
                    continue
                
                items = results.get("items", [])
                if not items:
                    continue
                
                for item in items:
                    link = item.get("link", "")
                    title = item.get("title", "")
                    snippet = item.get("snippet", "")
                    text = f"{title} {snippet}".lower()
                    
                    # Calculate confidence based on domain
                    confidence = 1.0
                    domain = ""
                    try:
                        from urllib.parse import urlparse
                        domain = urlparse(link).netloc.lower()
                        if any(td in domain for td in trusted_domains):
                            confidence = 2.0  # Boost trusted domains
                    except:
                        pass
                    
                    # Parse jackpot
                    jackpot = parse_jackpot_amount(f"{title} {snippet}")
                    if not jackpot or jackpot <= 0:
                        continue
                    
                    # Parse draw date
                    draw_date = parse_draw_date(f"{title} {snippet}", la_tz)
                    
                    # If we have jackpot and it's from trusted domain, use it
                    if confidence > best_confidence:
                        best_result = {
                            "game": "Powerball",
                            "jackpot": jackpot,
                            "drawDate": draw_date,
                            "sourceUrl": link,
                            "dataSource": "google_cse",
                            "stale": False,
                            "ttlSeconds": FIELD_TTL_LOTTERY,
                            "updatedAt": refresh_timestamp.isoformat()
                        }
                        best_confidence = confidence
                        
                        # If from trusted domain, break early
                        if confidence >= 2.0:
                            break
                
                if best_confidence >= 2.0:
                    break
                    
            except Exception as e:
                print(f"Error in Powerball query '{query}': {e}")
                continue
        
        if best_result:
            # Store in cache
            store_field_value(field, best_result)
            return best_result
        
        # No results - try last known good
        last_known = get_last_known_value(field)
        if last_known and "jackpot" in last_known:
            result = last_known.copy()
            result["stale"] = True
            result["dataSource"] = "mock"
            result["updatedAt"] = refresh_timestamp.isoformat()
            return result
        
        # Final fallback: mock
        return {
            "game": "Powerball",
            "jackpot": 33_000_000,
            "drawDate": None,
            "sourceUrl": None,
            "dataSource": "mock",
            "stale": True,
            "ttlSeconds": FIELD_TTL_LOTTERY,
            "updatedAt": refresh_timestamp.isoformat()
        }
        
    except Exception as e:
        print(f"Error fetching Powerball jackpot: {e}")
        import traceback
        traceback.print_exc()
        
        # Return last known good or mock
        last_known = get_last_known_value(field)
        if last_known and "jackpot" in last_known:
            result = last_known.copy()
            result["stale"] = True
            result["dataSource"] = "mock"
            result["updatedAt"] = refresh_timestamp.isoformat()
            return result
        
        return {
            "game": "Powerball",
            "jackpot": 33_000_000,
            "drawDate": None,
            "sourceUrl": None,
            "dataSource": "mock",
            "stale": True,
            "ttlSeconds": FIELD_TTL_LOTTERY,
            "updatedAt": refresh_timestamp.isoformat()
        }
    finally:
        release_field_lock(field)


def fetch_gold_price() -> Dict:
    """
    Fetch real-time gold price (XAU/USD) with CSE fallback
    Returns unified structure with caching, locking, and fallback
    
    Returns:
    {
        "price": 2650.1,
        "chgPct24h": 0.2,  # or null if unavailable
        "sourceUrl": "https://...",
        "dataSource": "live|google_cse|mock",
        "stale": false,
        "ttlSeconds": 600,
        "updatedAt": "ISO timestamp"
    }
    """
    field = "gold"
    cache_key = get_field_cache_key(field)
    refresh_timestamp = datetime.now(pytz.UTC)
    
    # Check cache first
    if redis_client:
        cached = redis_client.get(cache_key)
        if cached:
            try:
                data = json.loads(cached)
                if "updatedAt" in data:
                    updated = datetime.fromisoformat(data["updatedAt"].replace("Z", "+00:00"))
                    age = (refresh_timestamp - updated).total_seconds()
                    if age < FIELD_TTL_GOLD:
                        return data
            except:
                pass
    
    # Acquire field lock
    if not acquire_field_lock(field):
        if redis_client:
            cached = redis_client.get(cache_key)
            if cached:
                try:
                    return json.loads(cached)
                except:
                    pass
        return {
            "price": 2650.0,
            "chgPct24h": None,
            "sourceUrl": None,
            "dataSource": "mock",
            "stale": True,
            "ttlSeconds": FIELD_TTL_GOLD,
            "updatedAt": refresh_timestamp.isoformat()
        }
    
    try:
        # Priority 1: Finnhub (if available)
        finnhub_key = os.getenv("FINNHUB_API_KEY")
        if finnhub_key:
            try:
                import httpx
                url = f"https://finnhub.io/api/v1/quote?symbol=GC=F&token={finnhub_key}"
                with httpx.Client(timeout=3.0) as client:
                    response = client.get(url)
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("c") and data.get("c") > 0:
                            price = float(data["c"])
                            prev_close = data.get("pc", price)
                            chg_pct = ((price - prev_close) / prev_close) * 100 if prev_close > 0 else None
                            result = {
                                "price": round(price, 2),
                                "chgPct24h": round(chg_pct, 2) if chg_pct is not None else None,
                                "sourceUrl": "https://finnhub.io",
                                "dataSource": "live",
                                "stale": False,
                                "ttlSeconds": FIELD_TTL_GOLD,
                                "updatedAt": refresh_timestamp.isoformat()
                            }
                            store_field_value(field, result)
                            return result
            except Exception as e:
                print(f"Error fetching gold from Finnhub: {e}")
        
        # Priority 2: yfinance
        try:
            import yfinance as yf
            ticker = yf.Ticker("GC=F")
            hist = ticker.history(period="2d", interval="1d", timeout=3.0)
            if len(hist) >= 2:
                current_price = float(hist.iloc[-1]['Close'])
                prev_price = float(hist.iloc[-2]['Close'])
                chg_pct = ((current_price - prev_price) / prev_price) * 100 if prev_price > 0 else None
                result = {
                    "price": round(current_price, 2),
                    "chgPct24h": round(chg_pct, 2) if chg_pct is not None else None,
                    "sourceUrl": "https://finance.yahoo.com/quote/GC%3DF",
                    "dataSource": "live",
                    "stale": False,
                    "ttlSeconds": FIELD_TTL_GOLD,
                    "updatedAt": refresh_timestamp.isoformat()
                }
                store_field_value(field, result)
                return result
            elif len(hist) == 1:
                price = float(hist.iloc[-1]['Close'])
                result = {
                    "price": round(price, 2),
                    "chgPct24h": None,
                    "sourceUrl": "https://finance.yahoo.com/quote/GC%3DF",
                    "dataSource": "live",
                    "stale": False,
                    "ttlSeconds": FIELD_TTL_GOLD,
                    "updatedAt": refresh_timestamp.isoformat()
                }
                store_field_value(field, result)
                return result
        except ImportError:
            pass
        except Exception as e:
            print(f"Error fetching gold from yfinance: {e}")
        
        # Priority 3: Google CSE fallback
        from app.services.google_search import search_google, check_budget_exceeded
        
        if not check_budget_exceeded():
            try:
                queries = [
                    "XAU USD price per ounce",
                    "gold price per ounce USD today",
                    "site:google.com/finance gold price XAUUSD",
                ]
                
                for query in queries:
                    try:
                        results = search_google(query, num=5, date_restrict="d1", use_cache=True)
                        if results.get("error"):
                            continue
                        
                        items = results.get("items", [])
                        for item in items:
                            text = f"{item.get('title', '')} {item.get('snippet', '')}"
                            link = item.get("link", "")
                            
                            # Parse price patterns
                            price_patterns = [
                                r'\$?\s*(\d{1,4}(?:,\d{3})*(?:\.\d{2})?)\s*(?:usd|per ounce|oz|/oz)',
                                r'(\d{1,4}(?:,\d{3})*(?:\.\d{2})?)\s*(?:usd|per ounce)',
                            ]
                            
                            for pattern in price_patterns:
                                match = re.search(pattern, text, re.IGNORECASE)
                                if match:
                                    price_str = match.group(1).replace(',', '')
                                    try:
                                        price = float(price_str)
                                        if 1000 < price < 5000:  # Reasonable range
                                            result = {
                                                "price": round(price, 2),
                                                "chgPct24h": None,
                                                "sourceUrl": link,
                                                "dataSource": "google_cse",
                                                "stale": False,
                                                "ttlSeconds": FIELD_TTL_GOLD,
                                                "updatedAt": refresh_timestamp.isoformat()
                                            }
                                            store_field_value(field, result)
                                            return result
                                    except ValueError:
                                        continue
                    except Exception as e:
                        print(f"Error in gold CSE query '{query}': {e}")
                        continue
            except Exception as e:
                print(f"Error fetching gold from CSE: {e}")
        
        # Fallback: last known good
        last_known = get_last_known_value(field)
        if last_known and "price" in last_known:
            result = last_known.copy()
            result["stale"] = True
            result["dataSource"] = "mock"
            result["updatedAt"] = refresh_timestamp.isoformat()
            return result
        
        # Final fallback: mock
        return {
            "price": 2650.0,
            "chgPct24h": None,
            "sourceUrl": None,
            "dataSource": "mock",
            "stale": True,
            "ttlSeconds": FIELD_TTL_GOLD,
            "updatedAt": refresh_timestamp.isoformat()
        }
        
    except Exception as e:
        print(f"Error fetching gold price: {e}")
        import traceback
        traceback.print_exc()
        
        last_known = get_last_known_value(field)
        if last_known and "price" in last_known:
            result = last_known.copy()
            result["stale"] = True
            result["dataSource"] = "mock"
            result["updatedAt"] = refresh_timestamp.isoformat()
            return result
        
        return {
            "price": 2650.0,
            "chgPct24h": None,
            "sourceUrl": None,
            "dataSource": "mock",
            "stale": True,
            "ttlSeconds": FIELD_TTL_GOLD,
            "updatedAt": refresh_timestamp.isoformat()
        }
    finally:
        release_field_lock(field)


def fetch_btc_price() -> tuple[Optional[float], Optional[float], str]:
    """
    Fetch BTC price using Finnhub (if available), then yfinance, then fallback
    Returns: (price, chgPct24h, source) or (None, None, "error")
    """
    # Try Finnhub first if available (most reliable)
    finnhub_key = os.getenv("FINNHUB_API_KEY")
    if finnhub_key:
        try:
            import httpx
            # Use COINBASE:BTC-USD which we know works
            url = f"https://finnhub.io/api/v1/quote?symbol=COINBASE:BTC-USD&token={finnhub_key}"
            with httpx.Client(timeout=5.0) as client:
                response = client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    current_price = data.get("c")
                    if current_price and current_price > 0:  # current price must be > 0
                        price = float(current_price)
                        prev_close = data.get("pc", price)
                        chg_pct = ((price - prev_close) / prev_close) * 100 if prev_close > 0 else 0.0
                        print(f"BTC price from Finnhub: ${price:.2f} (change: {chg_pct:.2f}%)")
                        return (price, round(chg_pct, 2), "finnhub")
                    else:
                        print(f"Finnhub returned invalid BTC price: {current_price}")
        except Exception as e:
            print(f"Error fetching BTC from Finnhub: {e}")
            import traceback
            traceback.print_exc()
    
    try:
        try:
            import yfinance as yf
            ticker = yf.Ticker("BTC-USD")
            hist = ticker.history(period="2d", interval="1d")
            if len(hist) >= 2:
                current_price = float(hist.iloc[-1]['Close'])
                prev_price = float(hist.iloc[-2]['Close'])
                chg_pct = ((current_price - prev_price) / prev_price) * 100 if prev_price > 0 else 0.0
                return (current_price, round(chg_pct, 2), "yfinance")
            elif len(hist) == 1:
                price = float(hist.iloc[-1]['Close'])
                return (price, 0.0, "yfinance")
        except ImportError:
            pass
        except Exception as e:
            print(f"Error fetching BTC from yfinance: {e}")
        
        # Fallback: use existing crypto service
        from app.services.crypto_service import fetch_btc_price
        data = fetch_btc_price()
        if data.get("price", 0) > 0 and data.get("data_freshness") != "placeholder":
            price = data["price"]
            chg_pct = data.get("change_percent", 0.0)
            return (price, chg_pct, "crypto_service")
    except Exception as e:
        print(f"Error fetching BTC price: {e}")
    
    return (None, None, "error")


def fetch_sp500_price() -> tuple[Optional[float], Optional[float], str]:
    """
    Fetch S&P 500 price using yfinance (^GSPC) or fallback to SPY ETF
    Returns: (price, chgPct24h, source) or (None, None, "error")
    """
    try:
        try:
            import yfinance as yf
            # Try to get S&P 500 index directly
            ticker = yf.Ticker("^GSPC")
            # Use history instead of info to avoid rate limits
            hist = ticker.history(period="2d", interval="1d")
            if len(hist) >= 2:
                current_price = float(hist.iloc[-1]['Close'])
                prev_price = float(hist.iloc[-2]['Close'])
                chg_pct = ((current_price - prev_price) / prev_price) * 100 if prev_price > 0 else 0.0
                return (current_price, round(chg_pct, 2), "yfinance")
            elif len(hist) == 1:
                price = float(hist.iloc[-1]['Close'])
                return (price, 0.0, "yfinance")
        except ImportError:
            pass
        except Exception as e:
            print(f"Error fetching S&P 500 from yfinance (^GSPC): {e}")
            # Try SPY ETF as fallback (SPY tracks S&P 500, price is ~1/10 of index)
            try:
                import yfinance as yf
                spy_ticker = yf.Ticker("SPY")
                spy_hist = spy_ticker.history(period="2d", interval="1d")
                if len(spy_hist) >= 2:
                    spy_price = float(spy_hist.iloc[-1]['Close'])
                    spy_prev = float(spy_hist.iloc[-2]['Close'])
                    # Estimate S&P 500 index value (SPY is typically ~1/10 of index, but use actual ratio)
                    # For more accuracy, we can multiply by ~10, but let's use a more accurate method
                    # Actually, let's just use SPY price * 10 as approximation
                    estimated_index = spy_price * 10
                    chg_pct = ((spy_price - spy_prev) / spy_prev) * 100 if spy_prev > 0 else 0.0
                    return (estimated_index, round(chg_pct, 2), "yfinance_spy")
            except Exception as e2:
                print(f"Error fetching SPY from yfinance: {e2}")
        
        # Fallback: try Finnhub if available (use SPY and estimate index)
        finnhub_key = os.getenv("FINNHUB_API_KEY")
        if finnhub_key:
            try:
                import httpx
                url = f"https://finnhub.io/api/v1/quote?symbol=SPY&token={finnhub_key}"
                with httpx.Client(timeout=5.0) as client:
                    response = client.get(url)
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("c"):  # current price
                            spy_price = float(data["c"])
                            prev_close = data.get("pc", spy_price)  # previous close
                            chg_pct = ((spy_price - prev_close) / prev_close) * 100 if prev_close > 0 else 0.0
                            # Estimate S&P 500 index (SPY is typically ~1/10 of index, so multiply by 10)
                            estimated_index = spy_price * 10
                            return (round(estimated_index, 2), round(chg_pct, 2), "finnhub_spy")
            except Exception as e:
                print(f"Error fetching S&P 500 from Finnhub: {e}")
    except Exception as e:
        print(f"Error fetching S&P 500 price: {e}")
    
    return (None, None, "error")


def fetch_jumbo_7arm_rate() -> tuple[Optional[float], Optional[str], str]:
    """
    Fetch CA Jumbo 7/1 ARM rate (using as mortgage30y for now)
    Returns: (rate, week_date, source) or (None, None, "error")
    """
    try:
        from app.services.loan_service import fetch_jumbo_7arm_rate
        data = fetch_jumbo_7arm_rate()
        rate = data.get("rate", 0)
        if rate > 0:
            # Use current date as weekDate (could be improved with actual week date)
            week_date = datetime.now().strftime("%Y-%m-%d")
            return (rate, week_date, "loan_service")
    except Exception as e:
        print(f"Error fetching Jumbo 7/1 ARM rate: {e}")
    
    return (None, None, "error")


def fetch_tbill_3m_rate() -> tuple[Optional[float], str]:
    """
    Fetch T-bill 3-month rate
    Returns: (rate, source) or (None, "error")
    """
    try:
        from app.services.treasury_service import fetch_tbill_rate
        data = fetch_tbill_rate()
        rate = data.get("rate", 0)
        if rate > 0:
            return (rate, "treasury_service")
    except Exception as e:
        print(f"Error fetching T-bill rate: {e}")
    
    return (None, "error")


def fetch_market_snapshot() -> Dict:
    """
    Fetch unified market snapshot with all KPIs
    Uses per-field caching and tracks stale fields
    
    Returns structure compatible with frontend:
    {
        "updatedAt": "ISO",
        "dataSource": {"btc":"live|mock", "gold":"live|mock", "mortgage":"live|mock", "lottery":"live|mock"},
        "btc": {"price": 0, "chgPct24h": 0, "stale": false, "ttlSeconds": 600},
        "gold": {"price": 0, "chgPct24h": 0, "stale": false, "ttlSeconds": 600, "sourceUrl": "..."},
        "mortgage30y": {"rate": 0, "weekDate": "YYYY-MM-DD", "stale": false, "ttlSeconds": 43200},
        "lottery": {"game": "Powerball", "jackpot": 0, "drawDate": "YYYY-MM-DD", "stale": false, "ttlSeconds": 1800, "sourceUrl": "..."}
    }
    """
    # Check full snapshot cache first
    if redis_client:
        cached = redis_client.get(get_snapshot_cache_key())
        if cached:
            try:
                data = json.loads(cached)
                # Convert old format to new format if needed
                if "btc_usd" in data:
                    return convert_to_new_format(data)
                return data
            except:
                pass
    
    # Acquire lock to prevent cache stampede
    if not acquire_lock():
        # If lock exists, return cached data if available
        if redis_client:
            cached = redis_client.get(get_snapshot_cache_key())
            if cached:
                try:
                    data = json.loads(cached)
                    if "btc_usd" in data:
                        return convert_to_new_format(data)
                    return data
                except:
                    pass
    
    try:
        # Use consistent refresh timestamp for all fields
        refresh_timestamp = datetime.now(pytz.UTC)
        
        # Build new format snapshot with ttlSeconds
        snapshot = {
            "updatedAt": refresh_timestamp.isoformat(),
            "dataSource": {},
            "stale": False,
            "ttlSeconds": SNAPSHOT_CACHE_TTL,
            "btc": {"price": 0, "chgPct24h": 0, "stale": False, "ttlSeconds": FIELD_TTL_BTC},
            "gold": {"price": 0, "chgPct24h": None, "stale": False, "ttlSeconds": FIELD_TTL_GOLD},
            "sp500": {"price": 0, "chgPct24h": 0, "stale": False, "ttlSeconds": FIELD_TTL_SP500},
            "mortgage30y": {"rate": 0, "weekDate": refresh_timestamp.strftime("%Y-%m-%d"), "stale": False, "ttlSeconds": FIELD_TTL_MORTGAGE},
            "lottery": {"game": "Powerball", "jackpot": 0, "drawDate": None, "stale": False, "ttlSeconds": FIELD_TTL_LOTTERY}
        }
        
        # Fetch Gold (new unified structure)
        gold_data = fetch_gold_price()
        if gold_data and gold_data.get("price", 0) > 0:
            snapshot["gold"]["price"] = gold_data["price"]
            snapshot["gold"]["chgPct24h"] = gold_data.get("chgPct24h")
            snapshot["gold"]["stale"] = gold_data.get("stale", False)
            snapshot["gold"]["sourceUrl"] = gold_data.get("sourceUrl")
            snapshot["dataSource"]["gold"] = gold_data.get("dataSource", "mock")
        else:
            last_gold = get_last_known_value("gold")
            if last_gold and last_gold.get("price", 0) > 0:
                snapshot["gold"]["price"] = last_gold["price"]
                snapshot["gold"]["chgPct24h"] = last_gold.get("chgPct24h")
                snapshot["gold"]["stale"] = True
                snapshot["dataSource"]["gold"] = "mock"
            else:
                snapshot["gold"]["price"] = 2650.0
                snapshot["gold"]["chgPct24h"] = None
                snapshot["gold"]["stale"] = True
                snapshot["dataSource"]["gold"] = "mock"
        
        # Fetch Powerball (new unified structure)
        powerball_data = fetch_powerball_jackpot_and_next_draw()
        if powerball_data and powerball_data.get("jackpot", 0) > 0:
            snapshot["lottery"]["jackpot"] = powerball_data["jackpot"]
            snapshot["lottery"]["game"] = powerball_data.get("game", "Powerball")
            snapshot["lottery"]["drawDate"] = powerball_data.get("drawDate")
            snapshot["lottery"]["stale"] = powerball_data.get("stale", False)
            snapshot["lottery"]["sourceUrl"] = powerball_data.get("sourceUrl")
            snapshot["dataSource"]["lottery"] = powerball_data.get("dataSource", "mock")
        else:
            last_pb = get_last_known_value("powerball")
            if last_pb and last_pb.get("jackpot", 0) > 0:
                snapshot["lottery"]["jackpot"] = last_pb["jackpot"]
                snapshot["lottery"]["game"] = last_pb.get("game", "Powerball")
                snapshot["lottery"]["drawDate"] = last_pb.get("drawDate")
                snapshot["lottery"]["stale"] = True
                snapshot["dataSource"]["lottery"] = "mock"
            else:
                snapshot["lottery"]["jackpot"] = 33_000_000
                snapshot["lottery"]["game"] = "Powerball"
                snapshot["lottery"]["drawDate"] = None
                snapshot["lottery"]["stale"] = True
                snapshot["dataSource"]["lottery"] = "mock"
        
        # Fetch BTC (keep existing tuple-based approach for now)
        btc_price, btc_chg, btc_source = fetch_btc_price()
        if btc_price:
            snapshot["btc"]["price"] = round(btc_price, 0)
            snapshot["btc"]["chgPct24h"] = btc_chg if btc_chg is not None else 0.0
            snapshot["btc"]["stale"] = False
            snapshot["dataSource"]["btc"] = "live" if btc_source not in ["cached", "placeholder", "error"] else "mock"
            store_field_value("btc", {"value": btc_price})
        else:
            last_btc = get_last_known_value("btc")
            if last_btc and last_btc.get("value"):
                snapshot["btc"]["price"] = round(last_btc["value"], 0)
                snapshot["btc"]["chgPct24h"] = 0.0
                snapshot["btc"]["stale"] = True
                snapshot["dataSource"]["btc"] = "mock"
            else:
                snapshot["btc"]["price"] = 95000.0
                snapshot["btc"]["chgPct24h"] = 0.0
                snapshot["btc"]["stale"] = True
                snapshot["dataSource"]["btc"] = "mock"
        
        # S&P 500
        sp500_price, sp500_chg, sp500_source = fetch_sp500_price()
        if sp500_price:
            snapshot["sp500"]["price"] = round(sp500_price, 2)
            snapshot["sp500"]["chgPct24h"] = sp500_chg if sp500_chg is not None else 0.0
            snapshot["sp500"]["stale"] = False
            snapshot["dataSource"]["sp500"] = "live" if sp500_source not in ["cached", "placeholder", "error"] else "mock"
            store_field_value("sp500", {"value": sp500_price})
        else:
            last_sp500 = get_last_known_value("sp500")
            if last_sp500 and last_sp500.get("value"):
                snapshot["sp500"]["price"] = round(last_sp500["value"], 2)
                snapshot["sp500"]["chgPct24h"] = 0.0
                snapshot["sp500"]["stale"] = True
                snapshot["dataSource"]["sp500"] = "mock"
            else:
                snapshot["sp500"]["price"] = 5234.0
                snapshot["sp500"]["chgPct24h"] = 0.0
                snapshot["sp500"]["stale"] = True
                snapshot["dataSource"]["sp500"] = "mock"
        
        # Mortgage (using Jumbo 7/1 ARM as mortgage30y for now)
        jumbo_rate, jumbo_week_date, jumbo_source = fetch_jumbo_7arm_rate()
        if jumbo_rate:
            snapshot["mortgage30y"]["rate"] = round(jumbo_rate, 2)
            snapshot["mortgage30y"]["weekDate"] = jumbo_week_date or refresh_timestamp.strftime("%Y-%m-%d")
            snapshot["mortgage30y"]["stale"] = False
            snapshot["dataSource"]["mortgage"] = "live" if jumbo_source not in ["cached", "placeholder", "error"] else "mock"
            store_field_value("jumbo_loan", {"value": jumbo_rate})
        else:
            last_jumbo = get_last_known_value("jumbo_loan")
            if last_jumbo and last_jumbo.get("value"):
                snapshot["mortgage30y"]["rate"] = round(last_jumbo["value"], 2)
                snapshot["mortgage30y"]["weekDate"] = refresh_timestamp.strftime("%Y-%m-%d")
                snapshot["mortgage30y"]["stale"] = True
                snapshot["dataSource"]["mortgage"] = "mock"
            else:
                snapshot["mortgage30y"]["rate"] = 6.5
                snapshot["mortgage30y"]["weekDate"] = refresh_timestamp.strftime("%Y-%m-%d")
                snapshot["mortgage30y"]["stale"] = True
                snapshot["dataSource"]["mortgage"] = "mock"
        
        # T-bill (not in new format, but keep for backward compatibility)
        tbill_rate, tbill_source = fetch_tbill_3m_rate()
        if tbill_rate:
            store_field_value("tbill", {"value": tbill_rate})
        
        # Determine overall stale status (if any field is stale, mark overall as stale)
        snapshot["stale"] = any([
            snapshot["btc"]["stale"],
            snapshot["gold"]["stale"],
            snapshot["sp500"]["stale"],
            snapshot["mortgage30y"]["stale"],
            snapshot["lottery"]["stale"]
        ])
        
        # Cache the full snapshot
        if redis_client:
            redis_client.setex(
                get_snapshot_cache_key(),
                SNAPSHOT_CACHE_TTL,
                json.dumps(snapshot, default=str)
            )
        
        return snapshot
        
    except Exception as e:
        print(f"Error in fetch_market_snapshot: {e}")
        import traceback
        traceback.print_exc()
        # Return safe fallback
        fallback_timestamp = datetime.now(pytz.UTC)
        return {
            "updatedAt": fallback_timestamp.isoformat(),
            "dataSource": {"btc": "mock", "gold": "mock", "sp500": "mock", "mortgage": "mock", "lottery": "mock"},
            "stale": True,
            "ttlSeconds": SNAPSHOT_CACHE_TTL,
            "btc": {"price": 95000, "chgPct24h": 0, "stale": True, "ttlSeconds": FIELD_TTL_BTC},
            "gold": {"price": 2650, "chgPct24h": None, "stale": True, "ttlSeconds": FIELD_TTL_GOLD},
            "sp500": {"price": 5234, "chgPct24h": 0, "stale": True, "ttlSeconds": FIELD_TTL_SP500},
            "mortgage30y": {"rate": 6.5, "weekDate": fallback_timestamp.strftime("%Y-%m-%d"), "stale": True, "ttlSeconds": FIELD_TTL_MORTGAGE},
            "lottery": {"game": "Powerball", "jackpot": 33000000, "drawDate": None, "stale": True, "ttlSeconds": FIELD_TTL_LOTTERY}
        }
    finally:
        release_lock()


def convert_to_new_format(old_data: Dict) -> Dict:
    """Convert old format snapshot to new format"""
    try:
        fallback_timestamp = datetime.now(pytz.UTC)
        new_format = {
            "updatedAt": old_data.get("as_of", fallback_timestamp.isoformat()),
            "dataSource": {},
            "btc": {"price": 0, "chgPct24h": 0, "stale": True},
            "gold": {"price": 0, "chgPct24h": None, "stale": True},
            "mortgage30y": {"rate": 0, "weekDate": fallback_timestamp.strftime("%Y-%m-%d"), "stale": True},
            "lottery": {"game": "Powerball", "jackpot": 0, "drawDate": None, "stale": True}
        }
        
        # Convert BTC
        if old_data.get("btc_usd"):
            new_format["btc"]["price"] = round(old_data["btc_usd"], 0)
            new_format["btc"]["stale"] = "btc_usd" in old_data.get("stale_fields", [])
            new_format["dataSource"]["btc"] = "live" if old_data.get("sources", {}).get("btc") not in ["cached", "placeholder"] else "mock"
        
        # Convert Gold
        if old_data.get("gold_usd_per_oz"):
            new_format["gold"]["price"] = round(old_data["gold_usd_per_oz"], 2)
            new_format["gold"]["stale"] = "gold_usd_per_oz" in old_data.get("stale_fields", [])
            new_format["dataSource"]["gold"] = "live" if old_data.get("sources", {}).get("gold") not in ["cached", "placeholder"] else "mock"
        
        # Convert Mortgage
        if old_data.get("ca_jumbo_7_1_arm_rate"):
            new_format["mortgage30y"]["rate"] = round(old_data["ca_jumbo_7_1_arm_rate"], 2)
            new_format["mortgage30y"]["stale"] = "ca_jumbo_7_1_arm_rate" in old_data.get("stale_fields", [])
            new_format["dataSource"]["mortgage"] = "live" if old_data.get("sources", {}).get("mortgage") not in ["cached", "placeholder"] else "mock"
        
        # Convert Lottery
        if old_data.get("powerball_jackpot_usd"):
            new_format["lottery"]["jackpot"] = round(old_data["powerball_jackpot_usd"], 0)
            new_format["lottery"]["stale"] = "powerball_jackpot_usd" in old_data.get("stale_fields", [])
            new_format["dataSource"]["lottery"] = "live" if old_data.get("sources", {}).get("powerball") not in ["cached", "placeholder"] else "mock"
        
        # Add S&P 500 if not present (new field)
        if "sp500" not in new_format:
            new_format["sp500"] = {"price": 5234, "chgPct24h": 0, "stale": True}
            new_format["dataSource"]["sp500"] = "mock"
        
        return new_format
    except Exception as e:
        print(f"Error converting to new format: {e}")
        # Return safe fallback
        fallback_timestamp = datetime.now(pytz.UTC)
        return {
            "updatedAt": fallback_timestamp.isoformat(),
            "dataSource": {"btc": "mock", "gold": "mock", "sp500": "mock", "mortgage": "mock", "lottery": "mock"},
            "btc": {"price": 95000, "chgPct24h": 0, "stale": True},
            "gold": {"price": 2650, "chgPct24h": None, "stale": True},
            "sp500": {"price": 5234, "chgPct24h": 0, "stale": True},
            "mortgage30y": {"rate": 6.5, "weekDate": fallback_timestamp.strftime("%Y-%m-%d"), "stale": True},
            "lottery": {"game": "Powerball", "jackpot": 33000000, "drawDate": None, "stale": True}
        }
