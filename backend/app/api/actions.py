"""
Human-in-the-loop actions.

Per the spec: AI recommends, a human decides. Every action here does two
things atomically: (1) writes an immutable audit_logs entry (who, when,
what action, optional comment) and (2) updates the parent anomaly's
status so the dashboard reflects the outcome. Nothing here is ever
triggered automatically by the AI layer — these endpoints only fire
from an explicit human action in the UI.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.models import Anomaly, AuditLog, Investigation
from app.database.session import get_db
from app.schemas.api_schemas import ActionRequest, AuditLogOut

router = APIRouter()


def _record_action(db: Session, request: ActionRequest, action: str, anomaly_status: str) -> AuditLog:
    investigation = db.query(Investigation).filter(Investigation.id == request.investigation_id).first()
    if not investigation:
        raise HTTPException(status_code=404, detail=f"Investigation {request.investigation_id} not found")

    anomaly = db.query(Anomaly).filter(Anomaly.id == investigation.anomaly_id).first()
    if not anomaly:
        raise HTTPException(status_code=404, detail=f"Anomaly for investigation {request.investigation_id} not found")

    log_entry = AuditLog(
        investigation_id=investigation.id,
        user=request.user,
        action=action,
        comment=request.comment,
    )
    db.add(log_entry)
    anomaly.status = anomaly_status
    db.commit()
    db.refresh(log_entry)
    return log_entry


@router.post("/approve", response_model=AuditLogOut)
def approve_action(request: ActionRequest, db: Session = Depends(get_db)):
    return _record_action(db, request, action="Approve", anomaly_status="Resolved")


@router.post("/reject", response_model=AuditLogOut)
def reject_action(request: ActionRequest, db: Session = Depends(get_db)):
    return _record_action(db, request, action="Reject", anomaly_status="Resolved")


@router.post("/escalate", response_model=AuditLogOut)
def escalate_action(request: ActionRequest, db: Session = Depends(get_db)):
    return _record_action(db, request, action="Escalate", anomaly_status="Escalated")
