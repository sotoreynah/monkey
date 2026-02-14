from __future__ import annotations
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.plan import FinancialPlan, PlanPhase, WeeklySnapshot
from app.models.user import User
from app.schemas.plan import CalendarResponse, WeekData, PhaseData
from app.utils.date_utils import get_current_plan_week
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/plan", tags=["plan"])


@router.get("/calendar", response_model=CalendarResponse)
def get_calendar(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    plan = db.query(FinancialPlan).filter(FinancialPlan.is_active == True).first()
    if not plan:
        return CalendarResponse(
            current_week=0, total_weeks=252, progress_pct=0,
            phases=[], weeks=[],
        )

    current_week = get_current_plan_week()

    phases = db.query(PlanPhase).filter(PlanPhase.plan_id == plan.id).order_by(PlanPhase.phase_number).all()
    weeks = db.query(WeeklySnapshot).filter(WeeklySnapshot.plan_id == plan.id).order_by(WeeklySnapshot.week_number).all()

    phase_data = []
    for p in phases:
        total = p.end_week - p.start_week + 1
        completed = sum(1 for w in weeks if p.start_week <= w.week_number <= p.end_week and w.status == "completed")
        phase_data.append(PhaseData(
            phase_number=p.phase_number,
            name=p.name,
            start_week=p.start_week,
            end_week=p.end_week,
            color_code=p.color_code or "#888",
            primary_goal=p.primary_goal or "",
            weeks_completed=completed,
            weeks_total=total,
            progress_pct=round((completed / total) * 100, 1) if total else 0,
        ))

    week_data = [
        WeekData(
            week_number=w.week_number,
            week_start_date=w.week_start_date,
            week_end_date=w.week_end_date,
            phase_number=w.phase_number,
            total_spent=w.total_spent or 0,
            discretionary_spent=w.discretionary_spent or 0,
            debt_paid_down=w.debt_paid_down or 0,
            emergency_fund_balance=w.emergency_fund_balance or 0,
            is_on_track=w.is_on_track,
            status=w.status or "future",
        )
        for w in weeks
    ]

    return CalendarResponse(
        current_week=current_week,
        total_weeks=252,
        progress_pct=round((current_week / 252) * 100, 1),
        phases=phase_data,
        weeks=week_data,
    )


@router.get("/phases")
def get_phases(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    plan = db.query(FinancialPlan).filter(FinancialPlan.is_active == True).first()
    if not plan:
        return []
    return db.query(PlanPhase).filter(PlanPhase.plan_id == plan.id).order_by(PlanPhase.phase_number).all()
