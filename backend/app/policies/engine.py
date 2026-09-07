import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml

from app.schemas.chat import PolicyDecision, ProposedAction
from app.policies.evaluator import (
    evaluate_high_risk_escalation,
    evaluate_repeated_complaint,
    evaluate_pii_protection,
    evaluate_duplicate_refund,
    evaluate_customer_verification,
    evaluate_refund_limit,
    evaluate_delivery_verification,
)

POLICIES_DIR = Path(__file__).parent / "definitions"

class PolicyEngine:
    def __init__(self, definitions_dir: Optional[Path] = None):
        self.definitions_dir = definitions_dir or POLICIES_DIR
        self.policies: Dict[str, Dict[str, Any]] = {}
        self.load_policies()

    def load_policies(self) -> None:
        """Loads YAML policy definitions from disk."""
        self.policies.clear()
        if not self.definitions_dir.exists():
            return
            
        for file_path in self.definitions_dir.glob("*.yaml"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    if data and "policy_id" in data:
                        self.policies[data["policy_id"]] = data
            except Exception as e:
                print(f"Error loading policy {file_path}: {e}")

    def get_policy(self, policy_id: str) -> Optional[Dict[str, Any]]:
        return self.policies.get(policy_id)

    def list_policies(self) -> List[Dict[str, Any]]:
        return list(self.policies.values())

    def evaluate(
        self,
        customer_message: str,
        agent_a_response: str,
        proposed_action: Optional[ProposedAction],
        context: Optional[Dict[str, Any]] = None,
    ) -> PolicyDecision:
        """Evaluates all active policies in strict priority order.
        Returns the highest-priority decision (ESCALATE/BLOCK/MODIFY/ALLOW).
        """
        ctx = context or {}
        is_verified = bool(ctx.get("is_verified", False) or ctx.get("customer_verified", False))
        manager_approved = bool(ctx.get("manager_approved", False))

        # 1. HIGH_RISK_ESCALATION_001
        high_risk_def = self.policies.get("HIGH_RISK_ESCALATION_001", {
            "policy_id": "HIGH_RISK_ESCALATION_001", "version": "v1.0", "severity": "CRITICAL"
        })
        high_risk_dec = evaluate_high_risk_escalation(customer_message, agent_a_response, high_risk_def)
        if high_risk_dec:
            return high_risk_dec

        # 2. REPEATED_COMPLAINT_001 (Multi-turn Context Checking)
        rep_comp_def = self.policies.get("REPEATED_COMPLAINT_001", {
            "policy_id": "REPEATED_COMPLAINT_001", "version": "v1.0", "severity": "HIGH",
            "parameters": {"escalation_complaint_threshold": 3}
        })
        rep_comp_dec = evaluate_repeated_complaint(customer_message, ctx, rep_comp_def)
        if rep_comp_dec:
            return rep_comp_dec

        # 3. PII_PROTECTION_001
        pii_def = self.policies.get("PII_PROTECTION_001", {
            "policy_id": "PII_PROTECTION_001", "version": "v1.0", "severity": "CRITICAL"
        })
        pii_dec = evaluate_pii_protection(customer_message, agent_a_response, proposed_action, pii_def)
        if pii_dec:
            return pii_dec

        # 4. DUPLICATE_REFUND_001 (Multi-turn Context Checking)
        dup_refund_def = self.policies.get("DUPLICATE_REFUND_001", {
            "policy_id": "DUPLICATE_REFUND_001", "version": "v1.0", "severity": "HIGH"
        })
        dup_refund_dec = evaluate_duplicate_refund(proposed_action, ctx, dup_refund_def)
        if dup_refund_dec:
            return dup_refund_dec

        # 5. CUSTOMER_VERIFICATION_001
        cust_ver_def = self.policies.get("CUSTOMER_VERIFICATION_001", {
            "policy_id": "CUSTOMER_VERIFICATION_001", "version": "v1.0", "severity": "HIGH"
        })
        cust_ver_dec = evaluate_customer_verification(proposed_action, is_verified, cust_ver_def)
        if cust_ver_dec:
            return cust_ver_dec

        # 6. REFUND_LIMIT_001
        refund_def = self.policies.get("REFUND_LIMIT_001", {
            "policy_id": "REFUND_LIMIT_001", "version": "v1.0", "severity": "HIGH"
        })
        refund_dec = evaluate_refund_limit(proposed_action, manager_approved, is_verified, refund_def)
        if refund_dec:
            return refund_dec

        # 7. DELIVERY_VERIFICATION_001
        deliv_def = self.policies.get("DELIVERY_VERIFICATION_001", {
            "policy_id": "DELIVERY_VERIFICATION_001", "version": "v1.0", "severity": "MEDIUM"
        })
        deliv_dec = evaluate_delivery_verification(agent_a_response, ctx, deliv_def)
        if deliv_dec:
            return deliv_dec

        # Default ALLOW
        return PolicyDecision(
            decision="ALLOW",
            policy_id="STANDARD_ALLOW_001",
            policy_version="v1.0",
            severity="LOW",
            reason="All policy checks passed successfully.",
            evidence={"checks_performed": ["HIGH_RISK", "REPEATED_COMPLAINT", "PII", "DUPLICATE_REFUND", "VERIFICATION", "REFUND", "DELIVERY"]},
            requires_human_review=False
        )

policy_engine = PolicyEngine()
