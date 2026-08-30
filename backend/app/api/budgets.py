from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.api_schemas import BudgetOut
from app.services.analytics_service import get_budget_statuses

router = APIRouter()


@router.get("", response_model=list[BudgetOut])
def list_budgets(db: Session = Depends(get_db)):
    return get_budget_statuses(db)
