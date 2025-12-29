"""
Market Snapshot Service - unified service for banner KPIs
Aggregates data from multiple sources with per-field caching and stale tracking
"""
import os
import redis
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pytz

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(REDIS_URL, decode_responses=True) if REDIS_URL else None

# Cache TTL: 15 minutes for snapshot, per-field TTLs for last-known-good values
SNAPSHOT_CACHE_TTL = 900  # 15 minutes
# Per-field TTLs (in seconds)
FIELD_TTL_BTC = 600  # 10 minutes
FIELD_TTL_GOLD = 600  # 10 minutes
FIELD_TTL_MORTGAGE = 43200  # 12 hours
FIELD_TTL_LOTTERY = 1800  # 30 minutes

# Lock key to prevent cache stampede
LOCK_KEY = "market:snapshot:lock"
LOCK_TTL = 30  # 30 seconds


def get_snapshot_cache_key() -> str:
    """Get Redis key for full snapshot cache"""
    return "market:snapshot:full"


def get_field_cache_key(field: str) -> str:
    """Get Redis key for individual field last-known-good value"""
    return f"market:snapshot:field:{field}"


def get_field_ttl(field: str) -> int:
    """Get TTL for a specific field"""
    field_ttl_map = {
        "btc": FIELD_TTL_BTC,
        "gold": FIELD_TTL_GOLD,
        "jumbo_loan": FIELD_TTL_MORTGAGE,
        "powerball": FIELD_TTL_LOTTERY,
    }
    return field_ttl_map.get(field, 3600)  # Default 1 hour


def acquire_lock() -> bool:
    """Acquire distributed lock to prevent cache stampede"""
    if not redis_client:
        return True
    return redis_client.set(LOCK_KEY, "1", nx=True, ex=LOCK_TTL)


def release_lock():
    """Release distributed lock"""
    if redis_client:
        redis_client.delete(LOCK_KEY)


def fetch_gold_price() -> tuple[Optional[float], Optional[float], str]:
    """
    Fetch gold price using yfinance (GC=F) or fallback
    Returns: (price, chgPct24h, source) or (None, None, "error")
    """
    try:
        try:
            import yfinance as yf
            ticker = yf.Ticker("GC=F")
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
            print(f"Error fetching gold from yfinance: {e}")
        
        # Fallback: use existing metals service
        from app.services.metals_service import fetch_metals_prices
        data = fetch_metals_prices()
        gold_data = data.get("gold", {})
        if gold_data.get("price", 0) > 0:
            price = gold_data["price"]
            chg_pct = gold_data.get("change_percent", 0.0)
            return (price, chg_pct, "metals_service")
    except Exception as e:
        print(f"Error fetching gold price: {e}")
    
    return (None, None, "error")


def fetch_btc_price() -> tuple[Optional[float], Optional[float], str]:
    """
    Fetch BTC price using yfinance or fallback
    Returns: (price, chgPct24h, source) or (None, None, "error")
    """
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
        if data.get("price", 0) > 0:
            price = data["price"]
            chg_pct = data.get("change_percent", 0.0)
            return (price, chg_pct, "crypto_service")
    except Exception as e:
        print(f"Error fetching BTC price: {e}")
    
    return (None, None, "error")


def fetch_powerball_jackpot() -> tuple[Optional[float], Optional[str], Optional[str], str]:
    """
    Fetch Powerball jackpot amount and drawing date
    Returns: (amount_in_usd, game, draw_date, source) or (None, None, None, "error")
    """
    try:
        from app.services.powerball_service import fetch_powerball_info
        data = fetch_powerball_info()
        jackpot_str = data.get("jackpot", "$0")
        next_drawing = data.get("next_drawing")
        
        # Parse jackpot string like "$33M" or "$1.5B" or "$659M"
        import re
        # Try patterns: $33M, $1.5B, 33M, etc.
        match = re.search(r'\$?\s*(\d+(?:\.\d+)?)\s*([BMbm])', jackpot_str, re.IGNORECASE)
        if match:
            amount = float(match.group(1))
            unit = match.group(2).upper()
            if unit == "B":
                amount_usd = amount * 1_000_000_000
            else:  # M
                amount_usd = amount * 1_000_000
            # Parse drawing date if available
            draw_date = None
            if next_drawing:
                try:
                    # Try to parse common date formats
                    from dateutil import parser
                    draw_date = parser.parse(next_drawing).strftime("%Y-%m-%d")
                except:
                    pass
            return (amount_usd, "Powerball", draw_date, "powerball_service")
        # If no match, try to parse as plain number (fallback)
        elif jackpot_str and jackpot_str != "$0":
            # Try to extract just the number
            num_match = re.search(r'(\d+(?:\.\d+)?)', jackpot_str)
            if num_match:
                amount = float(num_match.group(1))
                # Assume millions if < 1000, billions if >= 1000
                if amount < 1000:
                    amount_usd = amount * 1_000_000
                else:
                    amount_usd = amount * 1_000_000_000
                draw_date = None
                if next_drawing:
                    try:
                        from dateutil import parser
                        draw_date = parser.parse(next_drawing).strftime("%Y-%m-%d")
                    except:
                        pass
                return (amount_usd, "Powerball", draw_date, "powerball_service")
    except Exception as e:
        print(f"Error fetching Powerball jackpot: {e}")
        import traceback
        traceback.print_exc()
    
    return (None, None, None, "error")


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


