from sqlalchemy import Column, Integer, Float, Date, DateTime, Text
from sqlalchemy.sql import func
from app.database import Base


class EmergencyFund(Base):
    """Emergency fund status (Baby Steps 1 & 3)"""
    __tablename__ = "emergency_fund"

    id = Column(Integer, primary_key=True, autoincrement=True)
    current_balance = Column(Float, nullable=False, default=0)
    target_step_1 = Column(Float, nullable=False, default=1000)
    target_step_3 = Column(Float, nullable=False, default=156000)
    monthly_contribution = Column(Float, default=0)
    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now())


class EmergencyFundTransaction(Base):
    """Emergency fund transaction history"""
    __tablename__ = "emergency_fund_transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_date = Column(Date, nullable=False)
    amount = Column(Float, nullable=False)
    type = Column(Text, nullable=False)  # 'deposit' or 'withdrawal'
    description = Column(Text)
    balance_after = Column(Float, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
