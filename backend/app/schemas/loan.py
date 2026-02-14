from __future__ import annotations
from pydantic import BaseModel
from datetime import date
from typing import Optional


class LoanResponse(BaseModel):
    id: int
    name: str
    loan_type: str
    creditor: str | None
    original_amount: float | None
    current_balance: float
    interest_rate: float | None
    monthly_payment: float | None
    end_date: date | None
    payments_remaining: int | None
    is_active: bool
    priority_rank: int | None

    class Config:
        from_attributes = True


class LoanCreate(BaseModel):
    name: str
    loan_type: str
    creditor: str | None = None
    original_amount: float | None = None
    current_balance: float
    interest_rate: float | None = None
    monthly_payment: float | None = None
    end_date: date | None = None
    payments_remaining: int | None = None
    priority_rank: int | None = None
    notes: str | None = None


class LoanUpdate(BaseModel):
    name: str | None = None
    loan_type: str | None = None
    creditor: str | None = None
    original_amount: float | None = None
    current_balance: float | None = None
    interest_rate: float | None = None
    monthly_payment: float | None = None
    end_date: date | None = None
    payments_remaining: int | None = None
    is_active: bool | None = None
    priority_rank: int | None = None
    notes: str | None = None


class LoanPayoffProjection(BaseModel):
    loan_id: int
    loan_name: str
    current_balance: float
    monthly_payment: float
    interest_rate: float
    projected_payoff_date: date | None
    total_interest_remaining: float
    months_remaining: int