def get_last_known_value(field: str) -> Optional[float]:
    """Get last known good value for a field from cache"""
    if not redis_client:
        return None
    cached = redis_client.get(get_field_cache_key(field))
    if cached:
        try:
            return float(cached)
        except:
            pass
    return None


def store_field_value(field: str, value: float):
    """Store last known good value for a field with field-specific TTL"""
    if redis_client and value:
        ttl = get_field_ttl(field)
        redis_client.setex(get_field_cache_key(field), ttl, str(value))


def fetch_market_snapshot() -> Dict:
    """
    Fetch unified market snapshot with all 5 KPIs
    Uses per-field caching and tracks stale fields
    
    Returns structure compatible with frontend:
    {
        "updatedAt": "ISO",
        "dataSource": {"btc":"live|mock", "gold":"live|mock", "mortgage":"live|mock", "lottery":"live|mock"},
        "btc": {"price": 0, "chgPct24h": 0},
        "gold": {"price": 0, "chgPct24h": 0},
        "mortgage30y": {"rate": 0, "weekDate": "YYYY-MM-DD"},
        "lottery": {"game": "Powerball|Mega Millions|SuperLotto Plus", "jackpot": 0, "drawDate": "YYYY-MM-DD"}
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
            "gold": {"price": 0, "chgPct24h": 0, "stale": False, "ttlSeconds": FIELD_TTL_GOLD},
            "mortgage30y": {"rate": 0, "weekDate": refresh_timestamp.strftime("%Y-%m-%d"), "stale": False, "ttlSeconds": FIELD_TTL_MORTGAGE},
            "lottery": {"game": "Powerball", "jackpot": 0, "drawDate": refresh_timestamp.strftime("%Y-%m-%d"), "stale": False, "ttlSeconds": FIELD_TTL_LOTTERY}
        }
        
        # Fetch each field with fallback to last-known-good
        # Gold
        gold_price, gold_chg, gold_source = fetch_gold_price()
        if gold_price:
            snapshot["gold"]["price"] = round(gold_price, 2)
            snapshot["gold"]["chgPct24h"] = gold_chg if gold_chg is not None else 0.0
            snapshot["gold"]["stale"] = False
            snapshot["dataSource"]["gold"] = "live" if gold_source not in ["cached", "placeholder", "error"] else "mock"
            store_field_value("gold", gold_price)
        else:
            last_gold = get_last_known_value("gold")
            if last_gold:
                snapshot["gold"]["price"] = round(last_gold, 2)
                snapshot["gold"]["chgPct24h"] = 0.0
                snapshot["gold"]["stale"] = True
                snapshot["dataSource"]["gold"] = "mock"
            else:
                snapshot["gold"]["price"] = 2650.0  # Fallback placeholder
                snapshot["gold"]["chgPct24h"] = 0.0
                snapshot["gold"]["stale"] = True
                snapshot["dataSource"]["gold"] = "mock"
        
        # BTC
        btc_price, btc_chg, btc_source = fetch_btc_price()
        if btc_price:
            snapshot["btc"]["price"] = round(btc_price, 0)
            snapshot["btc"]["chgPct24h"] = btc_chg if btc_chg is not None else 0.0
            snapshot["btc"]["stale"] = False
            snapshot["dataSource"]["btc"] = "live" if btc_source not in ["cached", "placeholder", "error"] else "mock"
            store_field_value("btc", btc_price)
        else:
            last_btc = get_last_known_value("btc")
            if last_btc:
                snapshot["btc"]["price"] = round(last_btc, 0)
                snapshot["btc"]["chgPct24h"] = 0.0
                snapshot["btc"]["stale"] = True
                snapshot["dataSource"]["btc"] = "mock"
            else:
                snapshot["btc"]["price"] = 95000.0  # Fallback placeholder
                snapshot["btc"]["chgPct24h"] = 0.0
                snapshot["btc"]["stale"] = True
                snapshot["dataSource"]["btc"] = "mock"
        
        # Powerball / Lottery
        pb_amount, pb_game, pb_draw_date, pb_source = fetch_powerball_jackpot()
        if pb_amount:
            snapshot["lottery"]["jackpot"] = round(pb_amount, 0)
            snapshot["lottery"]["game"] = pb_game or "Powerball"
            snapshot["lottery"]["drawDate"] = pb_draw_date or refresh_timestamp.strftime("%Y-%m-%d")
            snapshot["lottery"]["stale"] = False
            snapshot["dataSource"]["lottery"] = "live" if pb_source not in ["cached", "placeholder", "error"] else "mock"
            store_field_value("powerball", pb_amount)
        else:
            last_pb = get_last_known_value("powerball")
            if last_pb:
                snapshot["lottery"]["jackpot"] = round(last_pb, 0)
                snapshot["lottery"]["game"] = "Powerball"
                snapshot["lottery"]["drawDate"] = refresh_timestamp.strftime("%Y-%m-%d")
                snapshot["lottery"]["stale"] = True
                snapshot["dataSource"]["lottery"] = "mock"
            else:
                snapshot["lottery"]["jackpot"] = 33_000_000  # $33M fallback
                snapshot["lottery"]["game"] = "Powerball"
                snapshot["lottery"]["drawDate"] = refresh_timestamp.strftime("%Y-%m-%d")
                snapshot["lottery"]["stale"] = True
                snapshot["dataSource"]["lottery"] = "mock"
        
        # Mortgage (using Jumbo 7/1 ARM as mortgage30y for now)
        jumbo_rate, jumbo_week_date, jumbo_source = fetch_jumbo_7arm_rate()
        if jumbo_rate:
            snapshot["mortgage30y"]["rate"] = round(jumbo_rate, 2)
            snapshot["mortgage30y"]["weekDate"] = jumbo_week_date or refresh_timestamp.strftime("%Y-%m-%d")
            snapshot["mortgage30y"]["stale"] = False
            snapshot["dataSource"]["mortgage"] = "live" if jumbo_source not in ["cached", "placeholder", "error"] else "mock"
            store_field_value("jumbo_loan", jumbo_rate)
        else:
            last_jumbo = get_last_known_value("jumbo_loan")
            if last_jumbo:
                snapshot["mortgage30y"]["rate"] = round(last_jumbo, 2)
                snapshot["mortgage30y"]["weekDate"] = refresh_timestamp.strftime("%Y-%m-%d")
                snapshot["mortgage30y"]["stale"] = True
                snapshot["dataSource"]["mortgage"] = "mock"
            else:
                snapshot["mortgage30y"]["rate"] = 6.5  # Fallback placeholder
                snapshot["mortgage30y"]["weekDate"] = refresh_timestamp.strftime("%Y-%m-%d")
                snapshot["mortgage30y"]["stale"] = True
                snapshot["dataSource"]["mortgage"] = "mock"
        
        # T-bill (not in new format, but keep for backward compatibility)
        tbill_rate, tbill_source = fetch_tbill_3m_rate()
        if tbill_rate:
            store_field_value("tbill", tbill_rate)
        
        # Determine overall stale status (if any field is stale, mark overall as stale)
        snapshot["stale"] = any([
            snapshot["btc"]["stale"],
            snapshot["gold"]["stale"],
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
            "dataSource": {"btc": "mock", "gold": "mock", "mortgage": "mock", "lottery": "mock"},
            "stale": True,
            "ttlSeconds": SNAPSHOT_CACHE_TTL,
            "btc": {"price": 95000, "chgPct24h": 0, "stale": True, "ttlSeconds": FIELD_TTL_BTC},
            "gold": {"price": 2650, "chgPct24h": 0, "stale": True, "ttlSeconds": FIELD_TTL_GOLD},
            "mortgage30y": {"rate": 6.5, "weekDate": fallback_timestamp.strftime("%Y-%m-%d"), "stale": True, "ttlSeconds": FIELD_TTL_MORTGAGE},
            "lottery": {"game": "Powerball", "jackpot": 33000000, "drawDate": fallback_timestamp.strftime("%Y-%m-%d"), "stale": True, "ttlSeconds": FIELD_TTL_LOTTERY}
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
            "gold": {"price": 0, "chgPct24h": 0, "stale": True},
            "mortgage30y": {"rate": 0, "weekDate": fallback_timestamp.strftime("%Y-%m-%d"), "stale": True},
            "lottery": {"game": "Powerball", "jackpot": 0, "drawDate": fallback_timestamp.strftime("%Y-%m-%d"), "stale": True}
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
        
        return new_format
    except Exception as e:
        print(f"Error converting to new format: {e}")
        # Return safe fallback
        fallback_timestamp = datetime.now(pytz.UTC)
        return {
            "updatedAt": fallback_timestamp.isoformat(),
            "dataSource": {"btc": "mock", "gold": "mock", "mortgage": "mock", "lottery": "mock"},
            "btc": {"price": 95000, "chgPct24h": 0, "stale": True},
            "gold": {"price": 2650, "chgPct24h": 0, "stale": True},
            "mortgage30y": {"rate": 6.5, "weekDate": fallback_timestamp.strftime("%Y-%m-%d"), "stale": True},
            "lottery": {"game": "Powerball", "jackpot": 33000000, "drawDate": fallback_timestamp.strftime("%Y-%m-%d"), "stale": True}
        }

