from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.deps import require_admin
from app.database.database import get_db
from app.models.issue import Issue
from app.models.product import Product
from app.models.user import User
from app.services.audit import create_audit_log

router = APIRouter(tags=["Customer Issues"])


class IssueCreate(BaseModel):
    product_id: str = Field(..., min_length=1, max_length=128)
    message: str = Field(..., min_length=3, max_length=2000)
    contact: Optional[str] = Field(None, max_length=200)
    latitude: Optional[float] = None
    longitude: Optional[float] = None


def _issue_dict(i: Issue) -> dict:
    return {
        "id": i.id,
        "product_id": i.product_id,
        "message": i.message,
        "contact": i.contact,
        "latitude": i.latitude,
        "longitude": i.longitude,
        "status": i.status,
        "created_at": i.created_at,
    }


@router.post("/issues", status_code=status.HTTP_201_CREATED)
async def raise_issue(payload: IssueCreate, db: Session = Depends(get_db)):
    """Public: a customer reports a problem from a scan report. No account needed."""
    code = payload.product_id.strip()
    # Issues may also be raised for codes that are NOT registered (likely fakes),
    # so we do not require the product to exist; we just record whether it does.
    issue = Issue(
        product_id=code,
        message=payload.message.strip(),
        contact=(payload.contact or "").strip() or None,
        latitude=payload.latitude,
        longitude=payload.longitude,
    )
    db.add(issue)
    db.commit()
    db.refresh(issue)
    registered = db.query(Product).filter(Product.product_id == code).first() is not None
    return {"message": "Issue recorded", "registered_product": registered, **_issue_dict(issue)}


@router.get("/admin/issues")
async def list_issues(
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Admin: list customer-reported issues, newest first."""
    q = db.query(Issue)
    if status_filter:
        q = q.filter(Issue.status == status_filter.upper())
    return [_issue_dict(i) for i in q.order_by(Issue.created_at.desc()).limit(limit).all()]


class IssueStatusUpdate(BaseModel):
    status: str


@router.put("/admin/issues/{issue_id}/status")
async def update_issue_status(
    issue_id: int,
    payload: IssueStatusUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    new_status = payload.status.upper()
    if new_status not in {"OPEN", "REVIEWED", "CLOSED"}:
        raise HTTPException(status_code=400, detail="Status must be OPEN, REVIEWED or CLOSED")
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    old_status = issue.status
    issue.status = new_status
    create_audit_log(
        db=db, action=f"ISSUE_{new_status}", entity_type="ISSUE", entity_id=str(issue.id),
        user_id=current_user.id, request=request,
        description=f"Customer issue #{issue.id} (product {issue.product_id}) changed from {old_status} to {new_status} by Admin '{current_user.email}'.",
    )
    db.commit()
    return _issue_dict(issue)
