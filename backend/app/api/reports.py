from __future__ import annotations
from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.plan import Milestone
from app.models.user import User
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/milestones")
def get_milestones(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    milestones = db.query(Milestone).order_by(Milestone.target_date.asc().nullslast()).all()
    return [
        {
            "id": m.id,
            "phase_number": m.phase_number,
            "name": m.name,
            "description": m.description,
            "target_date": m.target_date,
            "target_amount": m.target_amount,
            "actual_date": m.actual_date,
            "actual_amount": m.actual_amount,
            "is_achieved": m.is_achieved,
        }
        for m in milestones
    ]


@router.patch("/milestones/{milestone_id}")
def update_milestone(
    milestone_id: int,
    actual_date: date | None = None,
    actual_amount: float | None = None,
    is_achieved: bool | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    m = db.query(Milestone).filter(Milestone.id == milestone_id).first()
    if not m:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Milestone not found")
    if actual_date is not None:
        m.actual_date = actual_date
    if actual_amount is not None:
        m.actual_amount = actual_amount
    if is_achieved is not None:
        m.is_achieved = is_achieved
    db.commit()
    return {"message": "Updated"}
