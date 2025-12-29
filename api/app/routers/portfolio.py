from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Holding, User
from app.schemas import PortfolioSummary, HoldingCreate, AddPositionRequest, ReducePositionRequest
from app.auth import get_current_user
from app.services.stock_service import get_stock_price, get_stock_daily_trend, get_stock_intraday_data, get_portfolio_advice
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

router = APIRouter()


@router.get("/summary", response_model=PortfolioSummary)
def get_portfolio_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    holdings = db.query(Holding).filter(Holding.user_id == current_user.id).all()
    
    total_cost = sum(h.cost_basis for h in holdings)
    total_value = 0.0
    holdings_data = []
    
    for holding in holdings:
        try:
            current_price = get_stock_price(holding.ticker)
            value = current_price * holding.quantity
            total_value += value
            pnl = value - holding.cost_basis
            pnl_percent = (pnl / holding.cost_basis * 100) if holding.cost_basis > 0 else 0
            
            holdings_data.append({
                "ticker": holding.ticker,
                "quantity": holding.quantity,
                "cost_basis": holding.cost_basis,
                "current_price": current_price,
                "value": value,
                "pnl": pnl,
                "pnl_percent": pnl_percent,
                "tags": holding.tags
            })
        except Exception as e:
            # If price fetch fails, use cost basis as value
            holdings_data.append({
                "ticker": holding.ticker,
                "quantity": holding.quantity,
                "cost_basis": holding.cost_basis,
                "current_price": None,
                "value": holding.cost_basis,
                "pnl": 0,
                "pnl_percent": 0,
                "tags": holding.tags,
                "error": str(e)
            })
            total_value += holding.cost_basis
    
    total_pnl = total_value - total_cost
    total_pnl_percent = (total_pnl / total_cost * 100) if total_cost > 0 else 0
    
    return PortfolioSummary(
        total_cost=total_cost,
        total_value=total_value,
        total_pnl=total_pnl,
        total_pnl_percent=total_pnl_percent,
        holdings=holdings_data
    )


@router.get("/csv-summary")
def get_csv_portfolio_summary():
    """
    Get portfolio summary from stock_holdings.csv file (no authentication required)
    Returns holdings with current prices, daily changes, and portfolio metrics
    """
    # Try multiple possible paths for CSV file
    possible_paths = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "stock_holdings.csv"),  # Project root
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "stock_holdings.csv"),  # api/ directory
        "/app/stock_holdings.csv",  # Docker container path
        "stock_holdings.csv"  # Current directory
    ]
    
    csv_path = None
    for path in possible_paths:
        if os.path.exists(path):
            csv_path = path
            break
    
    if not os.path.exists(csv_path):
        return {
            "total_cost": 0,
            "total_value": 0,
            "total_pnl": 0,
            "total_pnl_percent": 0,
            "day_gain": 0,
            "day_gain_percent": 0,
            "holdings": []
        }
    
    holdings_data = []
    total_cost = 0.0
    total_value = 0.0
    total_day_gain = 0.0
    
    # Read CSV file
    with open(csv_path, 'r') as f:
        lines = f.readlines()
        for line in lines:
            line = line.strip()
            if not line:
                continue
            parts = line.split(',')
            if len(parts) < 3:
                continue
            
            ticker = parts[0].strip()
            quantity = float(parts[1].strip())
            cost_basis_per_share = float(parts[2].strip())
            
            total_cost_per_holding = quantity * cost_basis_per_share
            total_cost += total_cost_per_holding
            
            # Get current price and daily trend (skip intraday for faster loading)
            current_price = get_stock_price(ticker)
            change_amount, change_percent = get_stock_daily_trend(ticker)
            # Skip intraday_data - load lazily if needed
            
            if current_price:
                value = current_price * quantity
                total_value += value
                
                # Calculate day gain for this holding
                if change_amount is not None:
                    day_gain = change_amount * quantity
                    total_day_gain += day_gain
                else:
                    day_gain = None
                
                pnl = value - total_cost_per_holding
                pnl_percent = (pnl / total_cost_per_holding * 100) if total_cost_per_holding > 0 else 0
                
                holdings_data.append({
                    "ticker": ticker,
                    "quantity": quantity,
                    "cost_basis_per_share": cost_basis_per_share,
                    "total_cost": total_cost_per_holding,
                    "current_price": current_price,
                    "value": value,
                    "day_gain": day_gain,
                    "day_gain_percent": change_percent if change_percent is not None else 0,
                    "total_gain": pnl,
                    "total_gain_percent": pnl_percent,
                    "intraday_data": []  # Load lazily
                })
            else:
                # If price fetch fails, use cost basis
                holdings_data.append({
                    "ticker": ticker,
                    "quantity": quantity,
                    "cost_basis_per_share": cost_basis_per_share,
                    "total_cost": total_cost_per_holding,
                    "current_price": None,
                    "value": total_cost_per_holding,
                    "day_gain": None,
                    "day_gain_percent": 0,
                    "total_gain": 0,
                    "total_gain_percent": 0
                })
                total_value += total_cost_per_holding
    
    total_pnl = total_value - total_cost
    total_pnl_percent = (total_pnl / total_cost * 100) if total_cost > 0 else 0
    day_gain_percent = (total_day_gain / total_value * 100) if total_value > 0 else 0
    
    return {
        "total_cost": total_cost,
        "total_value": total_value,
        "total_pnl": total_pnl,
        "total_pnl_percent": total_pnl_percent,
        "day_gain": total_day_gain,
        "day_gain_percent": day_gain_percent,
        "holdings": holdings_data
    }


