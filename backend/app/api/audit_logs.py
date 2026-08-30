from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.models import AuditLog
from app.database.session import get_db
from app.schemas.api_schemas import AuditLogOut

router = APIRouter()


@router.get("", response_model=list[AuditLogOut])
def list_audit_logs(investigation_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(AuditLog)
    if investigation_id:
        query = query.filter(AuditLog.investigation_id == investigation_id)
    return query.order_by(AuditLog.timestamp.desc()).all()
