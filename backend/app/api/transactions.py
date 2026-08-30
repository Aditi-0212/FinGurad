from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.models import Transaction
from app.database.session import get_db
from app.schemas.api_schemas import TransactionOut

router = APIRouter()


@router.get("", response_model=list[TransactionOut])
def list_transactions(
    department: str | None = None,
    vendor_id: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Transaction)
    if department:
        query = query.filter(Transaction.department == department)
    if vendor_id:
        query = query.filter(Transaction.vendor_id == vendor_id)
    return query.order_by(Transaction.date.desc()).all()


@router.get("/{transaction_id}", response_model=TransactionOut)
def get_transaction(transaction_id: str, db: Session = Depends(get_db)):
    txn = db.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()
    if not txn:
        raise HTTPException(status_code=404, detail=f"Transaction {transaction_id} not found")
    return txn
