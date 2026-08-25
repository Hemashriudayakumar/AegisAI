import uuid
from typing import Any, Dict
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ProposedAction,
    AuthorizationEnvelope,
)
from app.graph.workflow import policy_graph

router = APIRouter(prefix="/api", tags=["chat"])

@router.post("/chat", response_model=ChatResponse)
async def process_chat(request: ChatRequest, db: Session = Depends(get_db)):
    request_id = f"REQ-{uuid.uuid4().hex[:6].upper()}"
    conversation_id = request.conversation_id or f"CONV-{uuid.uuid4().hex[:6].upper()}"
    
    initial_state = {
        "request_id": request_id,
        "conversation_id": conversation_id,
        "customer_id": request.customer_id,
        "customer_message": request.customer_message,
        "conversation_context": {
            "is_verified": request.is_verified,
            "manager_approved": request.manager_approved,
            "conversation_id": conversation_id,
        },
        "agent_b_called": False,
        "tool_executed": False,
    }
    
    try:
        final_state = policy_graph.invoke(initial_state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Policy workflow failed: {str(e)}")

    dec_dict = final_state.get("policy_decision") or {
        "decision": "ALLOW",
        "policy_id": "STANDARD_ALLOW_001",
        "policy_version": "v1.0",
        "severity": "LOW",
        "reason": "OK",
        "evidence": {},
        "requires_human_review": False,
        "safe_response": None
    }
    
    proposed_act_dict = final_state.get("proposed_action")
    proposed_action = ProposedAction(**proposed_act_dict) if proposed_act_dict else None

    approved_act_dict = final_state.get("approved_action")
    approved_action = AuthorizationEnvelope(**approved_act_dict) if approved_act_dict else None

    return ChatResponse(
        request_id=request_id,
        conversation_id=conversation_id,
        policy_version=dec_dict.get("policy_version", "v1.0"),
        decision=dec_dict.get("decision", "ALLOW"),
        severity=dec_dict.get("severity", "LOW"),
        policy_id=dec_dict.get("policy_id"),
        reason=dec_dict.get("reason", ""),
        evidence=dec_dict.get("evidence", {}),
        proposed_action=proposed_action,
        approved_action=approved_action,
        safe_response=dec_dict.get("safe_response"),
        requires_human_review=bool(dec_dict.get("requires_human_review", False)),
        tool_executed=bool(final_state.get("tool_executed", False)),
        tool_result=final_state.get("tool_result"),
        final_response=final_state.get("final_response", ""),
        agent_a_response=final_state.get("agent_a_response"),
        agent_b_called=bool(final_state.get("agent_b_called", False)),
        incident_id=final_state.get("incident_id"),
    )
