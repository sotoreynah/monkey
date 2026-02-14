from __future__ import annotations
from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from dateutil.relativedelta import relativedelta
from app.database import get_db
from app.models.transaction import Transaction
from app.models.loan import Loan
from app.models.plan import PlanPhase, BudgetTarget, FinancialPlan
from app.models.user import User
from app.schemas.plan import DashboardResponse
from app.utils.date_utils import get_current_plan_week, get_phase_for_week
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardResponse)
def get_dashboard(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    current_week = get_current_plan_week()
    phase_num = get_phase_for_week(max(current_week, 1))

    plan = db.query(FinancialPlan).filter(FinancialPlan.is_active == True).first()
    phase = None
    if plan:
        phase = db.query(PlanPhase).filter(
            PlanPhase.plan_id == plan.id, PlanPhase.phase_number == phase_num
        ).first()

    # Debt totals
    active_loans = db.query(Loan).filter(Loan.is_active == True).all()
    total_debt = sum(l.current_balance for l in active_loans)
    non_mortgage = sum(l.current_balance for l in active_loans if l.loan_type != "mortgage")

    # This month spending
    today = date.today()
    month_start = today.replace(day=1)
    month_spent = db.query(func.sum(Transaction.amount)).filter(
        Transaction.transaction_date >= month_start,
        Transaction.is_debit == True,
        Transaction.is_excluded == False,
    ).scalar() or 0

    # Budget target for current phase
    budget_targets = db.query(BudgetTarget).filter(BudgetTarget.phase_number == phase_num).all()
    month_target = sum(bt.monthly_target for bt in budget_targets) if budget_targets else 13000

    # Spending trend (last 6 months)
    trend = []
    for i in range(5, -1, -1):
        m_start = (today - relativedelta(months=i)).replace(day=1)
        m_end = (m_start + relativedelta(months=1)) - relativedelta(days=1)
        spent = db.query(func.sum(Transaction.amount)).filter(
            Transaction.transaction_date >= m_start,
            Transaction.transaction_date <= m_end,
            Transaction.is_debit == True,
            Transaction.is_excluded == False,
        ).scalar() or 0
        trend.append({
            "month": m_start.strftime("%b %Y"),
            "spent": round(float(spent), 2),
            "target": month_target,
        })

    return DashboardResponse(
        current_week=current_week,
        current_phase=phase_num,
        current_phase_name=phase.name if phase else f"Phase {phase_num}",
        progress_pct=round((current_week / 252) * 100, 1),
        total_debt=round(total_debt, 2),
        non_mortgage_debt=round(non_mortgage, 2),
        month_spent=round(float(month_spent), 2),
        month_budget_target=month_target,
        month_variance=round(month_target - float(month_spent), 2),
        emergency_fund=0,  # Updated manually or via milestone
        debt_paid_this_month=0,  # Calculated from loan payments
        spending_trend=trend,
    )
