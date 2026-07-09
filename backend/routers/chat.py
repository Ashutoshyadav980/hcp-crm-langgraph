from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from database.database import get_db
from models import models
from schemas import schemas
from auth.auth import get_current_user
from agent_graph.agent import run_crm_agent

router = APIRouter(prefix="/api/chat", tags=["AI Chat"])

class ChatRequest(BaseModel):
    message: str
    active_interaction_id: Optional[int] = None
    chat_history: Optional[List[dict]] = []

@router.post("", response_model=schemas.ChatResponse)
def handle_chat_message(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    try:
        # Run LangGraph Agent
        result = run_crm_agent(
            user_id=current_user.id,
            message=payload.message,
            db=db,
            active_interaction_id=payload.active_interaction_id,
            chat_history=payload.chat_history
        )
        return schemas.ChatResponse(
            response=result["response"],
            tool_triggered=result["tool_triggered"],
            extracted_data=result["extracted_data"],
            chat_history=result["chat_history"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in LangGraph Agent execution: {str(e)}"
        )
