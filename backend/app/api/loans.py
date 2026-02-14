from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date
from dateutil.relativedelta import relativedelta
from app.database import get_db
from app.models.loan import Loan
from app.models.user import User
from app.schemas.loan import LoanResponse, LoanUpdate, LoanPayoffProjection
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/loans", tags=["loans"])


@router.get("", response_model=list[LoanResponse])
def list_loans(
    active_only: bool = True,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = db.query(Loan)
    if active_only:
        query = query.filter(Loan.is_active == True)
    return query.order_by(Loan.priority_rank.asc().nullslast()).all()


@router.get("/summary")
def loan_summary(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    loans = db.query(Loan).filter(Loan.is_active == True).all()
    total = sum(l.current_balance for l in loans)
    mortgage = sum(l.current_balance for l in loans if l.loan_type == "mortgage")
    non_mortgage = total - mortgage
    monthly_payments = sum(l.monthly_payment or 0 for l in loans)
    return {
        "total_debt": round(total, 2),
        "mortgage_debt": round(mortgage, 2),
        "non_mortgage_debt": round(non_mortgage, 2),
        "monthly_payments": round(monthly_payments, 2),
        "active_loans": len(loans),
    }


@router.get("/projections", response_model=list[LoanPayoffProjection])
def payoff_projections(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    loans = db.query(Loan).filter(Loan.is_active == True).all()
    projections = []
    for loan in loans:
        balance = loan.current_balance
        payment = loan.monthly_payment or 0
        rate = loan.interest_rate or 0
        monthly_rate = rate / 12

        if payment <= 0:
            projections.append(LoanPayoffProjection(
                loan_id=loan.id, loan_name=loan.name, current_balance=balance,
                monthly_payment=payment, interest_rate=rate,
                projected_payoff_date=None, total_interest_remaining=0, months_remaining=0,
            ))
            continue

        months = 0
        total_interest = 0.0
        remaining = balance
        while remaining > 0 and months < 600:
            interest = remaining * monthly_rate
            total_interest += interest
            principal = payment - interest
            if principal <= 0:
                break
            remaining -= principal
            months += 1

        payoff_date = date.today() + relativedelta(months=months) if months < 600 else None
        projections.append(LoanPayoffProjection(
            loan_id=loan.id, loan_name=loan.name, current_balance=balance,
            monthly_payment=payment, interest_rate=rate,
            projected_payoff_date=payoff_date,
            total_interest_remaining=round(total_interest, 2),
            months_remaining=months,
        ))
    return projections


@router.patch("/{loan_id}", response_model=LoanResponse)
def update_loan(
    loan_id: int,
    update: LoanUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    loan = db.query(Loan).filter(Loan.id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")

    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(loan, field, value)

    db.commit()
    db.refresh(loan)
    return loan