def get_or_create_default_user(db: Session) -> User:
    """Get or create a default user for anonymous portfolio tracking"""
    default_user = db.query(User).filter(User.email == "default@portfolio.local").first()
    if not default_user:
        from app.auth import get_password_hash
        try:
            # Use a simple password for default user
            default_user = User(
                email="default@portfolio.local",
                hashed_password=get_password_hash("default123")
            )
            db.add(default_user)
            db.commit()
            db.refresh(default_user)
        except Exception as e:
            print(f"Error creating default user: {e}")
            # If password hashing fails, use a pre-hashed password
            # This is a hash of "default123" using bcrypt
            default_user = User(
                email="default@portfolio.local",
                hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqJZ5q5Z5O"
            )
            db.add(default_user)
            db.commit()
            db.refresh(default_user)
    return default_user


@router.get("/db-summary")
def get_db_portfolio_summary(db: Session = Depends(get_db)):
    """
    Get portfolio summary from database (no authentication required)
    Uses a default user for anonymous tracking
    Falls back to CSV if database is empty
    """
    try:
        default_user = get_or_create_default_user(db)
        if default_user:
            holdings = db.query(Holding).filter(Holding.user_id == default_user.id).all()
        else:
            holdings = []
    except Exception as e:
        print(f"Error accessing database, falling back to CSV: {e}")
        holdings = []
    
    if not holdings:
        # Fall back to CSV file
        return get_csv_portfolio_summary()
        return {
            "total_cost": 0,
            "total_value": 0,
            "total_pnl": 0,
            "total_pnl_percent": 0,
            "day_gain": 0,
            "day_gain_percent": 0,
            "holdings": []
        }
    
    holdings_data = []
    total_cost = 0.0
    total_value = 0.0
    total_day_gain = 0.0
    
    # Calculate total cost first
    for holding in holdings:
        total_cost_per_holding = holding.cost_basis
        total_cost += total_cost_per_holding
    
    # Parallel fetch stock data for faster loading
    def fetch_stock_data(holding):
        """Fetch all data for a single stock"""
        ticker = holding.ticker
        total_cost_per_holding = holding.cost_basis
        
        # Fetch price and trend in parallel
        current_price = get_stock_price(ticker)
        change_amount, change_percent = get_stock_daily_trend(ticker)
        # Skip intraday data for initial load (can be loaded on demand)
        intraday_data = None  # Will be loaded lazily if needed
        
        if current_price:
            value = current_price * holding.quantity
            day_gain = change_amount * holding.quantity if change_amount is not None else None
            pnl = value - total_cost_per_holding
            pnl_percent = (pnl / total_cost_per_holding * 100) if total_cost_per_holding > 0 else 0
            
            return {
                "id": holding.id,
                "ticker": ticker,
                "quantity": holding.quantity,
                "cost_basis_per_share": total_cost_per_holding / holding.quantity if holding.quantity > 0 else 0,
                "total_cost": total_cost_per_holding,
                "current_price": current_price,
                "value": value,
                "day_gain": day_gain,
                "day_gain_percent": change_percent if change_percent is not None else 0,
                "total_gain": pnl,
                "total_gain_percent": pnl_percent,
                "intraday_data": []  # Load lazily
            }, value, day_gain
        else:
            return {
                "id": holding.id,
                "ticker": ticker,
                "quantity": holding.quantity,
                "cost_basis_per_share": total_cost_per_holding / holding.quantity if holding.quantity > 0 else 0,
                "total_cost": total_cost_per_holding,
                "current_price": None,
                "value": total_cost_per_holding,
                "day_gain": None,
                "day_gain_percent": 0,
                "total_gain": 0,
                "total_gain_percent": 0,
                "intraday_data": []
            }, total_cost_per_holding, 0
    
    # Use ThreadPoolExecutor for parallel processing
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_holding = {executor.submit(fetch_stock_data, holding): holding for holding in holdings}
        
        for future in as_completed(future_to_holding):
            try:
                holding_dict, value, day_gain = future.result()
                holdings_data.append(holding_dict)
                total_value += value
                if day_gain is not None:
                    total_day_gain += day_gain
            except Exception as e:
                holding = future_to_holding[future]
                print(f"Error processing {holding.ticker}: {e}")
                # Add placeholder data
                total_cost_per_holding = holding.cost_basis
                holdings_data.append({
                    "id": holding.id,
                    "ticker": holding.ticker,
                    "quantity": holding.quantity,
                    "cost_basis_per_share": total_cost_per_holding / holding.quantity if holding.quantity > 0 else 0,
                    "total_cost": total_cost_per_holding,
                    "current_price": None,
                    "value": total_cost_per_holding,
                    "day_gain": None,
                    "day_gain_percent": 0,
                    "total_gain": 0,
                    "total_gain_percent": 0,
                    "intraday_data": []
                })
                total_value += total_cost_per_holding
    
    total_pnl = total_value - total_cost
    total_pnl_percent = (total_pnl / total_cost * 100) if total_cost > 0 else 0
    day_gain_percent = (total_day_gain / total_value * 100) if total_value > 0 else 0
    
    return {
        "total_cost": total_cost,
        "total_value": total_value,
        "total_pnl": total_pnl,
        "total_pnl_percent": total_pnl_percent,
        "day_gain": total_day_gain,
        "day_gain_percent": day_gain_percent,
        "holdings": holdings_data
    }


