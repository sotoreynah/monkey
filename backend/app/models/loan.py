from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Loan(Base):
    __tablename__ = "loans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    loan_type = Column(String, nullable=False)  # bnpl, auto, mortgage, personal
    creditor = Column(String)
    original_amount = Column(Float)
    current_balance = Column(Float, nullable=False)
    interest_rate = Column(Float)  # as decimal, e.g., 0.0699
    monthly_payment = Column(Float)
    payment_day = Column(Integer)
    start_date = Column(Date)
    end_date = Column(Date)
    payments_remaining = Column(Integer)
    is_active = Column(Boolean, default=True)
    priority_rank = Column(Integer)
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    payments = relationship("LoanPayment", back_populates="loan")


class LoanPayment(Base):
    __tablename__ = "loan_payments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    loan_id = Column(Integer, ForeignKey("loans.id"), nullable=False)
    payment_date = Column(Date, nullable=False)
    amount = Column(Float, nullable=False)
    principal_amount = Column(Float)
    interest_amount = Column(Float)
    balance_after = Column(Float)
    transaction_id = Column(Integer, ForeignKey("transactions.id"))
    is_projected = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

    loan = relationship("Loan", back_populates="payments")
