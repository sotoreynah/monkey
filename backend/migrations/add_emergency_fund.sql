-- Migration: Add Emergency Fund Tracker (Baby Steps 1 & 3)
-- Date: 2026-02-14
-- Description: Create emergency_fund and emergency_fund_transactions tables

-- Create emergency_fund table
CREATE TABLE IF NOT EXISTS emergency_fund (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    current_balance FLOAT NOT NULL DEFAULT 0,
    target_step_1 FLOAT NOT NULL DEFAULT 1000,
    target_step_3 FLOAT NOT NULL DEFAULT 156000,
    monthly_contribution FLOAT DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create emergency_fund_transactions table
CREATE TABLE IF NOT EXISTS emergency_fund_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_date DATE NOT NULL,
    amount FLOAT NOT NULL,
    type TEXT NOT NULL,  -- 'deposit' or 'withdrawal'
    description TEXT,
    balance_after FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Initialize with zero balance
INSERT INTO emergency_fund (current_balance, target_step_1, target_step_3, monthly_contribution)
VALUES (0, 1000, 156000, 0);
