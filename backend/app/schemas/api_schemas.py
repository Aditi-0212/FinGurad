"""
Pydantic response/request models for the API layer.

Kept separate from the SQLAlchemy models (app/database/models.py) on
purpose: DB models describe storage, these describe the API contract.
They usually look similar but shouldn't be the same class — e.g. we
never want to accidentally expose a raw SQLAlchemy relationship object
in a JSON response.
"""

from datetime import date, datetime

from pydantic import BaseModel


class VendorOut(BaseModel):
    vendor_id: str
    vendor_name: str
    vendor_age: int
    industry: str
    risk_level: str
    total_transactions: int
    average_transaction: float

    model_config = {"from_attributes": True}


class TransactionOut(BaseModel):
    transaction_id: str
    date: datetime
    vendor_id: str
    vendor_name: str
    department: str
    category: str
    amount: float
    payment_method: str
    invoice_id: str
    description: str | None
    approval_status: str

    model_config = {"from_attributes": True}


class BudgetOut(BaseModel):
    department: str
    month: str
    budget: float
    actual_spending: float
    remaining_budget: float
    utilization_pct: float
    overrun_pct: float
    risk_level: str


class ReceivableOut(BaseModel):
    invoice_id: str
    customer: str
    amount: float
    due_date: str
    days_overdue: int
    payment_status: str
    priority: str


class RepeatedLatePayerOut(BaseModel):
    customer: str
    overdue_invoice_count: int


class AnomalyOut(BaseModel):
    id: int
    transaction_id: str
    type: str
    risk_score: int
    signals: list
    status: str

    model_config = {"from_attributes": True}


class InvestigationOut(BaseModel):
    id: int
    anomaly_id: int
    risk_score: int
    evidence: list[str]
    ai_explanation: str
    recommendation: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ActionRequest(BaseModel):
    investigation_id: int
    user: str
    comment: str | None = None


class AuditLogOut(BaseModel):
    id: int
    investigation_id: int
    user: str
    action: str
    comment: str | None
    timestamp: datetime

    model_config = {"from_attributes": True}


class AssistantQueryRequest(BaseModel):
    question: str


class AssistantQueryResponse(BaseModel):
    answer: str
    tool_calls_made: list[str]


class CashflowOut(BaseModel):
    as_of_date: str
    current_cash_estimate: float
    daily_net_change_trend: float
    projected_deficit_date: str | None
    days_until_deficit: int | None
    forecast_points: list[dict]


class DashboardOut(BaseModel):
    total_transactions: int
    total_vendors: int
    open_anomalies: int
    high_risk_anomalies: int
    budget_high_risk_count: int
    receivables_high_priority_count: int
    receivables_high_priority_value: float
    cashflow_days_until_deficit: int | None
    financial_health_score: int
    financial_health_breakdown: dict