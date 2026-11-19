from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.database.models import Vendor
from app.database.session import get_db
from app.schemas.api_schemas import DashboardOut
from app.services.analytics_service import (
    compute_financial_health_score,
    get_budget_statuses,
    get_cashflow_forecast,
    get_receivable_statuses,
    get_reference_date,
    load_receivables_df,
    load_transactions_df,
)
from app.services.digest_service import build_digest_data
from app.services.digest_template import render_digest_html

router = APIRouter()


@router.get("", response_model=DashboardOut)
def get_dashboard(db: Session = Depends(get_db)):
    transactions_df = load_transactions_df(db)
    from app.database.models import Anomaly
    anomalies = db.query(Anomaly).all()
    open_anomalies = [a for a in anomalies if a.status == "Open"]
    high_risk_anomalies = [a for a in open_anomalies if a.risk_score >= 70]

    budgets = get_budget_statuses(db)
    budget_high_risk = [b for b in budgets if b.risk_level == "HIGH"]

    receivables_df = load_receivables_df(db)
    reference_date = get_reference_date(db, tx_df=transactions_df, rec_df=receivables_df)
    receivables = get_receivable_statuses(db, rec_df=receivables_df, as_of=reference_date)
    receivables_high_priority = [r for r in receivables if r.priority == "HIGH"]

    forecast = get_cashflow_forecast(db, tx_df=transactions_df, rec_df=receivables_df)

    score, breakdown = compute_financial_health_score(
        db, budgets=budgets, receivables=receivables, forecast=forecast,
        anomalies=anomalies, total_txns=len(transactions_df),
    )

    return DashboardOut(
        total_transactions=len(transactions_df),
        total_vendors=db.query(Vendor).count(),
        open_anomalies=len(open_anomalies),
        high_risk_anomalies=len(high_risk_anomalies),
        budget_high_risk_count=len(budget_high_risk),
        receivables_high_priority_count=len(receivables_high_priority),
        receivables_high_priority_value=round(sum(r.amount for r in receivables_high_priority), 2),
        cashflow_days_until_deficit=forecast.days_until_deficit,
        financial_health_score=score,
        financial_health_breakdown=breakdown,
        budget_reports=[b.__dict__ for b in budgets],
        top_anomalies=[
            {"id": a.id, "transaction_id": a.transaction_id, "type": a.type, "risk_score": a.risk_score}
            for a in sorted(open_anomalies, key=lambda item: item.risk_score, reverse=True)[:5]
        ],
        forecast_points=forecast.forecast_points,
    )


@router.get("/digest", response_class=HTMLResponse)
def preview_digest(db: Session = Depends(get_db)):
    """Renders the daily digest as HTML so you can preview it in a browser
    before scheduling the actual email send (see scripts/send_digest.py)."""
    data = build_digest_data(db)
    return render_digest_html(data)
