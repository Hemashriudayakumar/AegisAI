import pytest
from app.services.context_service import context_service
from app.policies.engine import policy_engine
from app.schemas.chat import ProposedAction

def test_context_load_and_save(db):
    """Test loading and saving context in database."""
    conv_id = "CONV-CTX-TEST-01"
    cust_id = "CUST-CTX-99"

    ctx = context_service.load_context(db, conversation_id=conv_id, customer_id=cust_id)
    assert ctx.conversation_id == conv_id
    assert ctx.customer_id == cust_id
    assert ctx.customer_verified is False
    assert ctx.previous_refunds == []
    assert ctx.complaint_count == 0

    # Update verification
    ctx = context_service.set_verification(db, ctx, is_verified=True)
    assert ctx.customer_verified is True
    assert ctx.verified_at is not None

    # Reload from DB and verify persistence
    ctx_reloaded = context_service.load_context(db, conversation_id=conv_id)
    assert ctx_reloaded.customer_verified is True
    assert ctx_reloaded.verified_at is not None

def test_context_update_for_refund(db):
    """Test updating and persisting refunds in context."""
    conv_id = "CONV-CTX-TEST-REFUND"
    ctx = context_service.load_context(db, conversation_id=conv_id, customer_id="CUST-10")
    
    ctx = context_service.update_context_for_refund(db, ctx, order_id="ORD-101", amount=400.0)
    assert len(ctx.previous_refunds) == 1
    assert ctx.previous_refunds[0]["order_id"] == "ORD-101"
    assert ctx.previous_refunds[0]["amount"] == 400.0

    # Add second refund
    ctx = context_service.update_context_for_refund(db, ctx, order_id="ORD-202", amount=350.0)
    assert len(ctx.previous_refunds) == 2

    # Verify reloaded
    reloaded = context_service.load_context(db, conversation_id=conv_id)
    assert len(reloaded.previous_refunds) == 2

def test_duplicate_refund_policy_blocked(db):
    """Policy DUPLICATE_REFUND_001 blocks second refund for the same order."""
    conv_id = "CONV-CTX-DUP-REFUND"
    ctx = context_service.load_context(db, conversation_id=conv_id, customer_id="CUST-10")
    ctx = context_service.update_context_for_refund(db, ctx, order_id="ORD-101", amount=400.0)

    proposed_act = ProposedAction(
        tool_name="issue_refund",
        arguments={"order_id": "ORD-101", "amount": 400.0}
    )

    decision = policy_engine.evaluate(
        customer_message="Please refund ORD-101 again",
        agent_a_response="I can process a refund for ORD-101.",
        proposed_action=proposed_act,
        context=ctx.model_dump()
    )

    assert decision.decision == "BLOCK"
    assert decision.policy_id == "DUPLICATE_REFUND_001"
    assert "already issued" in decision.reason.lower()

def test_duplicate_refund_allowed_for_different_order(db):
    """Refund is allowed for a different order not yet in previous_refunds."""
    conv_id = "CONV-CTX-DIFF-ORDER"
    ctx = context_service.load_context(db, conversation_id=conv_id, customer_id="CUST-10")
    ctx = context_service.set_verification(db, ctx, is_verified=True)
    ctx = context_service.update_context_for_refund(db, ctx, order_id="ORD-101", amount=400.0)

    proposed_act = ProposedAction(
        tool_name="issue_refund",
        arguments={"order_id": "ORD-202", "amount": 400.0}
    )

    decision = policy_engine.evaluate(
        customer_message="Please refund ORD-202",
        agent_a_response="I can process a refund for ORD-202.",
        proposed_action=proposed_act,
        context=ctx.model_dump()
    )

    assert decision.decision == "ALLOW"
    assert decision.policy_id == "REFUND_LIMIT_001"

def test_repeated_complaint_escalation(db):
    """Policy REPEATED_COMPLAINT_001 escalates when complaint count reaches threshold."""
    conv_id = "CONV-CTX-COMPLAINTS"
    ctx = context_service.load_context(db, conversation_id=conv_id, customer_id="CUST-10")
    
    # 2 prior complaints recorded
    ctx = context_service.increment_complaints(db, ctx, count=2)
    assert ctx.complaint_count == 2

    # Third complaint incoming
    decision = policy_engine.evaluate(
        customer_message="This is my third issue with this broken product, terrible service!",
        agent_a_response="I am sorry for the trouble.",
        proposed_action=None,
        context=ctx.model_dump()
    )

    assert decision.decision == "ESCALATE"
    assert decision.policy_id == "REPEATED_COMPLAINT_001"
    assert decision.requires_human_review is True

def test_multi_turn_chat_api_workflow(client):
    """End-to-end multi-turn chat turns via /api/chat testing context updates and duplicate prevention."""
    conv_id = "CONV-MULTI-TURN-E2E"
    
    # Turn 1: Verified customer asks for ₹400 refund on ORD-101 (Should ALLOW and execute)
    payload_1 = {
        "customer_message": "Please refund ₹400 for order ORD-101.",
        "customer_id": "CUST-E2E",
        "conversation_id": conv_id,
        "is_verified": True,
        "manager_approved": False,
    }
    r1 = client.post("/api/chat", json=payload_1)
    assert r1.status_code == 200
    data1 = r1.json()
    assert data1["decision"] == "ALLOW"
    assert data1["tool_executed"] is True
    assert data1["context"] is not None
    assert len(data1["context"]["previous_refunds"]) == 1
    assert data1["context"]["previous_refunds"][0]["order_id"] == "ORD-101"

    # Turn 2: Same customer in same conversation asks for duplicate refund on ORD-101 (Should BLOCK via DUPLICATE_REFUND_001)
    payload_2 = {
        "customer_message": "Please refund ₹400 for order ORD-101.",
        "customer_id": "CUST-E2E",
        "conversation_id": conv_id,
        "is_verified": False,  # Verification should be preserved from turn 1
        "manager_approved": False,
    }
    r2 = client.post("/api/chat", json=payload_2)
    assert r2.status_code == 200
    data2 = r2.json()
    assert data2["decision"] == "BLOCK"
    assert data2["policy_id"] == "DUPLICATE_REFUND_001"
    assert data2["tool_executed"] is False
    assert data2["corrected_response"] is not None
    assert "already been issued" in data2["final_response"].lower()
