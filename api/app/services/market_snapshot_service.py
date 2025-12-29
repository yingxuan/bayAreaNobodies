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

# Cache TTL: 15 minutes for snapshot, longer for individual fields
SNAPSHOT_CACHE_TTL = 900  # 15 minutes
FIELD_CACHE_TTL = 3600  # 1 hour for last-known-good values

# Lock key to prevent cache stampede
LOCK_KEY = "market:snapshot:lock"
LOCK_TTL = 30  # 30 seconds


def get_snapshot_cache_key() -> str:
    """Get Redis key for full snapshot cache"""
    return "market:snapshot:full"


def get_field_cache_key(field: str) -> str:
    """Get Redis key for individual field last-known-good value"""
    return f"market:snapshot:field:{field}"


def acquire_lock() -> bool:
    """Acquire distributed lock to prevent cache stampede"""
    if not redis_client:
        return True
    return redis_client.set(LOCK_KEY, "1", nx=True, ex=LOCK_TTL)


def release_lock():
    """Release distributed lock"""
    if redis_client:
        redis_client.delete(LOCK_KEY)


def fetch_gold_price() -> tuple[Optional[float], str]:
    """
    Fetch gold price using yfinance (GC=F) or fallback
    Returns: (price, source) or (None, "error")
    """
    try:
        try:
            import yfinance as yf
            ticker = yf.Ticker("GC=F")
            hist = ticker.history(period="1d", interval="1m")
            if len(hist) > 0:
                price = float(hist.iloc[-1]['Close'])
                return (price, "yfinance")
        except ImportError:
            pass
        except Exception as e:
            print(f"Error fetching gold from yfinance: {e}")
        
        # Fallback: use existing metals service
        from app.services.metals_service import fetch_metals_prices
        data = fetch_metals_prices()
        if data.get("gold", {}).get("price", 0) > 0:
            return (data["gold"]["price"], "metals_service")
    except Exception as e:
        print(f"Error fetching gold price: {e}")
    
    return (None, "error")


def fetch_btc_price() -> tuple[Optional[float], str]:
    """
    Fetch BTC price using yfinance or fallback
    Returns: (price, source) or (None, "error")
    """
    try:
        try:
            import yfinance as yf
            ticker = yf.Ticker("BTC-USD")
            hist = ticker.history(period="1d", interval="1m")
            if len(hist) > 0:
                price = float(hist.iloc[-1]['Close'])
                return (price, "yfinance")
        except ImportError:
            pass
        except Exception as e:
            print(f"Error fetching BTC from yfinance: {e}")
        
        # Fallback: use existing crypto service
        from app.services.crypto_service import fetch_btc_price
        data = fetch_btc_price()
        if data.get("price", 0) > 0:
            return (data["price"], "crypto_service")
    except Exception as e:
        print(f"Error fetching BTC price: {e}")
    
    return (None, "error")


def fetch_powerball_jackpot() -> tuple[Optional[float], str]:
    """
    Fetch Powerball jackpot amount
    Returns: (amount_in_usd, source) or (None, "error")
    """
    try:
        from app.services.powerball_service import fetch_powerball_info
        data = fetch_powerball_info()
        jackpot_str = data.get("jackpot", "$0")
        
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
            return (amount_usd, "powerball_service")
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
                return (amount_usd, "powerball_service")
    except Exception as e:
        print(f"Error fetching Powerball jackpot: {e}")
        import traceback
        traceback.print_exc()
    
    return (None, "error")


def fetch_jumbo_7arm_rate() -> tuple[Optional[float], str]:
    """
    Fetch CA Jumbo 7/1 ARM rate
    Returns: (rate, source) or (None, "error")
    """
    try:
        from app.services.loan_service import fetch_jumbo_7arm_rate
        data = fetch_jumbo_7arm_rate()
        rate = data.get("rate", 0)
        if rate > 0:
            return (rate, "loan_service")
    except Exception as e:
        print(f"Error fetching Jumbo 7/1 ARM rate: {e}")
    
    return (None, "error")


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
    """Store last known good value for a field"""
    if redis_client and value:
        redis_client.setex(get_field_cache_key(field), FIELD_CACHE_TTL, str(value))


