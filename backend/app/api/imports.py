from __future__ import annotations
import os
import uuid
import hashlib
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Form
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.transaction import ImportBatch, TransactionSource
from app.models.user import User
from app.services.import_service import ImportService
from app.schemas.transaction import ImportResponse
from app.api.deps import get_current_user
from app.config import get_settings

router = APIRouter(prefix="/api/imports", tags=["imports"])
settings = get_settings()


@router.post("/upload", response_model=ImportResponse)
async def upload_csv(
    file: UploadFile = File(...),
    source_id: int | None = Form(None),
    source_name: str | None = Form(None),
    source_format: str | None = Form(None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    if not file.filename.endswith((".csv", ".CSV")):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    # Save uploaded file
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(settings.UPLOAD_DIR, f"{uuid.uuid4()}_{file.filename}")
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    file_hash = hashlib.sha256(content).hexdigest()

    # Check for duplicate file upload
    existing = db.query(ImportBatch).filter(ImportBatch.file_hash == file_hash).first()
    if existing:
        os.remove(file_path)
        raise HTTPException(status_code=409, detail=f"This file was already imported on {existing.imported_at}")

    try:
        service = ImportService(db)
        result = service.import_csv(file_path, file_hash, file.filename, source_id, source_name, source_format)
        return result
    except ValueError as e:
        os.remove(file_path)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.get("/history")
def import_history(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    batches = db.query(ImportBatch).order_by(ImportBatch.imported_at.desc()).limit(50).all()
    return [
        {
            "batch_id": b.batch_id,
            "filename": b.filename,
            "source_name": b.source.name if b.source else "Unknown",
            "rows_imported": b.rows_imported,
            "rows_skipped": b.rows_skipped,
            "date_range_start": b.date_range_start,
            "date_range_end": b.date_range_end,
            "imported_at": b.imported_at,
        }
        for b in batches
    ]


@router.get("/sources")
def list_sources(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """List transaction sources with actual transactions (in use)"""
    from sqlalchemy import func
    from app.models.transaction import Transaction
    
    # Only return sources that have at least one transaction
    sources = (
        db.query(TransactionSource)
        .join(Transaction, Transaction.source_id == TransactionSource.id)
        .filter(TransactionSource.active == True)
        .group_by(TransactionSource.id)
        .having(func.count(Transaction.id) > 0)
        .all()
    )
    return [{"id": s.id, "name": s.name, "type": s.type} for s in sources]
