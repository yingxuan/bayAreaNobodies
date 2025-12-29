import httpx
import os
import redis
import json
from typing import List, Optional, Dict, Tuple
from datetime import datetime, timedelta
from app.schemas import StockNewsItem

# Optional imports - handle gracefully if not installed
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    print("Warning: yfinance not installed. Stock prices will use fallback methods.")

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("Warning: google-generativeai not installed. Financial advice will be unavailable.")

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(REDIS_URL, decode_responses=True) if REDIS_URL else None


def get_stock_price(ticker: str) -> Optional[float]:
    """
    Get current stock price using Yahoo Finance (yfinance)
    Note: Google Finance doesn't have a public API, so we use Yahoo Finance which is the industry standard.
    
    Returns:
        Current price or None if error
    """
    cache_key = f"stock_price:{ticker}"
    
    # Check cache (5 minute cache)
    if redis_client:
        cached = redis_client.get(cache_key)
        if cached:
            try:
                return float(cached)
            except:
                pass
    
    if YFINANCE_AVAILABLE:
        try:
            stock = yf.Ticker(ticker.upper())
            info = stock.info
            
            # Get current price from 'currentPrice' or 'regularMarketPrice'
            current_price = info.get('currentPrice') or info.get('regularMarketPrice')
            
            if current_price:
                price = float(current_price)
                # Cache for 5 minutes
                if redis_client:
                    redis_client.setex(cache_key, 300, str(price))
                return price
        except Exception as e:
            print(f"Error fetching stock price from yfinance for {ticker}: {e}")
    
    # Fallback to Finnhub if available
    if FINNHUB_API_KEY:
        try:
            url = f"https://finnhub.io/api/v1/quote?symbol={ticker.upper()}&token={FINNHUB_API_KEY}"
            with httpx.Client(timeout=5.0) as client:
                response = client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("c"):  # current price
                        price = float(data["c"])
                        if redis_client:
                            redis_client.setex(cache_key, 300, str(price))
                        return price
        except Exception as e:
            print(f"Error fetching stock price from Finnhub for {ticker}: {e}")
    
    return None


def get_stock_daily_trend(ticker: str) -> Tuple[Optional[float], Optional[float]]:
    """
    Get daily price change and change percent using Yahoo Finance
    
    Returns:
        Tuple of (change_amount, change_percent) or (None, None) if error
    """
    cache_key = f"stock_trend:{ticker}"
    
    # Check cache (5 minute cache)
    if redis_client:
        cached = redis_client.get(cache_key)
        if cached:
            try:
                data = json.loads(cached)
                return data.get('change'), data.get('change_percent')
            except:
                pass
    
    if YFINANCE_AVAILABLE:
        try:
            stock = yf.Ticker(ticker.upper())
            hist = stock.history(period="2d")  # Get last 2 days to calculate change
            
            if len(hist) >= 2:
                # Get today's and yesterday's close prices
                today_close = hist.iloc[-1]['Close']
                yesterday_close = hist.iloc[-2]['Close']
                
                change = float(today_close - yesterday_close)
                change_percent = float((change / yesterday_close) * 100) if yesterday_close > 0 else 0.0
                
                # Cache for 5 minutes
                if redis_client:
                    redis_client.setex(
                        cache_key,
                        300,
                        json.dumps({'change': change, 'change_percent': change_percent})
                    )
                
                return change, change_percent
            elif len(hist) == 1:
                # Only one day of data, use current price vs previous close
                current_price = get_stock_price(ticker)
                if current_price:
                    prev_close = hist.iloc[0]['Close']
                    change = float(current_price - prev_close)
                    change_percent = float((change / prev_close) * 100) if prev_close > 0 else 0.0
                    
                    if redis_client:
                        redis_client.setex(
                            cache_key,
                            300,
                            json.dumps({'change': change, 'change_percent': change_percent})
                        )
                    
                    return change, change_percent
        except Exception as e:
            print(f"Error fetching stock trend from yfinance for {ticker}: {e}")
    
    return None, None


def get_stock_intraday_data(ticker: str) -> Optional[List[Dict[str, float]]]:
    """
    Get intraday price data for the current day using Yahoo Finance
    
    Returns:
        List of dicts with 'time' and 'price' keys, or None if error
    """
    cache_key = f"stock_intraday:{ticker}"
    
    # Check cache (2 minute cache for intraday data)
    if redis_client:
        cached = redis_client.get(cache_key)
        if cached:
            try:
                return json.loads(cached)
            except:
                pass
    
    if YFINANCE_AVAILABLE:
        try:
            stock = yf.Ticker(ticker.upper())
            # Get intraday data (1 minute intervals for today)
            hist = stock.history(period="1d", interval="1m")
            
            if len(hist) > 0:
                intraday_data = []
                for idx, row in hist.iterrows():
                    intraday_data.append({
                        'time': idx.timestamp(),
                        'price': float(row['Close'])
                    })
                
                # Cache for 2 minutes
                if redis_client:
                    redis_client.setex(
                        cache_key,
                        120,
                        json.dumps(intraday_data)
                    )
                
                return intraday_data
        except Exception as e:
            print(f"Error fetching intraday data from yfinance for {ticker}: {e}")
    
    return None


