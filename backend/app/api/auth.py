"""Company signup and login endpoints."""

import re
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.models import Account, AccountUser
from app.database.session import Base, create_workspace_tables, engine, get_db, get_public_db
from app.security import hash_password, issue_token, verify_password

router = APIRouter()


class RegisterRequest(BaseModel):
    company_name: str = Field(min_length=2, max_length=160)
    name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=10, max_length=256)


class LoginRequest(BaseModel):
    email: str
    password: str


def _auth_tables():
    Base.metadata.create_all(bind=engine, tables=[Account.__table__, AccountUser.__table__])


def _session_response(account: Account, user: AccountUser):
    return {
        "access_token": issue_token(account.id, user.id, user.name, user.email),
        "token_type": "bearer",
        "account_id": account.id,
        "company_name": account.company_name,
        "name": user.name,
        "email": user.email,
    }


@router.post("/register")
def register(payload: RegisterRequest, db: Session = Depends(get_public_db)):
    email = payload.email.strip().lower()
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        raise HTTPException(status_code=422, detail="Enter a valid email address")
    _auth_tables()
    account_id = str(uuid.uuid4())
    account = Account(id=account_id, company_name=payload.company_name.strip())
    user = AccountUser(
        account_id=account_id,
        name=payload.name.strip(),
        email=email,
        password_hash=hash_password(payload.password),
    )
    db.add_all([account, user])
    try:
        db.flush()
        create_workspace_tables(account_id)
        db.commit()
        db.refresh(user)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="An account already uses this email. Sign in instead.") from exc
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail=f"Could not create the isolated workspace: {exc}") from exc
    return _session_response(account, user)


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_public_db)):
    _auth_tables()
    user = db.query(AccountUser).filter(AccountUser.email == payload.email.strip().lower()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email or password is incorrect")
    account = db.query(Account).filter(Account.id == user.account_id).first()
    if not account:
        raise HTTPException(status_code=401, detail="This workspace is unavailable")
    return _session_response(account, user)


@router.get("/me")
def current_session(request: Request, db: Session = Depends(get_db)):
    identity = request.state.identity
    account = db.query(Account).filter(Account.id == identity["account_id"]).first()
    if not account:
        raise HTTPException(status_code=401, detail="This workspace is unavailable")
    return {**identity, "company_name": account.company_name}
