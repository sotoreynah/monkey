-- Migration: Add format_hint to transaction_sources
-- Date: 2026-02-14
-- Description: Allow custom source names with specified parser format

ALTER TABLE transaction_sources ADD COLUMN format_hint TEXT;
