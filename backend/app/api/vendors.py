from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.models import Vendor
from app.database.session import get_db
from app.schemas.api_schemas import VendorOut

router = APIRouter()


@router.get("", response_model=list[VendorOut])
def list_vendors(db: Session = Depends(get_db)):
    return db.query(Vendor).order_by(Vendor.vendor_name).all()


@router.get("/{vendor_id}", response_model=VendorOut)
def get_vendor(vendor_id: str, db: Session = Depends(get_db)):
    vendor = db.query(Vendor).filter(Vendor.vendor_id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail=f"Vendor {vendor_id} not found")
    return vendor
