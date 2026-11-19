"""Fast CSV imports and asynchronous post-import analysis."""

from io import BytesIO
from math import isfinite

import pandas as pd
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database.models import Account, AnalysisReport, Anomaly, Budget, IngestionRun, Receivable, Transaction, Vendor
from app.database.session import get_db, get_workspace_session

router = APIRouter()
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_ROWS = 50000
CHUNK_SIZE = 1000
REQUIRED_COLUMNS = {
    "vendors": {"vendor_id", "vendor_name", "vendor_age", "industry", "risk_level", "total_transactions", "average_transaction"},
    "transactions": {"transaction_id", "date", "vendor_id", "vendor_name", "department", "category", "amount", "payment_method", "invoice_id"},
    "budgets": {"department", "month", "budget", "actual_spending"},
    "receivables": {"invoice_id", "customer", "invoice_date", "due_date", "amount", "payment_status"},
}


def _rows(values, size=CHUNK_SIZE):
    for start in range(0, len(values), size):
        yield values[start : start + size]


def _date(value):
    return pd.to_datetime(value, errors="raise").to_pydatetime()


def _upsert_transactions(db: Session, df: pd.DataFrame):
    df = df.drop_duplicates("transaction_id", keep="last").copy()
    df["transaction_id"] = df["transaction_id"].astype(str)
    df["vendor_id"] = df["vendor_id"].astype(str)
    df["amount"] = pd.to_numeric(df["amount"], errors="raise")
    if not all(isfinite(float(value)) for value in df["amount"]):
        raise ValueError("Transaction amounts must be finite numbers")
    df["date"] = pd.to_datetime(df["date"], errors="raise")
    records = df.to_dict(orient="records")

    # A transaction export is sufficient to get started. Create minimal vendor
    # profiles for new vendor IDs, then enrich them later with a vendor upload.
    vendor_summaries = df.groupby("vendor_id").agg(
        vendor_name=("vendor_name", "last"),
        total_transactions=("transaction_id", "count"),
        average_transaction=("amount", "mean"),
    )
    vendor_ids = vendor_summaries.index.tolist()
    existing_vendor_ids = set()
    for batch in _rows(vendor_ids):
        existing_vendor_ids.update(
            item[0] for item in db.query(Vendor.vendor_id).filter(Vendor.vendor_id.in_(batch)).all()
        )
    missing_vendors = []
    for vendor_id, summary in vendor_summaries.iterrows():
        if vendor_id in existing_vendor_ids:
            continue
        missing_vendors.append({
            "vendor_id": vendor_id,
            "vendor_name": str(summary["vendor_name"]),
            "vendor_age": 0,
            "industry": "Unknown",
            "risk_level": "LOW",
            "total_transactions": int(summary["total_transactions"]),
            "average_transaction": float(summary["average_transaction"]),
        })
    if missing_vendors:
        db.bulk_insert_mappings(Vendor, missing_vendors)

    existing = {}
    transaction_ids = [str(row["transaction_id"]) for row in records]
    for batch in _rows(transaction_ids):
        for txn in db.query(Transaction).filter(Transaction.transaction_id.in_(batch)).all():
            existing[txn.transaction_id] = txn

    inserts, updates = [], []
    allowed = {column.name for column in Transaction.__table__.columns}
    for row in records:
        row["date"] = row["date"].to_pydatetime()
        row["vendor_id"] = str(row["vendor_id"])
        row["transaction_id"] = str(row["transaction_id"])
        row["invoice_id"] = str(row["invoice_id"])
        row["amount"] = float(row["amount"])
        description = row.get("description")
        row["description"] = None if pd.isna(description) else description
        approval_status = row.get("approval_status")
        row["approval_status"] = "Pending" if pd.isna(approval_status) or not approval_status else str(approval_status)
        for field in ("vendor_name", "department", "category", "payment_method"):
            row[field] = str(row[field])
        row = {key: value for key, value in row.items() if key in allowed}
        if row["transaction_id"] in existing:
            updates.append(row)
        else:
            inserts.append(row)
    for batch in _rows(inserts):
        db.bulk_insert_mappings(Transaction, batch)
    for batch in _rows(updates):
        db.bulk_update_mappings(Transaction, batch)
    return len(inserts), len(updates), len(records)


