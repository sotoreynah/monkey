from __future__ import annotations
from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from dateutil.relativedelta import relativedelta
from app.database import get_db
from app.models.transaction import Transaction
from app.models.plan import BudgetTarget
from app.models.user import User
from app.utils.date_utils import get_current_plan_week, get_phase_for_week
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/budget", tags=["budget"])


@router.get("")
def get_budget_vs_actual(
    month: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    if month:
        try:
            target_date = date.fromisoformat(month + "-01")
        except ValueError:
            target_date = date.today().replace(day=1)
    else:
        target_date = date.today().replace(day=1)

    month_end = (target_date + relativedelta(months=1)) - relativedelta(days=1)

    # Determine phase for this month
    plan_start = date(2026, 2, 1)
    months_from_start = (target_date.year - plan_start.year) * 12 + (target_date.month - plan_start.month)
    week_approx = max(months_from_start * 4 + 1, 1)
    phase_num = get_phase_for_week(min(week_approx, 252))

    # Get budget targets for this phase
    targets = db.query(BudgetTarget).filter(BudgetTarget.phase_number == phase_num).all()
    target_map = {t.category: t.monthly_target for t in targets}

    # Get actual spending by category
    actuals = (
        db.query(Transaction.category, func.sum(Transaction.amount))
        .filter(
            Transaction.transaction_date >= target_date,
            Transaction.transaction_date <= month_end,
            Transaction.is_debit == True,
            Transaction.is_excluded == False,
        )
        .group_by(Transaction.category)
        .all()
    )
    actual_map = {cat or "Uncategorized": round(float(amt), 2) for cat, amt in actuals}

    # Merge targets and actuals
    all_categories = sorted(set(list(target_map.keys()) + list(actual_map.keys())))
    rows = []
    total_target = 0
    total_actual = 0
    for cat in all_categories:
        target = target_map.get(cat, 0)
        actual = actual_map.get(cat, 0)
        total_target += target
        total_actual += actual
        rows.append({
            "category": cat,
            "target": target,
            "actual": actual,
            "variance": round(target - actual, 2),
            "over_budget": actual > target if target > 0 else False,
        })

    return {
        "month": target_date.isoformat()[:7],
        "phase": phase_num,
        "categories": rows,
        "total_target": round(total_target, 2),
        "total_actual": round(total_actual, 2),
        "total_variance": round(total_target - total_actual, 2),
    }
