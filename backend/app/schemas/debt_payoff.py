"""Pydantic schemas for debt payoff calculator API"""
from pydantic import BaseModel
from typing import List, Optional
from datetime import date


class PayoffSummary(BaseModel):
    """Summary of debt payoff plan"""
    total_debt: float
    monthly_capacity: float
    total_minimum_payments: float
    months_to_debt_free: Optional[int]
    debt_free_date: Optional[str]
    total_interest_paid: float
    interest_saved: float
    total_paid: float
    is_underwater: bool
    debt_paid_off: bool
    remaining_debt: float
    warning: Optional[str]


class LoanPayoffOrder(BaseModel):
    """Individual loan in payoff order"""
    rank: int
    loan_id: int
    name: str
    payoff_month: int
    payoff_date: str
    interest_paid: float


class PayoffTimeline(BaseModel):
    """Monthly snapshot of debt payoff progress"""
    month: int
    month_date: str
    total_debt_remaining: float
    total_paid: float
    interest_portion: float
    principal_portion: float
    active_loan: str


class DebtPayoffPlan(BaseModel):
    """Complete debt payoff calculation result"""
    summary: PayoffSummary
    payoff_order: List[LoanPayoffOrder]
    timeline: List[PayoffTimeline]


class RecalculateRequest(BaseModel):
    """Request body for recalculating debt payoff"""
    monthly_capacity: Optional[float] = None