@router.get("/intraday/{ticker}")
def get_intraday_data(ticker: str):
    """
    Get intraday data for a specific ticker (lazy loading endpoint)
    """
    intraday_data = get_stock_intraday_data(ticker)
    return {
        "ticker": ticker,
        "intraday_data": intraday_data if intraday_data else []
    }


@router.get("/advice")
def get_portfolio_investment_advice(
    db: Session = Depends(get_db)
):
    """
    Get AI investment advice based on portfolio holdings and market conditions
    """
    # Get portfolio data (using default user)
    default_user = get_or_create_default_user(db)
    if not default_user:
        return {"advice": None, "error": "Could not create default user"}
    
    holdings = db.query(Holding).filter(Holding.user_id == default_user.id).all()
    
    if not holdings:
        # Fallback to CSV if no DB holdings
        try:
            csv_data = get_csv_portfolio_summary()
            if csv_data and csv_data.get('holdings'):
                holdings_list = csv_data['holdings']
                total_value = csv_data.get('total_value', 0)
                total_pnl = csv_data.get('total_pnl', 0)
                total_pnl_percent = csv_data.get('total_pnl_percent', 0)
                day_gain = csv_data.get('day_gain', 0)
                day_gain_percent = csv_data.get('day_gain_percent', 0)
                
                advice = get_portfolio_advice(
                    holdings_list,
                    total_value,
                    total_pnl,
                    total_pnl_percent,
                    day_gain,
                    day_gain_percent
                )
                return {"advice": advice}
        except Exception as e:
            print(f"Error getting CSV portfolio for advice: {e}")
        
        return {"advice": None, "error": "No holdings found"}
    
    # Calculate portfolio summary
    total_cost = sum(h.cost_basis for h in holdings)
    holdings_data = []
    total_value = 0.0
    total_day_gain = 0.0
    
    for holding in holdings:
        current_price = get_stock_price(holding.ticker)
        change_amount, change_percent = get_stock_daily_trend(holding.ticker)
        
        if current_price:
            value = current_price * holding.quantity
            total_value += value
            day_gain = change_amount * holding.quantity if change_amount is not None else 0
            total_day_gain += day_gain
            
            pnl = value - holding.cost_basis
            pnl_percent = (pnl / holding.cost_basis * 100) if holding.cost_basis > 0 else 0
            
            holdings_data.append({
                "ticker": holding.ticker,
                "quantity": holding.quantity,
                "current_price": current_price,
                "value": value,
                "total_gain": pnl,
                "total_gain_percent": pnl_percent,
                "day_gain": day_gain,
                "day_gain_percent": change_percent if change_percent is not None else 0
            })
        else:
            holdings_data.append({
                "ticker": holding.ticker,
                "quantity": holding.quantity,
                "current_price": None,
                "value": holding.cost_basis,
                "total_gain": 0,
                "total_gain_percent": 0,
                "day_gain": 0,
                "day_gain_percent": 0
            })
            total_value += holding.cost_basis
    
    total_pnl = total_value - total_cost
    total_pnl_percent = (total_pnl / total_cost * 100) if total_cost > 0 else 0
    day_gain_percent = (total_day_gain / total_value * 100) if total_value > 0 else 0
    
    # Get AI advice
    advice = get_portfolio_advice(
        holdings_data,
        total_value,
        total_pnl,
        total_pnl_percent,
        total_day_gain,
        day_gain_percent
    )
    
    if advice is None:
        return {
            "advice": None, 
            "error": "无法获取投资建议。可能的原因：\n1. GEMINI_API_KEY 未配置或无效\n2. Gemini API 配额已用完（免费层每日限额）\n3. API 调用频率过高，请稍后再试\n\n请检查 .env 文件中的 GEMINI_API_KEY 配置，或等待配额重置。"
        }
    
    return {"advice": advice}


