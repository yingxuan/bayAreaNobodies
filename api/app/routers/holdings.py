from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Holding
from app.schemas import HoldingCreate, HoldingResponse
from app.auth import get_current_user
from app.models import User

router = APIRouter()


@router.get("", response_model=list[HoldingResponse])
def get_holdings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    holdings = db.query(Holding).filter(Holding.user_id == current_user.id).all()
    return holdings


@router.post("", response_model=HoldingResponse, status_code=status.HTTP_201_CREATED)
def create_holding(
    holding: HoldingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_holding = Holding(
        user_id=current_user.id,
        ticker=holding.ticker.upper(),
        quantity=holding.quantity,
        cost_basis=holding.cost_basis,
        tags=holding.tags
    )
    db.add(db_holding)
    db.commit()
    db.refresh(db_holding)
    return db_holding


@router.put("/{holding_id}", response_model=HoldingResponse)
def update_holding(
    holding_id: int,
    holding: HoldingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_holding = db.query(Holding).filter(
        Holding.id == holding_id,
        Holding.user_id == current_user.id
    ).first()
    if not db_holding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Holding not found"
        )
    db_holding.ticker = holding.ticker.upper()
    db_holding.quantity = holding.quantity
    db_holding.cost_basis = holding.cost_basis
    db_holding.tags = holding.tags
    db.commit()
    db.refresh(db_holding)
    return db_holding


@router.delete("/{holding_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_holding(
    holding_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_holding = db.query(Holding).filter(
        Holding.id == holding_id,
        Holding.user_id == current_user.id
    ).first()
    if not db_holding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Holding not found"
        )
    db.delete(db_holding)
    db.commit()
    return None