def _upsert_vendors(db: Session, df: pd.DataFrame):
    df = df.drop_duplicates("vendor_id", keep="last").copy()
    records = df.to_dict(orient="records")
    keys = [str(row["vendor_id"]) for row in records]
    existing = {}
    for batch in _rows(keys):
        existing.update({item.vendor_id: item for item in db.query(Vendor).filter(Vendor.vendor_id.in_(batch)).all()})
    inserts, updates = [], []
    for row in records:
        row.update(
            vendor_id=str(row["vendor_id"]), vendor_name=str(row["vendor_name"]),
            vendor_age=int(row["vendor_age"]), industry=str(row["industry"]),
            risk_level=str(row["risk_level"]).upper(), total_transactions=int(row["total_transactions"]),
            average_transaction=float(row["average_transaction"]),
        )
        if row["vendor_id"] in existing:
            updates.append(row)
        else:
            inserts.append(row)
    for batch in _rows(inserts):
        db.bulk_insert_mappings(Vendor, batch)
    for batch in _rows(updates):
        db.bulk_update_mappings(Vendor, batch)
    return len(inserts), len(updates)


def _upsert_budgets(db: Session, df: pd.DataFrame):
    df = df.drop_duplicates(["department", "month"], keep="last")
    existing = {(item.department, item.month): item for item in db.query(Budget).all()}
    inserts, updates = [], []
    for row in df.to_dict(orient="records"):
        key = (str(row["department"]), str(row["month"]))
        values = {"department": key[0], "month": key[1], "budget": float(row["budget"]), "actual_spending": float(row["actual_spending"])}
        if key in existing:
            updates.append({"id": existing[key].id, **values})
        else:
            inserts.append(values)
    for batch in _rows(inserts):
        db.bulk_insert_mappings(Budget, batch)
    for batch in _rows(updates):
        db.bulk_update_mappings(Budget, batch)
    return len(inserts), len(updates)


def _upsert_receivables(db: Session, df: pd.DataFrame):
    df = df.drop_duplicates("invoice_id", keep="last").copy()
    records = df.to_dict(orient="records")
    keys = [str(row["invoice_id"]) for row in records]
    existing = {}
    for batch in _rows(keys):
        existing.update({item.invoice_id: item for item in db.query(Receivable).filter(Receivable.invoice_id.in_(batch)).all()})
    inserts, updates = [], []
    for row in records:
        row.update(
            invoice_id=str(row["invoice_id"]), customer=str(row["customer"]),
            invoice_date=_date(row["invoice_date"]), due_date=_date(row["due_date"]),
            amount=float(row["amount"]), payment_status=str(row["payment_status"]).title(),
        )
        if row["invoice_id"] in existing:
            updates.append(row)
        else:
            inserts.append(row)
    for batch in _rows(inserts):
        db.bulk_insert_mappings(Receivable, batch)
    for batch in _rows(updates):
        db.bulk_update_mappings(Receivable, batch)
    return len(inserts), len(updates)


def analyze_ingestion_run(run_id: int, account_id: str):
    """Run the expensive model pass off the upload request and persist its report."""
    db = get_workspace_session(account_id)
    try:
        run = db.query(IngestionRun).filter(IngestionRun.id == run_id).first()
        if not run:
            return
        if run.dataset_type in ("transactions", "bundle"):
            from app.services.analytics_service import sync_anomalies
            anomalies = sync_anomalies(db)
        else:
            anomalies = db.query(Anomaly).order_by(Anomaly.risk_score.desc()).all()
        total_transactions = db.query(func.count(Transaction.transaction_id)).scalar() or 0
        total_vendors = db.query(func.count(Vendor.vendor_id)).scalar() or 0
        total_spend = db.query(func.sum(Transaction.amount)).scalar() or 0.0
        budget_count = db.query(func.count(Budget.id)).scalar() or 0
        receivable_count = db.query(func.count(Receivable.invoice_id)).scalar() or 0
        report = {
            "transactions": total_transactions,
            "vendors": total_vendors,
            "total_spend": round(float(total_spend), 2),
            "anomalies": len(anomalies),
            "high_risk_anomalies": sum(a.risk_score >= 70 for a in anomalies),
            "duplicate_invoices": sum(a.type == "duplicate_invoice" for a in anomalies),
            "ml_flags": sum(a.type == "ml_anomaly" for a in anomalies),
            "budgets": budget_count,
            "receivables": receivable_count,
            "top_anomalies": [
                {"id": a.id, "transaction_id": a.transaction_id, "type": a.type, "risk_score": a.risk_score, "signals": a.signals or []}
                for a in sorted(anomalies, key=lambda item: item.risk_score, reverse=True)[:10]
            ],
        }
        saved = db.query(AnalysisReport).filter(AnalysisReport.ingestion_run_id == run_id).first()
        if saved:
            saved.report = report
        else:
            db.add(AnalysisReport(ingestion_run_id=run_id, report=report))
        run.anomalies_found = len(anomalies)
        run.status = "completed"
        run.error = None
        db.commit()
    except Exception as exc:
        db.rollback()
        run = db.query(IngestionRun).filter(IngestionRun.id == run_id).first()
        if run:
            run.status = "failed"
            run.error = f"Import saved, but analysis failed: {str(exc)[:900]}"
            db.commit()
    finally:
        db.close()


