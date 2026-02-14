from __future__ import annotations
from pydantic import BaseModel
from datetime import date
from typing import Optional


class TransactionResponse(BaseModel):
    id: int
    source_id: int
    source_name: str | None = None
    transaction_date: date
    description: str
    merchant: str | None
    category: str | None
    transaction_type: str | None
    amount: float
    is_debit: bool
    memo: str | None = None

    class Config:
        from_attributes = True


class TransactionFilter(BaseModel):
    source_id: int | None = None
    category: str | None = None
    date_from: date | None = None
    date_to: date | None = None
    min_amount: float | None = None
    max_amount: float | None = None
    search: str | None = None
    page: int = 1
    per_page: int = 50


class TransactionUpdate(BaseModel):
    category: str | None = None
    user_notes: str | None = None
    is_excluded: bool | None = None


class TransactionSourceResponse(BaseModel):
    id: int
    name: str
    type: str
    institution: str | None
    active: bool

    class Config:
        from_attributes = True


class ImportResponse(BaseModel):
    batch_id: str
    filename: str
    source_name: str
    rows_imported: int
    rows_skipped: int
    date_range_start: date | None
    date_range_end: date | None
