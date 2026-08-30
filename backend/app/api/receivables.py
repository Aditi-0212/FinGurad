from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.api_schemas import ReceivableOut, RepeatedLatePayerOut
from app.services.analytics_service import get_receivable_statuses, get_repeated_late_payers

router = APIRouter()


@router.get("", response_model=list[ReceivableOut])
def list_receivables(db: Session = Depends(get_db)):
    return get_receivable_statuses(db)


@router.get("/repeated-late-payers", response_model=list[RepeatedLatePayerOut])
def repeated_late_payers(db: Session = Depends(get_db)):
    return get_repeated_late_payers(db)