@router.post("/add-position")
def add_position(
    request: AddPositionRequest,
    db: Session = Depends(get_db)
):
    ticker = request.ticker
    quantity = request.quantity
    cost_basis_per_share = request.cost_basis_per_share
    """
    Add a new position or add to existing position (no authentication required)
    """
    default_user = get_or_create_default_user(db)
    
    # Check if holding already exists
    existing = db.query(Holding).filter(
        Holding.user_id == default_user.id,
        Holding.ticker == ticker.upper()
    ).first()
    
    if existing:
        # Update existing: calculate new average cost basis
        total_old_cost = existing.cost_basis
        total_new_cost = quantity * cost_basis_per_share
        total_cost = total_old_cost + total_new_cost
        total_quantity = existing.quantity + quantity
        
        existing.quantity = total_quantity
        existing.cost_basis = total_cost
    else:
        # Create new holding
        new_holding = Holding(
            user_id=default_user.id,
            ticker=ticker.upper(),
            quantity=quantity,
            cost_basis=quantity * cost_basis_per_share
        )
        db.add(new_holding)
    
    db.commit()
    return {"status": "success", "message": f"Added {quantity} shares of {ticker.upper()}"}


@router.post("/reduce-position")
def reduce_position(
    request: ReducePositionRequest,
    db: Session = Depends(get_db)
):
    ticker = request.ticker
    quantity = request.quantity
    """
    Reduce a position (no authentication required)
    """
    default_user = get_or_create_default_user(db)
    
    existing = db.query(Holding).filter(
        Holding.user_id == default_user.id,
        Holding.ticker == ticker.upper()
    ).first()
    
    if not existing:
        raise HTTPException(status_code=404, detail=f"No position found for {ticker.upper()}")
    
    if quantity >= existing.quantity:
        # Remove entire position
        db.delete(existing)
    else:
        # Reduce quantity proportionally
        ratio = (existing.quantity - quantity) / existing.quantity
        existing.quantity = existing.quantity - quantity
        existing.cost_basis = existing.cost_basis * ratio
    
    db.commit()
    return {"status": "success", "message": f"Reduced {quantity} shares of {ticker.upper()}"}

