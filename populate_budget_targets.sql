-- Populate budget_targets table with "Stop the Monkey" plan values
-- Phase 1: Stop the Bleeding (Months 1-6)
-- Phase 2: Debt Avalanche (Months 7-24)
-- Phase 3: Build Fortress (Months 25-42)
-- Phase 4: Build Runway (Months 43-58)

-- Clear existing targets
DELETE FROM budget_targets;

-- ============================================================================
-- PHASE 1: STOP THE BLEEDING (Months 1-6, Feb-Jul 2026)
-- Goal: Reduce spending by 50%, create $5,413/mo surplus
-- ============================================================================

-- Fixed expenses (cannot cut)
-- NOTE: Loan payments are tracked separately in loans table, not as budget categories
INSERT INTO budget_targets (phase_number, category, monthly_target, is_fixed, notes) VALUES
  (1, 'Utilities', 200, 1, 'Internet, phone, basic utilities');

-- Discretionary (Phase 1 aggressive cuts)
INSERT INTO budget_targets (phase_number, category, monthly_target, is_fixed, notes) VALUES
  (1, 'Groceries', 700, 0, 'Switch from Whole Foods to Kroger/Costco'),
  (1, 'Dining', 150, 0, 'Max 2 restaurant meals per month'),
  (1, 'Shopping', 100, 0, '30-day rule: wait before any purchase'),
  (1, 'Transportation', 100, 0, 'Eliminate leisure travel, Tesla charging only'),
  (1, 'Entertainment', 100, 0, 'No concerts, no events over $50'),
  (1, 'Health', 150, 0, 'Pick ONE fitness membership, cancel others'),
  (1, 'Services', 60, 0, 'Keep max 3 subscriptions (cancel rest)'),
  (1, 'Cash', 100, 0, 'Envelope system for cash spending'),
  (1, 'Other', 200, 0, 'Strict miscellaneous budget');

-- ============================================================================
-- PHASE 2: DEBT AVALANCHE (Months 7-24, Aug 2026 - Jan 2028)
-- Goal: Pay off all non-mortgage debt
-- ============================================================================

-- Fixed expenses (some BNPL loans ending, payment drops)
INSERT INTO budget_targets (phase_number, category, monthly_target, is_fixed, notes) VALUES
  (2, 'Utilities', 200, 1, 'Internet, phone, basic utilities');

-- Discretionary (maintain Phase 1 discipline)
INSERT INTO budget_targets (phase_number, category, monthly_target, is_fixed, notes) VALUES
  (2, 'Groceries', 750, 0, 'Kroger/Costco + occasional Whole Foods'),
  (2, 'Dining', 200, 0, 'Up to 3 restaurant meals per month'),
  (2, 'Shopping', 150, 0, 'Slightly relaxed, still mindful'),
  (2, 'Transportation', 150, 0, 'Minimal travel, charging'),
  (2, 'Entertainment', 150, 0, 'Small events OK, no major concerts'),
  (2, 'Health', 150, 0, 'One gym membership'),
  (2, 'Services', 100, 0, 'Up to 5 subscriptions'),
  (2, 'Cash', 100, 0, 'Envelope system'),
  (2, 'Other', 250, 0, 'Miscellaneous');

-- ============================================================================
-- PHASE 3: BUILD FORTRESS (Months 25-42, Feb 2028 - Jul 2029)
-- Goal: 12-month emergency fund ($156k) + 15% to retirement
-- ============================================================================

-- Fixed expenses (all BNPL and most debt paid off)
INSERT INTO budget_targets (phase_number, category, monthly_target, is_fixed, notes) VALUES
  (3, 'Utilities', 250, 1, 'Internet, phone, utilities');

-- Discretionary (moderate relaxation after debt payoff)
INSERT INTO budget_targets (phase_number, category, monthly_target, is_fixed, notes) VALUES
  (3, 'Groceries', 900, 0, 'Mix of Kroger and Whole Foods'),
  (3, 'Dining', 400, 0, 'More frequent dining out'),
  (3, 'Shopping', 300, 0, 'Reasonable purchases, still mindful'),
  (3, 'Transportation', 400, 0, 'Some leisure travel allowed'),
  (3, 'Entertainment', 300, 0, 'Concerts and events OK'),
  (3, 'Health', 200, 0, 'Gym + wellness'),
  (3, 'Services', 150, 0, 'More subscriptions allowed'),
  (3, 'Cash', 150, 0, 'Envelope system'),
  (3, 'Other', 400, 0, 'Miscellaneous');

-- ============================================================================
-- PHASE 4: BUILD RUNWAY (Months 43-58, Aug 2029 - Dec 2030)
-- Goal: Accelerate mortgage, prepare for potential job loss
-- ============================================================================

-- Fixed expenses (debt-free except mortgage)
INSERT INTO budget_targets (phase_number, category, monthly_target, is_fixed, notes) VALUES
  (4, 'Utilities', 250, 1, 'Internet, phone, utilities');

-- Discretionary (sustainable long-term spending)
INSERT INTO budget_targets (phase_number, category, monthly_target, is_fixed, notes) VALUES
  (4, 'Groceries', 1000, 0, 'Normal grocery budget'),
  (4, 'Dining', 500, 0, 'Regular dining out'),
  (4, 'Shopping', 400, 0, 'Normal shopping'),
  (4, 'Transportation', 600, 0, 'Travel as desired'),
  (4, 'Entertainment', 400, 0, 'Full entertainment budget'),
  (4, 'Health', 250, 0, 'Gym + wellness'),
  (4, 'Services', 200, 0, 'All desired subscriptions'),
  (4, 'Cash', 150, 0, 'Envelope system'),
  (4, 'Other', 500, 0, 'Miscellaneous');

-- Verify
SELECT 
  phase_number,
  COUNT(*) as categories,
  ROUND(SUM(monthly_target), 2) as total_budget
FROM budget_targets
GROUP BY phase_number
ORDER BY phase_number;
