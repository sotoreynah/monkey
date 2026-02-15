"""Pydantic schemas for emergency fund API"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import date


class EmergencyFundResponse(BaseModel):
    """Emergency fund status response"""
    current_balance: float
    baby_step: int  # 1 or 3
    target: float  # Current step target
    progress_percent: float
    months_of_expenses: float
    monthly_contribution_needed: float
    projected_completion_date: Optional[str]
    next_milestone: dict


class TransactionCreate(BaseModel):
    """Create emergency fund transaction"""
    amount: float
    description: Optional[str] = None


class TransactionResponse(BaseModel):
    """Emergency fund transaction response"""
    id: int
    transaction_date: str
    amount: float
    type: str
    description: Optional[str]
    balance_after: float

    class Config:
        from_attributes = True
