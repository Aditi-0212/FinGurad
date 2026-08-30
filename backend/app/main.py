"""
FastAPI application entrypoint.

Kept intentionally thin: this file wires up middleware and routers only.
Business logic lives in app/services, ML in app/ml, AI orchestration in
app/ai — main.py should never grow business logic of its own.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import actions, anomalies, assistant, audit_logs, budgets, cashflow, dashboard, receivables, transactions, vendors
from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title="FinGuard AI",
    description="Evidence-driven AI Finance Controller API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok", "environment": settings.environment}


app.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
app.include_router(vendors.router, prefix="/vendors", tags=["vendors"])
app.include_router(budgets.router, prefix="/budgets", tags=["budgets"])
app.include_router(receivables.router, prefix="/receivables", tags=["receivables"])
app.include_router(cashflow.router, prefix="/cashflow", tags=["cashflow"])
app.include_router(anomalies.router, prefix="/anomalies", tags=["anomalies"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
app.include_router(actions.router, prefix="/actions", tags=["actions"])
app.include_router(audit_logs.router, prefix="/audit-logs", tags=["audit-logs"])
app.include_router(assistant.router, prefix="/assistant", tags=["assistant"])