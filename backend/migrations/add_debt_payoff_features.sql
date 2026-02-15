-- Migration: Add Debt Payoff Calculator features
-- Date: 2026-02-14
-- Description: Add monthly_payment_capacity to financial_plan and create debt_payoff_projections table

-- Add monthly_payment_capacity to financial_plan
ALTER TABLE financial_plan ADD COLUMN monthly_payment_capacity FLOAT DEFAULT 5413.0;

-- Create debt_payoff_projections table
CREATE TABLE IF NOT EXISTS debt_payoff_projections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id INTEGER NOT NULL,
    loan_id INTEGER NOT NULL,
    payoff_month INTEGER NOT NULL,
    payoff_date DATE NOT NULL,
    total_paid FLOAT NOT NULL,
    interest_paid FLOAT NOT NULL,
    principal_paid FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (plan_id) REFERENCES financial_plan(id),
    FOREIGN KEY (loan_id) REFERENCES loans(id)
);
