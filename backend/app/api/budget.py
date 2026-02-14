from __future__ import annotations
from datetime import date
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
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


class BudgetTargetUpdate(BaseModel):
    category: str
    monthly_target: float
    is_fixed: bool = False


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

    # Get budget targets for this month (month-specific takes priority)
    month_str = target_date.isoformat()[:7]  # YYYY-MM format
    targets = db.query(BudgetTarget).filter(BudgetTarget.month == month_str).all()
    
    # If no targets for this month, copy from previous month or use phase defaults
    if not targets:
        # Try to find previous month's targets
        prev_month = (target_date - relativedelta(months=1)).isoformat()[:7]
        targets = db.query(BudgetTarget).filter(BudgetTarget.month == prev_month).all()
        
        # If still no targets, use phase defaults (fallback)
        if not targets:
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
            Transaction.category != 'Payment',  # Exclude credit card payments from spending
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


@router.get("/targets/{month}")
def get_budget_targets(
    month: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Get budget targets for a specific month (YYYY-MM format)"""
    targets = db.query(BudgetTarget).filter(BudgetTarget.month == month).all()
    
    # If no targets for this month, check if we should copy from previous month
    if not targets:
        try:
            target_date = date.fromisoformat(month + "-01")
            prev_month = (target_date - relativedelta(months=1)).isoformat()[:7]
            prev_targets = db.query(BudgetTarget).filter(BudgetTarget.month == prev_month).all()
            
            if prev_targets:
                return {
                    "month": month,
                    "targets": [],
                    "can_copy_from": prev_month,
                    "has_targets": False,
                }
        except ValueError:
            pass
    
    return {
        "month": month,
        "targets": [
            {
                "id": t.id,
                "category": t.category,
                "monthly_target": t.monthly_target,
                "is_fixed": t.is_fixed,
                "notes": t.notes,
            }
            for t in targets
        ],
        "has_targets": len(targets) > 0,
    }


@router.post("/targets/{month}")
def update_budget_targets(
    month: str,
    targets: list[BudgetTargetUpdate],
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Create or update budget targets for a specific month"""
    try:
        # Validate month format
        date.fromisoformat(month + "-01")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid month format (use YYYY-MM)")
    
    # Delete existing targets for this month
    db.query(BudgetTarget).filter(BudgetTarget.month == month).delete()
    
    # Create new targets
    for target_data in targets:
        db_target = BudgetTarget(
            month=month,
            category=target_data.category,
            monthly_target=target_data.monthly_target,
            is_fixed=target_data.is_fixed,
            phase_number=None,  # Month-specific targets don't need phase
        )
        db.add(db_target)
    
    db.commit()
    
    return {"success": True, "month": month, "count": len(targets)}


@router.post("/targets/{month}/copy-from/{source_month}")
def copy_budget_targets(
    month: str,
    source_month: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Copy budget targets from another month"""
    try:
        date.fromisoformat(month + "-01")
        date.fromisoformat(source_month + "-01")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid month format (use YYYY-MM)")
    
    # Get source targets
    source_targets = db.query(BudgetTarget).filter(BudgetTarget.month == source_month).all()
    
    if not source_targets:
        raise HTTPException(status_code=404, detail=f"No budget targets found for {source_month}")
    
    # Delete existing targets for destination month
    db.query(BudgetTarget).filter(BudgetTarget.month == month).delete()
    
    # Copy targets
    for source in source_targets:
        db_target = BudgetTarget(
            month=month,
            category=source.category,
            monthly_target=source.monthly_target,
            is_fixed=source.is_fixed,
            notes=source.notes,
            phase_number=None,
        )
        db.add(db_target)
    
    db.commit()
    
    return {"success": True, "month": month, "copied_from": source_month, "count": len(source_targets)}


@router.delete("/targets/{month}/{category}")
def delete_budget_target(
    month: str,
    category: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Delete a specific budget target"""
    target = db.query(BudgetTarget).filter(
        BudgetTarget.month == month,
        BudgetTarget.category == category
    ).first()
    
    if not target:
        raise HTTPException(status_code=404, detail="Budget target not found")
    
    db.delete(target)
    db.commit()
    
    return {"success": True}