def get_stock_financial_metrics(ticker: str) -> Dict[str, Optional[any]]:
    """
    Get forward PE ratio and next earnings date using Yahoo Finance and Finnhub
    
    Returns:
        Dict with 'forward_pe' and 'next_er_date' keys
    """
    cache_key = f"stock_financial:{ticker}"
    
    # Check cache (1 hour cache for financial metrics)
    if redis_client:
        cached = redis_client.get(cache_key)
        if cached:
            try:
                return json.loads(cached)
            except:
                pass
    
    result = {
        'forward_pe': None,
        'next_er_date': None
    }
    
    # Try Finnhub first (more reliable, no rate limits if you have API key)
    if FINNHUB_API_KEY:
        try:
            # Get company profile for PE ratio
            url = f"https://finnhub.io/api/v1/stock/metric"
            params = {
                "symbol": ticker.upper(),
                "metric": "all",
                "token": FINNHUB_API_KEY
            }
            with httpx.Client(timeout=5.0) as client:
                response = client.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("metric"):
                        metric = data["metric"]
                        # Try to get PE ratio
                        if metric.get("peForwardTTM"):
                            result['forward_pe'] = float(metric["peForwardTTM"])
                        elif metric.get("peTTM"):
                            result['forward_pe'] = float(metric["peTTM"])
            
            # Get earnings calendar
            url = f"https://finnhub.io/api/v1/stock/earnings-calendar"
            params = {
                "symbol": ticker.upper(),
                "from": datetime.now().strftime("%Y-%m-%d"),
                "to": (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d"),
                "token": FINNHUB_API_KEY
            }
            with httpx.Client(timeout=5.0) as client:
                response = client.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("earningsCalendar") and len(data["earningsCalendar"]) > 0:
                        next_er = data["earningsCalendar"][0]
                        if next_er.get("date"):
                            result['next_er_date'] = next_er["date"]
            
            # If we got data from Finnhub, cache and return
            if result['forward_pe'] or result['next_er_date']:
                if redis_client:
                    redis_client.setex(
                        cache_key,
                        3600,
                        json.dumps(result)
                    )
                return result
        except Exception as e:
            print(f"Error fetching financial metrics from Finnhub for {ticker}: {e}")
    
    # Fallback to Yahoo Finance
    if YFINANCE_AVAILABLE:
        try:
            import time
            stock = yf.Ticker(ticker.upper())
            
            # Add delay to avoid rate limiting (longer delay for financial metrics)
            time.sleep(0.5)
            
            try:
                info = stock.info
            except Exception as e:
                print(f"Error getting info for {ticker}: {e}")
                # Try to get basic info without full info
                try:
                    fast_info = stock.fast_info
                    if fast_info:
                        info = {}
                        # Try to get PE from fast_info
                        if hasattr(fast_info, 'trailingPE'):
                            result['forward_pe'] = float(fast_info.trailingPE) if fast_info.trailingPE else None
                except:
                    pass
                return result
            
            if not info:
                print(f"No info available for {ticker}")
                return result
            
            # Get forward PE - try multiple fields
            forward_pe = None
            
            # Debug: print available keys
            pe_keys = [k for k in info.keys() if 'PE' in k.upper() or 'RATIO' in k.upper()]
            if pe_keys:
                print(f"Available PE keys for {ticker}: {pe_keys}")
            
            # Try forwardPE first
            if 'forwardPE' in info:
                pe_val = info.get('forwardPE')
                if pe_val and pe_val != 'N/A' and pe_val != 'None':
                    try:
                        forward_pe = float(pe_val)
                        result['forward_pe'] = forward_pe
                        print(f"Found forwardPE for {ticker}: {forward_pe}")
                    except (ValueError, TypeError) as e:
                        print(f"Error converting forwardPE for {ticker}: {e}, value: {pe_val}")
            
            # Fallback to trailingPE
            if not forward_pe and 'trailingPE' in info:
                pe_val = info.get('trailingPE')
                if pe_val and pe_val != 'N/A' and pe_val != 'None':
                    try:
                        forward_pe = float(pe_val)
                        result['forward_pe'] = forward_pe
                        print(f"Using trailingPE for {ticker}: {forward_pe}")
                    except (ValueError, TypeError) as e:
                        print(f"Error converting trailingPE for {ticker}: {e}, value: {pe_val}")
            
            # Try priceToBookTrailing12Months as last resort
            if not forward_pe and 'priceToBookTrailing12Months' in info:
                try:
                    pb = info.get('priceToBookTrailing12Months')
                    if pb and pb != 'N/A':
                        # This is P/B, not P/E, but better than nothing
                        pass
                except:
                    pass
            
            # Get next earnings date - try multiple methods
            earnings_date = None
            
            # Debug: print available earnings keys
            er_keys = [k for k in info.keys() if 'earn' in k.lower() or 'calendar' in k.lower()]
            if er_keys:
                print(f"Available earnings keys for {ticker}: {er_keys}")
            
            # Method 1: earningsDate field
            if 'earningsDate' in info:
                earnings_dates = info.get('earningsDate')
                print(f"earningsDate for {ticker}: {earnings_dates}, type: {type(earnings_dates)}")
                if isinstance(earnings_dates, list) and len(earnings_dates) > 0:
                    earnings_date = earnings_dates[0]
                elif isinstance(earnings_dates, (int, float)):
                    earnings_date = earnings_dates
            
            # Method 2: earningsCalendar field
            if not earnings_date and info.get('earningsCalendar'):
                earnings_cal = info.get('earningsCalendar')
                if isinstance(earnings_cal, dict) and earnings_cal.get('earningsDate'):
                    earnings_date = earnings_cal.get('earningsDate')
                    if isinstance(earnings_date, list) and len(earnings_date) > 0:
                        earnings_date = earnings_date[0]
            
            # Method 3: Try calendar DataFrame
            if not earnings_date:
                try:
                    time.sleep(0.1)  # Add delay
                    calendar = stock.calendar
                    if calendar is not None and len(calendar) > 0:
                        # Get the next earnings date
                        next_earnings = calendar.iloc[0]
                        if 'Earnings Date' in next_earnings.index:
                            earnings_date = next_earnings['Earnings Date']
                        elif 'EarningsDate' in next_earnings.index:
                            earnings_date = next_earnings['EarningsDate']
                except Exception as e:
                    print(f"Error getting calendar for {ticker}: {e}")
            
            # Method 5: Try using Finnhub as fallback for earnings date
            if not earnings_date and FINNHUB_API_KEY:
                try:
                    url = f"https://finnhub.io/api/v1/stock/earnings-calendar"
                    params = {
                        "symbol": ticker.upper(),
                        "from": datetime.now().strftime("%Y-%m-%d"),
                        "to": (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d"),
                        "token": FINNHUB_API_KEY
                    }
                    with httpx.Client(timeout=5.0) as client:
                        response = client.get(url, params=params)
                        if response.status_code == 200:
                            data = response.json()
                            if data.get("earningsCalendar") and len(data["earningsCalendar"]) > 0:
                                next_er = data["earningsCalendar"][0]
                                if next_er.get("date"):
                                    earnings_date = next_er["date"]
                except Exception as e:
                    print(f"Error getting earnings from Finnhub for {ticker}: {e}")
            
            # Method 4: Try earningsDates field
            if not earnings_date and info.get('earningsDates'):
                earnings_dates = info.get('earningsDates')
                if isinstance(earnings_dates, list) and len(earnings_dates) > 0:
                    earnings_date = earnings_dates[0]
            
            if earnings_date:
                # Convert to datetime if it's a timestamp
                try:
                    if isinstance(earnings_date, (int, float)):
                        result['next_er_date'] = datetime.fromtimestamp(earnings_date).isoformat()
                    elif isinstance(earnings_date, datetime):
                        result['next_er_date'] = earnings_date.isoformat()
                    elif isinstance(earnings_date, str):
                        # Try to parse string date
                        try:
                            dt = datetime.fromisoformat(earnings_date.replace('Z', '+00:00'))
                            result['next_er_date'] = dt.isoformat()
                        except:
                            result['next_er_date'] = earnings_date
                    else:
                        result['next_er_date'] = str(earnings_date)
                    print(f"Found earnings date for {ticker}: {result['next_er_date']}")
                except Exception as e:
                    print(f"Error parsing earnings date for {ticker}: {e}")
            
            # Cache for 1 hour
            if redis_client:
                redis_client.setex(
                    cache_key,
                    3600,
                    json.dumps(result)
                )
        except Exception as e:
            print(f"Error fetching financial metrics from yfinance for {ticker}: {e}")
            import traceback
            traceback.print_exc()
    
    return result


def get_stock_news(ticker: str, range_hours: int = 24) -> List[StockNewsItem]:
    """
    Get stock news from Yahoo Finance and Finnhub
    
    Args:
        ticker: Stock ticker symbol
        range_hours: Time range in hours
    
    Returns:
        List of StockNewsItem
    """
    cache_key = f"stock_news:{ticker}:{range_hours}"
    
    # Check cache (15 minute cache)
    if redis_client:
        cached = redis_client.get(cache_key)
        if cached:
            try:
                data = json.loads(cached)
                return [StockNewsItem(**item) for item in data]
            except:
                pass
    
    news_items = []
    
    # Try Yahoo Finance first
    if YFINANCE_AVAILABLE:
        try:
            stock = yf.Ticker(ticker.upper())
            news = stock.news
            
            for item in news[:10]:  # Limit to 10 items
                try:
                    published_at = None
                    if item.get("providerPublishTime"):
                        published_at = datetime.fromtimestamp(item["providerPublishTime"])
                    
                    news_items.append(StockNewsItem(
                        headline=item.get("title", ""),
                        summary=item.get("summary", ""),
                        url=item.get("link", ""),
                        published_at=published_at,
                        source=item.get("publisher", "Yahoo Finance")
                    ))
                except Exception as e:
                    print(f"Error parsing news item for {ticker}: {e}")
                    continue
        except Exception as e:
            print(f"Error fetching news from Yahoo Finance for {ticker}: {e}")
    
    # Fallback to Finnhub if available and we don't have enough news
    if len(news_items) < 5 and FINNHUB_API_KEY:
        try:
            url = f"https://finnhub.io/api/v1/company-news"
            params = {
                "symbol": ticker.upper(),
                "from": (datetime.now() - timedelta(hours=range_hours)).strftime("%Y-%m-%d"),
                "to": datetime.now().strftime("%Y-%m-%d"),
                "token": FINNHUB_API_KEY
            }
            
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    for item in data[:10]:  # Limit to 10 items
                        try:
                            published_at = None
                            if item.get("datetime"):
                                published_at = datetime.fromtimestamp(item["datetime"])
                            
                            news_items.append(StockNewsItem(
                                headline=item.get("headline", ""),
                                summary=item.get("summary", ""),
                                url=item.get("url", ""),
                                published_at=published_at,
                                source=item.get("source", "Finnhub")
                            ))
                        except Exception:
                            continue
        except Exception as e:
            print(f"Error fetching stock news from Finnhub: {e}")
    
    # Cache for 15 minutes
    if redis_client and news_items:
        redis_client.setex(
            cache_key,
            900,
            json.dumps([item.dict() for item in news_items])
        )
    
    return news_items


def get_financial_advice(ticker: str, current_price: Optional[float], 
                         change_percent: float, news_items: List[StockNewsItem]) -> Optional[str]:
    """
    Get financial advice from Gemini AI based on stock data
    
    Args:
        ticker: Stock ticker symbol
        current_price: Current stock price
        change_percent: Daily change percent
        news_items: Recent news items
    
    Returns:
        Financial advice string or None if error
    """
    if not GEMINI_API_KEY or not GEMINI_AVAILABLE:
        return None
    
    cache_key = f"stock_advice:{ticker}"
    
    # Check cache (1 hour cache)
    if redis_client:
        cached = redis_client.get(cache_key)
        if cached:
            return cached
    
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-pro')
        
        # Build context for Gemini
        price_info = f"Current price: ${current_price:.2f}" if current_price else "Price: N/A"
        change_info = f"Daily change: {change_percent:+.2f}%"
        
        news_summaries = []
        for news in news_items[:5]:  # Top 5 news items
            news_summaries.append(f"- {news.headline}")
        
        news_text = "\n".join(news_summaries) if news_summaries else "No recent news available."
        
        prompt = f"""You are a financial advisor. Provide a brief, actionable financial analysis for {ticker} stock.

Stock: {ticker}
{price_info}
{change_info}

Recent News:
{news_text}

Please provide:
1. A brief assessment of the stock's current situation (2-3 sentences)
2. Key factors to watch (2-3 bullet points)
3. A concise recommendation (1-2 sentences): Buy, Hold, or Sell

Keep the response under 200 words and be practical and data-driven."""

        response = model.generate_content(prompt)
        advice = response.text.strip()
        
        # Cache for 1 hour
        if redis_client:
            redis_client.setex(cache_key, 3600, advice)
        
        return advice
    except Exception as e:
        print(f"Error getting financial advice from Gemini for {ticker}: {e}")
        return None