@router.get("/runs")
def list_ingestion_runs(limit: int = 20, db: Session = Depends(get_db)):
    return db.query(IngestionRun).order_by(IngestionRun.created_at.desc()).limit(min(max(limit, 1), 100)).all()


@router.get("/workspace")
def get_workspace_summary(db: Session = Depends(get_db)):
    account_id = db.info["account_id"]
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=401, detail="This company workspace is unavailable")
    latest = db.query(IngestionRun).order_by(IngestionRun.created_at.desc()).first()
    return {
        "company_name": account.company_name,
        "counts": {
            "transactions": db.query(func.count(Transaction.transaction_id)).scalar() or 0,
            "vendors": db.query(func.count(Vendor.vendor_id)).scalar() or 0,
            "budgets": db.query(func.count(Budget.id)).scalar() or 0,
            "receivables": db.query(func.count(Receivable.invoice_id)).scalar() or 0,
        },
        "latest_import": {
            "filename": latest.filename,
            "status": latest.status,
            "created_at": latest.created_at,
        } if latest else None,
    }


@router.get("/runs/{run_id}")
def get_ingestion_run(run_id: int, db: Session = Depends(get_db)):
    run = db.query(IngestionRun).filter(IngestionRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Analysis run not found")
    result = db.query(AnalysisReport).filter(AnalysisReport.ingestion_run_id == run_id).first()
    return {"run": run, "report": result.report if result else None}


async def _read_dataset(upload: UploadFile, dataset_type: str):
    if not upload.filename or not upload.filename.lower().endswith(".csv"):
        raise ValueError(f"{dataset_type.title()} file must be a .csv")
    content = await upload.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise ValueError(f"{upload.filename} exceeds the 10 MB per-file limit")
    df = pd.read_csv(BytesIO(content))
    missing = sorted(REQUIRED_COLUMNS[dataset_type] - set(df.columns))
    if missing:
        raise ValueError(f"{upload.filename} is missing columns: {', '.join(missing)}")
    if df.empty:
        raise ValueError(f"{upload.filename} contains no data rows")
    if len(df) > MAX_ROWS:
        raise ValueError(f"{upload.filename} exceeds the {MAX_ROWS:,}-row per-file limit")
    blank_columns = [
        column for column in REQUIRED_COLUMNS[dataset_type]
        if df[column].isna().any() or df[column].astype(str).str.strip().eq("").any()
    ]
    if blank_columns:
        raise ValueError(f"{upload.filename} has blank values in: {', '.join(sorted(blank_columns))}")
    return df


@router.post("/upload-batch")
async def upload_batch(
    background_tasks: BackgroundTasks,
    transactions: UploadFile = File(...),
    vendors: UploadFile | None = File(default=None),
    budgets: UploadFile | None = File(default=None),
    receivables: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
):
    """Import a transaction CSV and any optional supporting CSVs as one workspace update."""
    uploads = {
        "vendors": vendors,
        "transactions": transactions,
        "budgets": budgets,
        "receivables": receivables,
    }
    selected = [(kind, upload) for kind, upload in uploads.items() if upload is not None]
    filenames = [upload.filename for _, upload in selected]
    run = IngestionRun(dataset_type="bundle", filename=", ".join(filenames)[:500], status="validating")
    db.add(run)
    db.commit()
    db.refresh(run)
    try:
        datasets = {}
        total_bytes = 0
        for kind, upload in selected:
            before = upload.size or 0
            df = await _read_dataset(upload, kind)
            total_bytes += before
            datasets[kind] = df
        if total_bytes > 20 * MAX_UPLOAD_BYTES:
            raise ValueError("Combined uploads are limited to 20 MB")
        run.rows_received = sum(len(frame) for frame in datasets.values())

        created = updated = 0
        if "vendors" in datasets:
            new, changed = _upsert_vendors(db, datasets["vendors"])
            created += new
            updated += changed
        new, changed, _ = _upsert_transactions(db, datasets["transactions"])
        created += new
        updated += changed
        for kind, upsert in (("budgets", _upsert_budgets), ("receivables", _upsert_receivables)):
            if kind in datasets:
                new, changed = upsert(db, datasets[kind])
                created += new
                updated += changed

        run.status = "processing"
        run.rows_created, run.rows_updated = created, updated
        db.commit()
        background_tasks.add_task(analyze_ingestion_run, run.id, db.info["account_id"])
        return {
            "run_id": run.id,
            "status": run.status,
            "filename": run.filename,
            "rows_received": run.rows_received,
        }
    except Exception as exc:
        db.rollback()
        failed = db.query(IngestionRun).filter(IngestionRun.id == run.id).first()
        if failed:
            failed.status = "failed"
            failed.error = str(exc)[:1000]
            db.commit()
        raise HTTPException(status_code=422, detail=f"Import failed: {exc}") from exc


@router.post("/upload")
async def upload_csv(
    background_tasks: BackgroundTasks,
    dataset_type: str = Form("transactions"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    dataset_type = dataset_type.strip().lower()
    if dataset_type not in REQUIRED_COLUMNS:
        raise HTTPException(status_code=422, detail=f"dataset_type must be one of: {', '.join(REQUIRED_COLUMNS)}")
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=415, detail="Upload a .csv file")
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="CSV uploads are limited to 10 MB")

    run = IngestionRun(dataset_type=dataset_type, filename=file.filename, status="validating")
    db.add(run)
    db.commit()
    db.refresh(run)
    try:
        df = pd.read_csv(BytesIO(content))
        missing = sorted(REQUIRED_COLUMNS[dataset_type] - set(df.columns))
        if missing:
            raise ValueError(f"Missing required columns: {', '.join(missing)}")
        blank_columns = [
            column for column in REQUIRED_COLUMNS[dataset_type]
            if df[column].isna().any() or df[column].astype(str).str.strip().eq("").any()
        ]
        if blank_columns:
            raise ValueError(f"Required columns contain blank values: {', '.join(sorted(blank_columns))}")
        if df.empty:
            raise ValueError("The CSV contains no data rows")
        if len(df) > MAX_ROWS:
            raise ValueError(f"A single upload can contain at most {MAX_ROWS:,} rows")
        run.rows_received = len(df)
        if dataset_type == "transactions":
            created, updated, _ = _upsert_transactions(db, df)
        else:
            created = updated = 0
            if dataset_type == "vendors":
                df = df.drop_duplicates("vendor_id", keep="last")
                model, key, date_cols = Vendor, "vendor_id", ()
            elif dataset_type == "budgets":
                df = df.drop_duplicates(["department", "month"], keep="last")
                model, key, date_cols = Budget, None, ()
            else:
                df = df.drop_duplicates("invoice_id", keep="last")
                model, key, date_cols = Receivable, "invoice_id", ("invoice_date", "due_date")
            for row in df.to_dict(orient="records"):
                row = {name: (None if pd.isna(value) else value) for name, value in row.items()}
                if dataset_type == "vendors":
                    row.update(vendor_id=str(row["vendor_id"]), vendor_age=int(row["vendor_age"]),
                               risk_level=str(row["risk_level"]).upper(), total_transactions=int(row["total_transactions"]),
                               average_transaction=float(row["average_transaction"]))
                elif dataset_type == "budgets":
                    row.update(budget=float(row["budget"]), actual_spending=float(row["actual_spending"]))
                    existing = db.query(Budget).filter(Budget.department == row["department"], Budget.month == row["month"]).first()
                    if existing:
                        existing.budget, existing.actual_spending = row["budget"], row["actual_spending"]
                        updated += 1
                    else:
                        db.add(Budget(**{k: row[k] for k in ("department", "month", "budget", "actual_spending")}))
                        created += 1
                    continue
                else:
                    row["invoice_id"] = str(row["invoice_id"])
                    row["payment_status"] = str(row["payment_status"]).title()
                    for column in date_cols:
                        row[column] = _date(row[column])
                    row["amount"] = float(row["amount"])
                existing = db.query(model).filter(getattr(model, key) == str(row[key])).first()
                allowed = {column.name for column in model.__table__.columns}
                row = {k: v for k, v in row.items() if k in allowed}
                if existing:
                    for column, value in row.items():
                        setattr(existing, column, value)
                    updated += 1
                else:
                    db.add(model(**row))
                    created += 1
        run.status = "processing"
        run.rows_created, run.rows_updated = created, updated
        db.commit()
        background_tasks.add_task(analyze_ingestion_run, run.id, db.info["account_id"])
        return {"run_id": run.id, "status": run.status, "filename": run.filename, "rows_received": run.rows_received}
    except Exception as exc:
        db.rollback()
        failed = db.query(IngestionRun).filter(IngestionRun.id == run.id).first()
        if failed:
            failed.status = "failed"
            failed.error = str(exc)[:1000]
            failed.rows_received = locals().get("df", pd.DataFrame()).shape[0]
            db.commit()
        raise HTTPException(status_code=422, detail=f"Ingestion failed: {exc}") from exc
