-- Add month column to budget_targets for month-specific budgets
-- This allows different targets for each month (Feb vs Mar, etc.)

-- Add month column (nullable initially)
ALTER TABLE budget_targets ADD COLUMN month TEXT;

-- Create index for fast lookups
CREATE INDEX IF NOT EXISTS idx_budget_targets_month ON budget_targets(month);

-- Create composite unique constraint: one target per category per month
CREATE UNIQUE INDEX IF NOT EXISTS idx_budget_targets_month_category 
  ON budget_targets(month, category) 
  WHERE month IS NOT NULL;

-- Migrate existing phase-based targets to February 2026 (current month)
UPDATE budget_targets SET month = '2026-02' WHERE month IS NULL AND phase_number = 1;

-- Delete phase 2-4 targets (they'll be created on-demand when user edits future months)
DELETE FROM budget_targets WHERE phase_number IN (2, 3, 4);

-- Make phase_number nullable (now that we have month-specific)
-- SQLite doesn't support ALTER COLUMN, so we'll just leave it for backward compatibility

-- Verify
SELECT month, category, monthly_target, is_fixed 
FROM budget_targets 
ORDER BY month, category
LIMIT 20;
