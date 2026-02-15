-- Migration: Make phase_number nullable in budget_targets
-- Date: 2026-02-15
-- Description: Allow month-specific budget targets without phase_number

-- SQLite doesn't support ALTER COLUMN directly, so we need to recreate the table

-- Step 1: Create new table with nullable phase_number
CREATE TABLE budget_targets_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phase_number INTEGER,  -- Now nullable
    month TEXT,
    category VARCHAR NOT NULL,
    monthly_target FLOAT NOT NULL,
    is_fixed BOOLEAN DEFAULT 0,
    notes TEXT
);

-- Step 2: Copy data from old table
INSERT INTO budget_targets_new (id, phase_number, month, category, monthly_target, is_fixed, notes)
SELECT id, phase_number, month, category, monthly_target, is_fixed, notes
FROM budget_targets;

-- Step 3: Drop old table
DROP TABLE budget_targets;

-- Step 4: Rename new table
ALTER TABLE budget_targets_new RENAME TO budget_targets;
