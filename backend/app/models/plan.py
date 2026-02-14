from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class FinancialPlan(Base):
    __tablename__ = "financial_plan"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_name = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    total_weeks = Column(Integer, nullable=False)
    total_months = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())


class PlanPhase(Base):
    __tablename__ = "plan_phases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_id = Column(Integer, ForeignKey("financial_plan.id"), nullable=False)
    phase_number = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    start_month = Column(Integer, nullable=False)
    end_month = Column(Integer, nullable=False)
    start_week = Column(Integer, nullable=False)
    end_week = Column(Integer, nullable=False)
    color_code = Column(String)
    primary_goal = Column(String)
    description = Column(Text)


class WeeklySnapshot(Base):
    __tablename__ = "weekly_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_id = Column(Integer, ForeignKey("financial_plan.id"), nullable=False)
    week_number = Column(Integer, nullable=False, index=True)
    week_start_date = Column(Date, nullable=False)
    week_end_date = Column(Date, nullable=False)
    phase_number = Column(Integer, nullable=False)
    total_spent = Column(Float)
    discretionary_spent = Column(Float)
    debt_paid_down = Column(Float)
    emergency_fund_balance = Column(Float)
    weekly_spending_target = Column(Float)
    is_on_track = Column(Boolean)
    status = Column(String, default="future")  # future, current, completed, missed
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())


class MonthlySnapshot(Base):
    __tablename__ = "monthly_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_id = Column(Integer, ForeignKey("financial_plan.id"), nullable=False)
    month_number = Column(Integer, nullable=False)
    month_date = Column(Date, nullable=False)
    phase_number = Column(Integer, nullable=False)
    monthly_income = Column(Float)
    total_spent = Column(Float)
    fixed_expenses = Column(Float)
    discretionary_spent = Column(Float)
    total_debt_start = Column(Float)
    total_debt_end = Column(Float)
    debt_paid_this_month = Column(Float)
    interest_paid = Column(Float)
    emergency_fund = Column(Float)
    budget_target = Column(Float)
    budget_variance = Column(Float)
    created_at = Column(DateTime, server_default=func.now())


class BudgetTarget(Base):
    __tablename__ = "budget_targets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    phase_number = Column(Integer, nullable=False)
    category = Column(String, nullable=False)
    monthly_target = Column(Float, nullable=False)
    is_fixed = Column(Boolean, default=False)
    notes = Column(Text)


class Milestone(Base):
    __tablename__ = "milestones"

    id = Column(Integer, primary_key=True, autoincrement=True)
    phase_number = Column(Integer)
    name = Column(String, nullable=False)
    description = Column(Text)
    target_date = Column(Date)
    target_amount = Column(Float)
    actual_date = Column(Date)
    actual_amount = Column(Float)
    is_achieved = Column(Boolean, default=False)
