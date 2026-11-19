"""
Database engine and account-scoped session management.

Public account identities use the shared registry. Every authenticated
request binds its ORM session to that account's PostgreSQL schema, keeping
financial tables physically separate between company workspaces.
"""

from sqlalchemy import create_engine
from sqlalchemy import event
from sqlalchemy.orm import Session as SQLAlchemySession, declarative_base, sessionmaker
from fastapi import HTTPException, Request

from app.config import get_settings

settings = get_settings()

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


@event.listens_for(SQLAlchemySession, "after_begin")
def _set_workspace_search_path(session, transaction, connection):
    schema = session.info.get("workspace_schema")
    if schema:
        connection.exec_driver_sql(f'SET LOCAL search_path TO "{schema}", public')


def _workspace_engine(account_id: str, create_schema: bool = False):
    from app.security import workspace_schema

    schema = workspace_schema(account_id)
    if create_schema:
        with engine.begin() as connection:
            connection.exec_driver_sql(f'CREATE SCHEMA IF NOT EXISTS "{schema}"')
    return engine.execution_options(schema_translate_map={None: schema})


def create_workspace_tables(account_id: str):
    from app.database.models import (
        AnalysisReport, Anomaly, AuditLog, Budget, IngestionRun, Investigation,
        Receivable, Transaction, Vendor,
    )

    tables = [
        Vendor.__table__, Transaction.__table__, Budget.__table__, Receivable.__table__,
        Anomaly.__table__, Investigation.__table__, AuditLog.__table__,
        IngestionRun.__table__, AnalysisReport.__table__,
    ]
    Base.metadata.create_all(bind=_workspace_engine(account_id, create_schema=True), tables=tables)


def get_workspace_session(account_id: str):
    from app.security import workspace_schema

    schema = workspace_schema(account_id)
    db = SessionLocal(bind=_workspace_engine(account_id))
    db.info["account_id"] = account_id
    db.info["workspace_schema"] = schema
    return db


def get_public_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db(request: Request):
    from app.security import read_token

    authorization = request.headers.get("authorization", "")
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Sign in to access your finance workspace")
    try:
        identity = read_token(authorization[7:].strip())
        account_id = identity["account_id"]
    except (ValueError, KeyError):
        raise HTTPException(status_code=401, detail="Your session is invalid or expired. Please sign in again.")
    db = get_workspace_session(account_id)
    try:
        request.state.identity = identity
        yield db
    finally:
        db.close()
