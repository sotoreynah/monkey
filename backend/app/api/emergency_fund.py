"""Emergency Fund Tracker API endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

from app.database import get_db
from app.models.emergency_fund import EmergencyFund, EmergencyFundTransaction
from app.models.user import User
from app.schemas.emergency_fund import EmergencyFundResponse, TransactionCreate, TransactionResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/emergency-fund", tags=["emergency-fund"])


@router.get("", response_model=EmergencyFundResponse)
def get_emergency_fund(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Get current emergency fund status"""
    fund = db.query(EmergencyFund).first()
    if not fund:
        raise HTTPException(status_code=404, detail="Emergency fund not initialized")
    
    # Determine current baby step
    if fund.current_balance < fund.target_step_1:
        baby_step = 1
        target = fund.target_step_1
    else:
        baby_step = 3
        target = fund.target_step_3
    
    # Calculate progress
    progress_percent = (fund.current_balance / target * 100) if target > 0 else 0
    
    # Calculate months of expenses (assuming $13,000/month from plan)
    monthly_expenses = 13000
    months_of_expenses = fund.current_balance / monthly_expenses if monthly_expenses > 0 else 0
    
    # Calculate monthly contribution needed to reach Step 3 by Phase 3 end
    # Phase 3 ends at month 58 (from the plan)
    months_remaining = 58 - 1  # Rough estimate
    if baby_step == 3:
        amount_needed = fund.target_step_3 - fund.current_balance
        monthly_contribution_needed = amount_needed / months_remaining if months_remaining > 0 else 0
    else:
        monthly_contribution_needed = fund.target_step_1 / 6  # Aim for Step 1 in 6 months
    
    # Projected completion date
    if fund.monthly_contribution > 0:
        amount_remaining = target - fund.current_balance
        months_to_complete = int(amount_remaining / fund.monthly_contribution) if fund.monthly_contribution > 0 else 999
        projected_date = (date.today() + relativedelta(months=months_to_complete)).isoformat()
    else:
        projected_date = None
    
    # Next milestone
    if baby_step == 1:
        next_milestone = {
            "name": "Baby Step 1: Starter Emergency Fund",
            "amount": fund.target_step_1,
            "percent": round(progress_percent, 1)
        }
    else:
        next_milestone = {
            "name": "Baby Step 3: Full Emergency Fund (12 months)",
            "amount": fund.target_step_3,
            "percent": round(progress_percent, 1)
        }
    
    return {
        "current_balance": round(fund.current_balance, 2),
        "baby_step": baby_step,
        "target": target,
        "progress_percent": round(progress_percent, 1),
        "months_of_expenses": round(months_of_expenses, 1),
        "monthly_contribution_needed": round(monthly_contribution_needed, 2),
        "projected_completion_date": projected_date,
        "next_milestone": next_milestone
    }


@router.post("/deposit", response_model=TransactionResponse)
def add_deposit(
    transaction: TransactionCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Add a deposit to emergency fund"""
    fund = db.query(EmergencyFund).first()
    if not fund:
        raise HTTPException(status_code=404, detail="Emergency fund not initialized")
    
    # Update balance
    fund.current_balance += transaction.amount
    
    # Create transaction record
    new_transaction = EmergencyFundTransaction(
        transaction_date=date.today(),
        amount=transaction.amount,
        type="deposit",
        description=transaction.description,
        balance_after=fund.current_balance
    )
    
    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)
    
    return {
        "id": new_transaction.id,
        "transaction_date": new_transaction.transaction_date.isoformat(),
        "amount": new_transaction.amount,
        "type": new_transaction.type,
        "description": new_transaction.description,
        "balance_after": new_transaction.balance_after
    }


@router.post("/withdraw", response_model=TransactionResponse)
def add_withdrawal(
    transaction: TransactionCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Record a withdrawal from emergency fund"""
    fund = db.query(EmergencyFund).first()
    if not fund:
        raise HTTPException(status_code=404, detail="Emergency fund not initialized")
    
    # Check if sufficient balance
    if fund.current_balance < transaction.amount:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient balance. Current: ${fund.current_balance:.2f}"
        )
    
    # Update balance
    fund.current_balance -= transaction.amount
    
    # Create transaction record
    new_transaction = EmergencyFundTransaction(
        transaction_date=date.today(),
        amount=transaction.amount,
        type="withdrawal",
        description=transaction.description,
        balance_after=fund.current_balance
    )
    
    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)
    
    return {
        "id": new_transaction.id,
        "transaction_date": new_transaction.transaction_date.isoformat(),
        "amount": new_transaction.amount,
        "type": new_transaction.type,
        "description": new_transaction.description,
        "balance_after": new_transaction.balance_after
    }


@router.get("/history", response_model=list[TransactionResponse])
def get_transaction_history(
    limit: int = 50,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Get emergency fund transaction history"""
    transactions = (
        db.query(EmergencyFundTransaction)
        .order_by(EmergencyFundTransaction.transaction_date.desc())
        .limit(limit)
        .all()
    )
    
    return [
        {
            "id": t.id,
            "transaction_date": t.transaction_date.isoformat(),
            "amount": t.amount,
            "type": t.type,
            "description": t.description,
            "balance_after": t.balance_after
        }
        for t in transactions
    ]
