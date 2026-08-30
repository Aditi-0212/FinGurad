from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.ai.controller import investigate_anomaly
from app.database.models import Anomaly, Investigation
from app.database.session import get_db
from app.schemas.api_schemas import AnomalyOut, InvestigationOut
from app.services.analytics_service import sync_anomalies

router = APIRouter()


@router.get("", response_model=list[AnomalyOut])
def list_anomalies(status: str | None = None, db: Session = Depends(get_db)):
    anomalies = sync_anomalies(db)
    if status:
        anomalies = [a for a in anomalies if a.status == status]
    return anomalies


@router.get("/{anomaly_id}", response_model=AnomalyOut)
def get_anomaly(anomaly_id: int, db: Session = Depends(get_db)):
    anomaly = db.query(Anomaly).filter(Anomaly.id == anomaly_id).first()
    if not anomaly:
        raise HTTPException(status_code=404, detail=f"Anomaly {anomaly_id} not found")
    return anomaly


@router.post("/{anomaly_id}/investigate", response_model=InvestigationOut)
def investigate(anomaly_id: int, db: Session = Depends(get_db)):
    anomaly = db.query(Anomaly).filter(Anomaly.id == anomaly_id).first()
    if not anomaly:
        raise HTTPException(status_code=404, detail=f"Anomaly {anomaly_id} not found")

    try:
        result = investigate_anomaly(db, anomaly_id)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI investigation failed: {e}")

    investigation = Investigation(
        anomaly_id=anomaly_id,
        risk_score=result.get("risk_score", anomaly.risk_score),
        evidence=result.get("evidence", []),
        ai_explanation=result.get("explanation", ""),
        recommendation=result.get("recommendation", ""),
    )
    db.add(investigation)

    anomaly.status = "Investigating"

    db.commit()
    db.refresh(investigation)
    return investigation