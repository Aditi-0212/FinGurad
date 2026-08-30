from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.api_schemas import CashflowOut
from app.services.analytics_service import get_cashflow_forecast

router = APIRouter()


@router.get("", response_model=CashflowOut)
def get_cashflow(db: Session = Depends(get_db)):
    forecast = get_cashflow_forecast(db)
    return CashflowOut(**forecast.__dict__)
