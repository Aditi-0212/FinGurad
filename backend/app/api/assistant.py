from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.ai.assistant import ask_assistant
from app.database.session import get_db
from app.schemas.api_schemas import AssistantQueryRequest, AssistantQueryResponse

router = APIRouter()


@router.post("/query", response_model=AssistantQueryResponse)
def query_assistant(request: AssistantQueryRequest, db: Session = Depends(get_db)):
    try:
        result = ask_assistant(db, request.question)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Assistant request failed: {e}")
    return AssistantQueryResponse(**result)