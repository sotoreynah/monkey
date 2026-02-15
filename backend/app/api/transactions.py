from __future__ import annotations
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import date
from app.database import get_db
from app.models.transaction import Transaction, TransactionSource
from app.models.user import User
from app.schemas.transaction import TransactionResponse, TransactionUpdate, TransactionSourceResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


@router.get("/sources", response_model=list[TransactionSourceResponse])
def get_sources(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """List transaction sources that have at least one transaction"""
    from sqlalchemy import func
    
    # Only return sources that have transactions
    sources = (
        db.query(TransactionSource)
        .join(Transaction, Transaction.source_id == TransactionSource.id)
        .filter(TransactionSource.active == True)
        .group_by(TransactionSource.id)
        .having(func.count(Transaction.id) > 0)
        .all()
    )
    return sources


@router.get("", response_model=dict)
def list_transactions(
    source_id: int | None = None,
    category: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    min_amount: float | None = None,
    max_amount: float | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = db.query(Transaction)

    if source_id:
        query = query.filter(Transaction.source_id == source_id)
    if category:
        query = query.filter(Transaction.category == category)
    if date_from:
        query = query.filter(Transaction.transaction_date >= date_from)
    if date_to:
        query = query.filter(Transaction.transaction_date <= date_to)
    if min_amount is not None:
        query = query.filter(Transaction.amount >= min_amount)
    if max_amount is not None:
        query = query.filter(Transaction.amount <= max_amount)
    if search:
        like = f"%{search}%"
        query = query.filter(
            (Transaction.description.ilike(like))
            | (Transaction.merchant.ilike(like))
            | (Transaction.memo.ilike(like))
        )

    total = query.count()
    transactions = (
        query.order_by(desc(Transaction.transaction_date))
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    # Attach source names
    source_map = {s.id: s.name for s in db.query(TransactionSource).all()}
    results = []
    for t in transactions:
        resp = TransactionResponse(
            id=t.id,
            source_id=t.source_id,
            source_name=source_map.get(t.source_id),
            transaction_date=t.transaction_date,
            description=t.description,
            merchant=t.merchant,
            category=t.category,
            transaction_type=t.transaction_type,
            amount=t.amount,
            is_debit=t.is_debit,
            memo=t.memo,
        )
        results.append(resp)

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
        "transactions": results,
    }


@router.get("/categories")
def get_categories(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    rows = db.query(Transaction.category).distinct().filter(Transaction.category.isnot(None)).all()
    return sorted([r[0] for r in rows])


@router.patch("/{transaction_id}")
def update_transaction(
    transaction_id: int,
    update: TransactionUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    txn = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not txn:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Transaction not found")

    if update.category is not None:
        txn.category = update.category
    if update.user_notes is not None:
        txn.user_notes = update.user_notes
    if update.is_excluded is not None:
        txn.is_excluded = update.is_excluded

    db.commit()
    return {"message": "Updated"}
