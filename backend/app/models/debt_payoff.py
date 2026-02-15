from sqlalchemy import Column, Integer, Float, Date, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class DebtPayoffProjection(Base):
    """Stores projected debt payoff timeline using debt avalanche method"""
    __tablename__ = "debt_payoff_projections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_id = Column(Integer, ForeignKey("financial_plan.id"), nullable=False)
    loan_id = Column(Integer, ForeignKey("loans.id"), nullable=False)
    payoff_month = Column(Integer, nullable=False)  # Month number in sequence
    payoff_date = Column(Date, nullable=False)
    total_paid = Column(Float, nullable=False)
    interest_paid = Column(Float, nullable=False)
    principal_paid = Column(Float, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
