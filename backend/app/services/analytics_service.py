"""
Analytics service layer.

Route handlers (app/api/*) should stay thin — they parse the request,
call a function here, and serialize the result. All the actual logic
of "pull data from Postgres, hand it to the ML layer, shape the result"
lives here so it's testable without spinning up FastAPI at all.
"""

import pandas as pd
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.models import Anomaly
from app.ml.anomaly_detection import detect_anomalies
from app.ml.budget_analysis import analyze_budgets
from app.ml.cashflow_forecast import forecast_cashflow
from app.ml.duplicate_detection import find_duplicate_invoices
from app.ml.receivables_analysis import analyze_receivables, find_repeated_late_payers


def load_transactions_df(db: Session) -> pd.DataFrame:
    return pd.read_sql(text("SELECT * FROM transactions"), db.bind)


def load_vendors_df(db: Session) -> pd.DataFrame:
    return pd.read_sql(text("SELECT * FROM vendors"), db.bind)


def load_budgets_df(db: Session) -> pd.DataFrame:
    return pd.read_sql(text("SELECT * FROM budgets"), db.bind)


def load_receivables_df(db: Session) -> pd.DataFrame:
    return pd.read_sql(text("SELECT * FROM receivables"), db.bind)


def sync_anomalies(db: Session) -> list[Anomaly]:
    """Run duplicate + ML anomaly detection and insert any newly-found
    anomalies into the DB. Never duplicates or overwrites an existing
    anomaly row (and therefore never disturbs its investigation status)
    — matched on (transaction_id, type), enforced by a DB-level unique
    constraint (not just this in-memory check) since concurrent requests
    can both pass the in-memory check before either commits."""
    tx_df = load_transactions_df(db)
    vendors_df = load_vendors_df(db)

    existing_keys = {(a.transaction_id, a.type) for a in db.query(Anomaly).all()}

    dup_matches = find_duplicate_invoices(tx_df)
    ml_results = detect_anomalies(tx_df, vendors_df)

    candidates = []
    for match in dup_matches:
        key = (match.transaction_id_b, "duplicate_invoice")
        if key in existing_keys:
            continue
        existing_keys.add(key)
        candidates.append(
            Anomaly(
                transaction_id=match.transaction_id_b,
                type="duplicate_invoice",
                risk_score=int(match.combined_score),
                signals=match.reasons
                + [f"Matches transaction {match.transaction_id_a} (₹{match.amount_a} on {match.date_a})"],
                status="Open",
            )
        )

    for result in ml_results:
        if not result.is_anomaly:
            continue
        key = (result.transaction_id, "ml_anomaly")
        if key in existing_keys:
            continue
        existing_keys.add(key)
        candidates.append(
            Anomaly(
                transaction_id=result.transaction_id,
                type="ml_anomaly",
                risk_score=result.anomaly_score,
                signals=result.evidence,
                status="Open",
            )
        )

    # Insert one at a time: if a concurrent request wins a race on a given
    # (transaction_id, type) pair, the DB constraint rejects just that one
    # row (caught and skipped) instead of the whole batch's commit failing.
    for candidate in candidates:
        db.add(candidate)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()

    return db.query(Anomaly).order_by(Anomaly.risk_score.desc()).all()


def get_reference_date(db: Session):
    """The synthetic dataset lives in a fixed historical window (Mar-Aug 2025).
    Using wall-clock date.today() for 'days overdue' calculations would silently
    drift wrong as real time moves past that window (e.g. showing 400+ days
    overdue instead of the intended ~20-90 day range). Instead, derive 'today'
    from the data itself: one day after the latest known transaction/receivable
    date, matching how generate_synthetic_data.py defined its own 'as of' date."""
    tx_df = load_transactions_df(db)
    rec_df = load_receivables_df(db)
    latest_tx = pd.to_datetime(tx_df["date"]).max() if not tx_df.empty else None
    latest_due = pd.to_datetime(rec_df["due_date"]).max() if not rec_df.empty else None
    candidates = [d for d in (latest_tx, latest_due) if d is not None]
    if not candidates:
        from datetime import date as _date

        return _date.today()
    return (max(candidates) + pd.Timedelta(days=1)).date()


def get_budget_statuses(db: Session):
    return analyze_budgets(load_budgets_df(db))


def get_receivable_statuses(db: Session):
    return analyze_receivables(load_receivables_df(db), as_of=get_reference_date(db))


def get_repeated_late_payers(db: Session):
    return find_repeated_late_payers(load_receivables_df(db), as_of=get_reference_date(db))


def get_cashflow_forecast(db: Session):
    return forecast_cashflow(load_transactions_df(db), load_receivables_df(db))


def compute_financial_health_score(db: Session) -> tuple[int, dict]:
    """Transparent, componentized score — never a bare LLM-guessed number.
    Each sub-score is 0-100; the overall score is their average. Formula
    is deliberately simple and documented here so it can be explained
    in an interview without hand-waving."""
    budgets = get_budget_statuses(db)
    receivables = get_receivable_statuses(db)
    forecast = get_cashflow_forecast(db)
    anomalies = sync_anomalies(db)

    # Budget health: penalize by how many dept/months are HIGH or MEDIUM risk
    if budgets:
        risky = sum(1 for b in budgets if b.risk_level in ("HIGH", "MEDIUM"))
        budget_health = round(100 * (1 - risky / len(budgets)))
    else:
        budget_health = 100

    # Receivables health: penalize by overdue value as a share of total receivables value
    total_value = sum(r.amount for r in receivables) or 1
    overdue_value = sum(r.amount for r in receivables if r.payment_status == "Overdue")
    receivables_health = round(100 * (1 - min(1.0, overdue_value / total_value)))

    # Cash-flow health: penalize based on how soon a deficit is projected
    if forecast.days_until_deficit is None:
        cashflow_health = 100
    else:
        cashflow_health = round(max(0, min(100, (forecast.days_until_deficit / 60) * 100)))

    # Transaction risk health: penalize by open high-risk anomaly count relative to total transactions
    total_txns = len(load_transactions_df(db)) or 1
    high_risk_anomalies = sum(1 for a in anomalies if a.status == "Open" and a.risk_score >= 70)
    transaction_risk_health = round(max(0, 100 - (high_risk_anomalies / total_txns) * 1000))

    overall = round((budget_health + receivables_health + cashflow_health + transaction_risk_health) / 4)

    breakdown = {
        "budget_health": budget_health,
        "receivables_health": receivables_health,
        "cashflow_health": cashflow_health,
        "transaction_risk_health": transaction_risk_health,
    }
    return overall, breakdown