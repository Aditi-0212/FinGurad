"""
Daily digest generation.

Reuses the same analytics functions the dashboard already calls — this
is deliberately not a separate data path. The digest is just a
different *presentation* (email-friendly HTML) of the same numbers a
finance manager would see on the dashboard, so there's no risk of the
digest and the dashboard ever disagreeing with each other.
"""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from app.services.analytics_service import (
    compute_financial_health_score,
    get_budget_statuses,
    get_cashflow_forecast,
    get_receivable_statuses,
    sync_anomalies,
)


@dataclass
class DigestData:
    generated_at: str
    health_score: int
    health_breakdown: dict
    open_anomaly_count: int
    high_risk_anomalies: list  # top 5, each a dict
    budget_overruns: list  # dept/month over budget
    high_priority_receivables: list  # top 5 by amount
    cashflow_current: float
    cashflow_days_until_deficit: int | None


def build_digest_data(db: Session) -> DigestData:
    anomalies = sync_anomalies(db)
    open_anomalies = [a for a in anomalies if a.status == "Open"]
    top_anomalies = sorted(open_anomalies, key=lambda a: a.risk_score, reverse=True)[:5]

    budgets = get_budget_statuses(db)
    overruns = [b for b in budgets if b.overrun_pct > 0]

    receivables = get_receivable_statuses(db)
    high_priority_receivables = sorted(
        [r for r in receivables if r.payment_status == "Overdue"], key=lambda r: r.amount, reverse=True
    )[:5]

    forecast = get_cashflow_forecast(db)
    score, breakdown = compute_financial_health_score(db)

    return DigestData(
        generated_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        health_score=score,
        health_breakdown=breakdown,
        open_anomaly_count=len(open_anomalies),
        high_risk_anomalies=[
            {"transaction_id": a.transaction_id, "type": a.type, "risk_score": a.risk_score} for a in top_anomalies
        ],
        budget_overruns=[
            {"department": b.department, "month": b.month, "overrun_pct": b.overrun_pct} for b in overruns
        ],
        high_priority_receivables=[
            {"customer": r.customer, "amount": r.amount, "days_overdue": r.days_overdue}
            for r in high_priority_receivables
        ],
        cashflow_current=forecast.current_cash_estimate,
        cashflow_days_until_deficit=forecast.days_until_deficit,
    )
