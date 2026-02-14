from __future__ import annotations
from pydantic import BaseModel
from datetime import date


class WeekData(BaseModel):
    week_number: int
    week_start_date: date
    week_end_date: date
    phase_number: int
    total_spent: float
    discretionary_spent: float
    debt_paid_down: float
    emergency_fund_balance: float
    is_on_track: bool | None
    status: str


class PhaseData(BaseModel):
    phase_number: int
    name: str
    start_week: int
    end_week: int
    color_code: str
    primary_goal: str
    weeks_completed: int
    weeks_total: int
    progress_pct: float


class CalendarResponse(BaseModel):
    current_week: int
    total_weeks: int
    progress_pct: float
    phases: list[PhaseData]
    weeks: list[WeekData]


class DashboardResponse(BaseModel):
    current_week: int
    current_phase: int
    current_phase_name: str
    progress_pct: float
    total_debt: float
    non_mortgage_debt: float
    month_spent: float
    month_budget_target: float
    month_variance: float
    emergency_fund: float
    debt_paid_this_month: float
    spending_trend: list[dict]
