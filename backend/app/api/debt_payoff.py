"""Debt Payoff Calculator API endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.loan import Loan
from app.models.plan import FinancialPlan
from app.models.user import User
from app.schemas.debt_payoff import DebtPayoffPlan, RecalculateRequest
from app.services.debt_calculator import DebtPayoffCalculator
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/debt", tags=["debt"])


@router.get("/payoff-plan", response_model=DebtPayoffPlan)
def get_payoff_plan(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Get complete debt payoff plan using debt avalanche method
    Uses the active financial plan's monthly payment capacity
    """
    # Get active plan
    plan = db.query(FinancialPlan).filter(FinancialPlan.is_active == True).first()
    if not plan:
        raise HTTPException(status_code=404, detail="No active financial plan found")
    
    # Get active loans
    loans = db.query(Loan).filter(Loan.is_active == True).all()
    if not loans:
        raise HTTPException(status_code=404, detail="No active loans found")
    
    # Calculate payoff plan
    calculator = DebtPayoffCalculator(db)
    try:
        result = calculator.calculate_payoff_plan(
            loans=loans,
            monthly_capacity=plan.monthly_payment_capacity,
            start_date=plan.start_date
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/recalculate", response_model=DebtPayoffPlan)
def recalculate_payoff(
    request: RecalculateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Recalculate debt payoff with updated monthly payment capacity
    If monthly_capacity provided, updates the plan and recalculates
    """
    # Get active plan
    plan = db.query(FinancialPlan).filter(FinancialPlan.is_active == True).first()
    if not plan:
        raise HTTPException(status_code=404, detail="No active financial plan found")
    
    # Update monthly capacity if provided
    if request.monthly_capacity is not None:
        plan.monthly_payment_capacity = request.monthly_capacity
        db.commit()
        db.refresh(plan)
    
    # Get active loans
    loans = db.query(Loan).filter(Loan.is_active == True).all()
    if not loans:
        raise HTTPException(status_code=404, detail="No active loans found")
    
    # Calculate payoff plan
    calculator = DebtPayoffCalculator(db)
    try:
        result = calculator.calculate_payoff_plan(
            loans=loans,
            monthly_capacity=plan.monthly_payment_capacity,
            start_date=plan.start_date
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/summary")
def debt_summary(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Get quick debt summary"""
    loans = db.query(Loan).filter(Loan.is_active == True).all()
    plan = db.query(FinancialPlan).filter(FinancialPlan.is_active == True).first()
    
    total_debt = sum(loan.current_balance for loan in loans)
    total_minimums = sum(loan.monthly_payment or 0 for loan in loans)
    monthly_capacity = plan.monthly_payment_capacity if plan else 0
    
    return {
        "total_debt": round(total_debt, 2),
        "total_minimums": round(total_minimums, 2),
        "monthly_capacity": round(monthly_capacity, 2),
        "extra_payment": round(monthly_capacity - total_minimums, 2),
        "active_loans": len(loans)
    }
