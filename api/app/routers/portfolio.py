from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Holding
from app.schemas import PortfolioSummary
from app.auth import get_current_user
from app.models import User
from app.services.stock_service import get_stock_price

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

