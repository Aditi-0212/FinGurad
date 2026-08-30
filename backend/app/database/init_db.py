"""
Initializes the database: creates all tables (if they don't exist) and
loads the synthetic CSVs from backend/data/ into them.

Why a plain script instead of Alembic migrations: at buildathon scale,
with one developer and a schema that isn't expected to evolve through
multiple deployed versions, `Base.metadata.create_all` is the simplest
reliable approach — it creates exactly what the models define, once.
Alembic would be the right call for a team shipping incremental schema
changes over time; that's a deliberate scope choice, not an oversight.

This script is idempotent for demo purposes: it wipes and reloads the
four base tables every run, so re-running it after regenerating the CSVs
always leaves the database in a known, consistent state. It does NOT
touch anomalies/investigations/audit_logs — those are created by the
application itself (Phase 4+), not seeded from CSV.

Run from backend/:
    python -m app.database.init_db
"""

import os

import pandas as pd

from app.database.models import Budget, Receivable, Transaction, Vendor
from app.database.session import Base, SessionLocal, engine

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")


def create_tables():
    Base.metadata.create_all(bind=engine)
    print("Tables created (or already existed).")


def clear_tables(db):
    """Delete in child-to-parent order so foreign keys never block a clean
    reload. Once the app has run (Phase 8+), audit_logs/investigations/
    anomalies all transitively reference transactions, so a full CSV reload
    must clear that whole chain too — those rows would be stale anyway
    once transaction IDs are regenerated fresh from the CSVs."""
    from app.database.models import AuditLog, Investigation, Anomaly

    db.query(AuditLog).delete()
    db.query(Investigation).delete()
    db.query(Anomaly).delete()
    db.query(Transaction).delete()
    db.query(Vendor).delete()
    db.query(Budget).delete()
    db.query(Receivable).delete()
    db.commit()


def load_vendors(db):
    df = pd.read_csv(os.path.join(DATA_DIR, "vendors.csv"))
    for _, row in df.iterrows():
        db.add(
            Vendor(
                vendor_id=row["vendor_id"],
                vendor_name=row["vendor_name"],
                vendor_age=int(row["vendor_age"]),
                industry=row["industry"],
                risk_level=row["risk_level"],
                total_transactions=int(row["total_transactions"]),
                average_transaction=float(row["average_transaction"]),
            )
        )
    db.commit()
    print(f"Loaded {len(df)} vendors.")


def load_transactions(db):
    df = pd.read_csv(os.path.join(DATA_DIR, "transactions.csv"), parse_dates=["date"])
    for _, row in df.iterrows():
        db.add(
            Transaction(
                transaction_id=row["transaction_id"],
                date=row["date"],
                vendor_id=row["vendor_id"],
                vendor_name=row["vendor_name"],
                department=row["department"],
                category=row["category"],
                amount=float(row["amount"]),
                payment_method=row["payment_method"],
                invoice_id=row["invoice_id"],
                description=row["description"],
                approval_status=row["approval_status"],
            )
        )
    db.commit()
    print(f"Loaded {len(df)} transactions.")


def load_budgets(db):
    df = pd.read_csv(os.path.join(DATA_DIR, "budgets.csv"))
    for _, row in df.iterrows():
        db.add(
            Budget(
                department=row["department"],
                month=row["month"],
                budget=float(row["budget"]),
                actual_spending=float(row["actual_spending"]),
            )
        )
    db.commit()
    print(f"Loaded {len(df)} budget rows.")


def load_receivables(db):
    df = pd.read_csv(os.path.join(DATA_DIR, "receivables.csv"), parse_dates=["invoice_date", "due_date"])
    for _, row in df.iterrows():
        db.add(
            Receivable(
                invoice_id=row["invoice_id"],
                customer=row["customer"],
                invoice_date=row["invoice_date"],
                due_date=row["due_date"],
                amount=float(row["amount"]),
                payment_status=row["payment_status"],
            )
        )
    db.commit()
    print(f"Loaded {len(df)} receivables.")


def main():
    create_tables()
    db = SessionLocal()
    try:
        # Clear child tables before parent tables (FK constraint), then
        # reload in parent-before-child order: vendors before transactions.
        clear_tables(db)
        load_vendors(db)
        load_transactions(db)
        load_budgets(db)
        load_receivables(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()