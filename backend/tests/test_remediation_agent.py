import pytest
from app.agents.remediation import (
    remediate_response_template,
    remediate_response,
    REMEDIATION_TEMPLATES,
)
from app.graph.workflow import policy_graph

def test_remediation_templates_for_all_policies():
    """Verify templates exist and format properly for all policies."""
    policies = [
        "REFUND_LIMIT_001",
        "CUSTOMER_VERIFICATION_001",
        "DELIVERY_VERIFICATION_001",
        "PII_PROTECTION_001",
        "HIGH_RISK_ESCALATION_001",
        "DUPLICATE_REFUND_001",
        "REPEATED_COMPLAINT_001",
    ]

    for pol in policies:
        corrected = remediate_response_template(
            policy_id=pol,
            original_response="Raw unsafe response",
            context={"approval_limit": 500}
        )
        assert corrected is not None
        assert len(corrected) > 10
        assert "₹500" in corrected if pol == "REFUND_LIMIT_001" else True

def test_remediate_response_wrapper():
    """Test remediate_response wrapper returns corrected string and TEMPLATE type."""
    policy_dec = {
        "decision": "BLOCK",
        "policy_id": "REFUND_LIMIT_001",
        "reason": "Exceeds limit",
        "evidence": {"approval_limit": 500}
    }
    corrected, rem_type = remediate_response(
        policy_decision=policy_dec,
        original_response="I will give you ₹3000 right now.",
        context={"approval_limit": 500}
    )
    assert rem_type == "TEMPLATE"
    assert "above ₹500" in corrected
    assert "approval from our support team" in corrected

def test_workflow_remediation_on_blocked_refund():
    """LangGraph workflow routes blocked refund through remediation_agent node."""
    initial_state = {
        "request_id": "REQ-REM-TEST-01",
        "conversation_id": "CONV-REM-TEST-01",
        "customer_id": "CUST-10",
        "customer_message": "I want a refund of ₹3,000 for ORD-101",
        "conversation_context": {
            "is_verified": True,
            "manager_approved": False,
        },
        "agent_b_called": False,
        "tool_executed": False,
    }

    final_state = policy_graph.invoke(initial_state)

    assert final_state["policy_decision"]["decision"] == "BLOCK"
    assert final_state["tool_executed"] is False
    assert final_state.get("original_response") is not None
    assert final_state.get("corrected_response") is not None
    assert final_state.get("remediation_type") in ("TEMPLATE", "LLM")
    assert "approval" in final_state["final_response"].lower()

def test_workflow_remediation_on_unverified_delivery_promise():
    """LangGraph workflow routes unverified delivery promise to MODIFY and remediates response."""
    initial_state = {
        "request_id": "REQ-REM-TEST-02",
        "conversation_id": "CONV-REM-TEST-02",
        "customer_id": "CUST-10",
        "customer_message": "When will my package arrive?",
        "conversation_context": {
            "is_verified": True,
            "verified_delivery_date": None,
        },
        "agent_b_called": False,
        "tool_executed": False,
    }

    final_state = policy_graph.invoke(initial_state)

    assert final_state["policy_decision"]["decision"] == "MODIFY"
    assert final_state.get("corrected_response") is not None
    assert final_state.get("remediation_type") == "TEMPLATE"
    assert "verified delivery date" in final_state["final_response"].lower()