def fetch_market_snapshot() -> Dict:
    """
    Fetch unified market snapshot with all 5 KPIs
    Uses per-field caching and tracks stale fields
    """
    # Check full snapshot cache first
    if redis_client:
        cached = redis_client.get(get_snapshot_cache_key())
        if cached:
            try:
                return json.loads(cached)
            except:
                pass
    
    # Acquire lock to prevent cache stampede
    if not acquire_lock():
        # If lock exists, return cached data if available
        if redis_client:
            cached = redis_client.get(get_snapshot_cache_key())
            if cached:
                try:
                    return json.loads(cached)
                except:
                    pass
    
    try:
        snapshot = {
            "gold_usd_per_oz": None,
            "btc_usd": None,
            "powerball_jackpot_usd": None,
            "ca_jumbo_7_1_arm_rate": None,
            "t_bill_3m_rate": None,
            "as_of": datetime.now(pytz.UTC).isoformat(),
            "stale_fields": [],
            "sources": {}
        }
        
        # Fetch each field with fallback to last-known-good
        # Gold
        gold_price, gold_source = fetch_gold_price()
        if gold_price:
            snapshot["gold_usd_per_oz"] = round(gold_price, 2)
            snapshot["sources"]["gold"] = gold_source
            store_field_value("gold", gold_price)
        else:
            last_gold = get_last_known_value("gold")
            if last_gold:
                snapshot["gold_usd_per_oz"] = round(last_gold, 2)
                snapshot["stale_fields"].append("gold_usd_per_oz")
                snapshot["sources"]["gold"] = "cached"
            else:
                snapshot["gold_usd_per_oz"] = 2650.0  # Fallback placeholder
                snapshot["stale_fields"].append("gold_usd_per_oz")
                snapshot["sources"]["gold"] = "placeholder"
        
        # BTC
        btc_price, btc_source = fetch_btc_price()
        if btc_price:
            snapshot["btc_usd"] = round(btc_price, 0)
            snapshot["sources"]["btc"] = btc_source
            store_field_value("btc", btc_price)
        else:
            last_btc = get_last_known_value("btc")
            if last_btc:
                snapshot["btc_usd"] = round(last_btc, 0)
                snapshot["stale_fields"].append("btc_usd")
                snapshot["sources"]["btc"] = "cached"
            else:
                snapshot["btc_usd"] = 95000.0  # Fallback placeholder
                snapshot["stale_fields"].append("btc_usd")
                snapshot["sources"]["btc"] = "placeholder"
        
        # Powerball
        pb_amount, pb_source = fetch_powerball_jackpot()
        if pb_amount:
            snapshot["powerball_jackpot_usd"] = round(pb_amount, 0)
            snapshot["sources"]["powerball"] = pb_source
            store_field_value("powerball", pb_amount)
        else:
            last_pb = get_last_known_value("powerball")
            if last_pb:
                snapshot["powerball_jackpot_usd"] = round(last_pb, 0)
                snapshot["stale_fields"].append("powerball_jackpot_usd")
                snapshot["sources"]["powerball"] = "cached"
            else:
                snapshot["powerball_jackpot_usd"] = 33_000_000  # $33M fallback
                snapshot["stale_fields"].append("powerball_jackpot_usd")
                snapshot["sources"]["powerball"] = "placeholder"
        
        # Jumbo Loan
        jumbo_rate, jumbo_source = fetch_jumbo_7arm_rate()
        if jumbo_rate:
            snapshot["ca_jumbo_7_1_arm_rate"] = round(jumbo_rate, 2)
            snapshot["sources"]["mortgage"] = jumbo_source
            store_field_value("jumbo_loan", jumbo_rate)
        else:
            last_jumbo = get_last_known_value("jumbo_loan")
            if last_jumbo:
                snapshot["ca_jumbo_7_1_arm_rate"] = round(last_jumbo, 2)
                snapshot["stale_fields"].append("ca_jumbo_7_1_arm_rate")
                snapshot["sources"]["mortgage"] = "cached"
            else:
                snapshot["ca_jumbo_7_1_arm_rate"] = 6.5  # Fallback placeholder
                snapshot["stale_fields"].append("ca_jumbo_7_1_arm_rate")
                snapshot["sources"]["mortgage"] = "placeholder"
        
        # T-bill
        tbill_rate, tbill_source = fetch_tbill_3m_rate()
        if tbill_rate:
            snapshot["t_bill_3m_rate"] = round(tbill_rate, 2)
            snapshot["sources"]["t_bill"] = tbill_source
            store_field_value("tbill", tbill_rate)
        else:
            last_tbill = get_last_known_value("tbill")
            if last_tbill:
                snapshot["t_bill_3m_rate"] = round(last_tbill, 2)
                snapshot["stale_fields"].append("t_bill_3m_rate")
                snapshot["sources"]["t_bill"] = "cached"
            else:
                snapshot["t_bill_3m_rate"] = 5.2  # Fallback placeholder
                snapshot["stale_fields"].append("t_bill_3m_rate")
                snapshot["sources"]["t_bill"] = "placeholder"
        
        # Remove stale_fields if empty
        if not snapshot["stale_fields"]:
            del snapshot["stale_fields"]
        
        # Cache the full snapshot
        if redis_client:
            redis_client.setex(
                get_snapshot_cache_key(),
                SNAPSHOT_CACHE_TTL,
                json.dumps(snapshot)
            )
        
        return snapshot
        
    finally:
        release_lock()

