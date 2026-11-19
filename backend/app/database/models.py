"""
SQLAlchemy models for FinGuard AI.

Design notes (so this is easy to defend in an interview):
- vendor_id / transaction_id / invoice_id are used as natural string
  primary keys (e.g. "VEND-0001") rather than surrogate integers, because
  they're already unique, human-readable, and match the synthetic CSVs
  exactly — no separate ID-mapping step needed when loading data.
- anomalies -> investigations -> audit_logs is a one-to-many chain
  mirroring the actual product workflow: an anomaly can be investigated,
  an investigation can have many audit log entries (approve/reject/
  escalate actions), never the other way around.
- JSON columns (signals, evidence) hold structured-but-variable data
  (lists of evidence strings, feature values) that don't need their own
  relational tables at this scale — keeps the schema simple without
  losing structure, since we still parse them as JSON, not free text.
"""

from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database.session import Base


class Vendor(Base):
    __tablename__ = "vendors"

    vendor_id = Column(String, primary_key=True)
    vendor_name = Column(String, nullable=False)
    vendor_age = Column(Integer, nullable=False)  # months since onboarding
    industry = Column(String, nullable=False)
    risk_level = Column(String, nullable=False)  # LOW / MEDIUM / HIGH
    total_transactions = Column(Integer, default=0)
    average_transaction = Column(Float, default=0.0)

    transactions = relationship("Transaction", back_populates="vendor")


class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(String, primary_key=True)
    date = Column(DateTime, nullable=False)
    vendor_id = Column(String, ForeignKey("vendors.vendor_id"), nullable=False)
    vendor_name = Column(String, nullable=False)  # denormalized for fast reads/display
    department = Column(String, nullable=False)
    category = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    payment_method = Column(String, nullable=False)
    invoice_id = Column(String, nullable=False, index=True)
    description = Column(Text)
    approval_status = Column(String, default="Pending")

    vendor = relationship("Vendor", back_populates="transactions")
    anomalies = relationship("Anomaly", back_populates="transaction")


class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    department = Column(String, nullable=False)
    month = Column(String, nullable=False)  # "YYYY-MM"
    budget = Column(Float, nullable=False)
    actual_spending = Column(Float, nullable=False)


class Receivable(Base):
    __tablename__ = "receivables"

    invoice_id = Column(String, primary_key=True)
    customer = Column(String, nullable=False)
    invoice_date = Column(DateTime, nullable=False)
    due_date = Column(DateTime, nullable=False)
    amount = Column(Float, nullable=False)
    payment_status = Column(String, nullable=False)  # Paid / Pending / Overdue


class Anomaly(Base):
    __tablename__ = "anomalies"
    __table_args__ = (UniqueConstraint("transaction_id", "type", name="uq_anomaly_transaction_type"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(String, ForeignKey("transactions.transaction_id"), nullable=False)
    type = Column(String, nullable=False)  # duplicate_invoice / amount_outlier / etc.
    risk_score = Column(Integer, nullable=False)  # 0-100
    signals = Column(JSON, default=list)  # list of evidence strings/feature values
    status = Column(String, default="Open")  # Open / Investigating / Resolved

    transaction = relationship("Transaction", back_populates="anomalies")
    investigations = relationship("Investigation", back_populates="anomaly")


class Investigation(Base):
    __tablename__ = "investigations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    anomaly_id = Column(Integer, ForeignKey("anomalies.id"), nullable=False)
    risk_score = Column(Integer, nullable=False)  # snapshot of the risk score at investigation time
    evidence = Column(JSON, default=list)
    ai_explanation = Column(Text)
    recommendation = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    anomaly = relationship("Anomaly", back_populates="investigations")
    audit_logs = relationship("AuditLog", back_populates="investigation")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    investigation_id = Column(Integer, ForeignKey("investigations.id"), nullable=False)
    user = Column(String, nullable=False)
    action = Column(String, nullable=False)  # Approve / Reject / Escalate
    comment = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

    investigation = relationship("Investigation", back_populates="audit_logs")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    role = Column(String, default="Finance Manager")


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    dataset_type = Column(String, nullable=False)
    filename = Column(String, nullable=False)
    status = Column(String, nullable=False)
    rows_received = Column(Integer, default=0)
    rows_created = Column(Integer, default=0)
    rows_updated = Column(Integer, default=0)
    anomalies_found = Column(Integer, default=0)
    error = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class AnalysisReport(Base):
    __tablename__ = "analysis_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ingestion_run_id = Column(Integer, ForeignKey("ingestion_runs.id"), nullable=False, unique=True)
    report = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Account(Base):
    """Company account metadata is global; financial records live in its own schema."""
    __tablename__ = "accounts"
    __table_args__ = {"schema": "public"}

    id = Column(String, primary_key=True)
    company_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class AccountUser(Base):
    __tablename__ = "account_users"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(String, ForeignKey("public.accounts.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True, index=True)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
