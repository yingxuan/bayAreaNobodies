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
        # Use gemini-2.0-flash for fast responses
        model = genai.GenerativeModel('gemini-2.0-flash')
        
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


def get_portfolio_advice(holdings: List[Dict], total_value: float, total_pnl: float, 
                         total_pnl_percent: float, day_gain: float, day_gain_percent: float) -> Optional[str]:
    """
    Get investment advice from Gemini AI based on entire portfolio
    
    Args:
        holdings: List of holding dictionaries with ticker, quantity, current_price, total_gain, etc.
        total_value: Total portfolio value
        total_pnl: Total profit/loss
        total_pnl_percent: Total P&L percentage
        day_gain: Today's gain/loss
        day_gain_percent: Today's gain/loss percentage
    
    Returns:
        Investment advice string or None if error
    """
    if not GEMINI_API_KEY or not GEMINI_AVAILABLE:
        return None
    
    # Use date-based cache key to ensure only one query per day
    from datetime import datetime
    today = datetime.now().strftime("%Y%m%d")
    cache_key = f"portfolio_advice:{today}"
    
    # Check cache (24 hour cache - one query per day)
    if redis_client:
        cached = redis_client.get(cache_key)
        if cached:
            return cached
    
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        # Use gemini-2.0-flash for fast responses
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Build portfolio summary
        holdings_summary = []
        for holding in holdings[:10]:  # Top 10 holdings
            ticker = holding.get('ticker') or 'N/A'
            quantity = holding.get('quantity') or 0
            price = holding.get('current_price') or 0
            value = holding.get('value') or 0
            total_gain = holding.get('total_gain') or 0
            total_gain_percent = holding.get('total_gain_percent') or 0
            day_gain = holding.get('day_gain') or 0
            day_gain_percent = holding.get('day_gain_percent') or 0
            
            # Ensure all values are numeric (handle None values)
            try:
                quantity = float(quantity) if quantity is not None else 0.0
                price = float(price) if price is not None else 0.0
                value = float(value) if value is not None else 0.0
                total_gain = float(total_gain) if total_gain is not None else 0.0
                total_gain_percent = float(total_gain_percent) if total_gain_percent is not None else 0.0
                day_gain = float(day_gain) if day_gain is not None else 0.0
                day_gain_percent = float(day_gain_percent) if day_gain_percent is not None else 0.0
            except (ValueError, TypeError):
                # If conversion fails, use defaults
                quantity = 0.0
                price = 0.0
                value = 0.0
                total_gain = 0.0
                total_gain_percent = 0.0
                day_gain = 0.0
                day_gain_percent = 0.0
            
            holdings_summary.append(
                f"- {ticker}: {quantity} shares @ ${price:.2f}, "
                f"Value: ${value:.2f}, "
                f"Total Gain: ${total_gain:.2f} ({total_gain_percent:+.2f}%), "
                f"Today: ${day_gain:.2f} ({day_gain_percent:+.2f}%)"
            )
        
        holdings_text = "\n".join(holdings_summary) if holdings_summary else "No holdings"
        
        # Get current date for context
        from datetime import datetime
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        prompt = f"""你是一名专业的理财专家，非常熟悉最新的金融股市房地产政策和形势。请注意，**一定要根据最新的经济政治形势和我的实时持仓信息，给出切实的理财建议。不要有模式化的回答**。

投资组合概况（截至 {current_date}）：
- 总资产价值：${total_value:,.2f}
- 总盈亏：${total_pnl:,.2f} ({total_pnl_percent:+.2f}%)
- 今日盈亏：${day_gain:,.2f} ({day_gain_percent:+.2f}%)

当前持仓：
{holdings_text}

请基于以下要求提供专业的投资建议：
1. **结合最新经济政治形势**：分析当前宏观经济环境、货币政策、地缘政治等因素对投资组合的影响
2. **针对具体持仓分析**：对每只股票或主要持仓给出具体评价，不要泛泛而谈
3. **提供切实可行的建议**：给出具体的操作建议（如加仓、减仓、调仓），并说明理由
4. **风险评估**：指出当前投资组合的主要风险点
5. **市场展望**：结合最新市场动态，给出短期和中期展望

**重要提示**：
- 必须结合最新的经济政治形势，不要使用过时的信息
- 必须针对我的具体持仓给出建议，不要使用模板化的回答
- 建议要具体、可操作，避免空泛的表述
- 总字数控制在 400-600 字"""
        
        response = model.generate_content(prompt)
        advice = response.text.strip()
        
        # Cache for 24 hours (one query per day)
        if redis_client:
            # Set cache to expire at end of day (86400 seconds = 24 hours)
            redis_client.setex(cache_key, 86400, advice)
        
        return advice
    except Exception as e:
        error_msg = str(e)
        print(f"Error getting portfolio advice from Gemini: {error_msg}")
        
        # Log more details for debugging
        if "API_KEY" in error_msg or "api_key" in error_msg.lower():
            print("GEMINI_API_KEY may be missing or invalid")
        elif "quota" in error_msg.lower() or "rate" in error_msg.lower() or "429" in error_msg:
            print("Gemini API quota or rate limit exceeded")
            print("This may be due to:")
            print("  1. Free tier quota exhausted (wait for daily reset)")
            print("  2. Rate limit exceeded (wait a few minutes)")
            print("  3. Need to upgrade to paid plan")
        else:
            import traceback
            traceback.print_exc()
        
        return None
