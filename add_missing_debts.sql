-- Add missing debt accounts from "Stop the Monkey" plan
-- These are critical for debt payoff tracking

-- Credit Cards (need actual balances - using estimates for now)
-- User should update these with real balances
INSERT INTO loans (name, loan_type, creditor, current_balance, interest_rate, monthly_payment, priority_rank, end_date, notes) VALUES
  ('Credit Card 6032', 'credit_card', 'US Bank', 0, 0.2200, 0, 1, NULL, 'Highest priority - has cash advances at 25%+ APR'),
  ('AMEX', 'credit_card', 'American Express', 5742, 0.2241, 0, 2, NULL, 'Balance from analysis, $2,241/yr interest'),
  ('Apple Card', 'credit_card', 'Goldman Sachs', 0, 0.1999, 0, 3, NULL, 'Update with actual balance'),
  ('Wells Fargo CC', 'credit_card', 'Wells Fargo', 0, 0.2000, 0, 4, NULL, 'Update with actual balance'),
  ('Chase CC', 'credit_card', 'JPMorgan Chase', 0, 0.2000, 0, 5, NULL, 'Update with actual balance');

-- Auto Loans (from monthly payment analysis)
INSERT INTO loans (name, loan_type, creditor, current_balance, interest_rate, monthly_payment, priority_rank, end_date, notes) VALUES
  ('VW Credit', 'auto', 'VW Credit', 0, 0.0500, 509, 8, NULL, 'Update with actual balance'),
  ('Santander Auto', 'auto', 'Santander Consumer', 0, 0.0600, 420, 9, NULL, 'Update with actual balance'),
  ('Tesla Finance', 'auto', 'Tesla Motors', 0, 0.0400, 775, 10, NULL, 'Lease or loan - update balance'),
  ('German American Auto', 'auto', 'German American Bank', 0, 0.0600, 2762, 11, NULL, 'Large monthly payment - update balance');

-- Verify all loans
SELECT 
  priority_rank,
  name,
  loan_type,
  creditor,
  current_balance,
  ROUND(interest_rate * 100, 2) || '%' as rate,
  monthly_payment
FROM loans
ORDER BY priority_rank;
