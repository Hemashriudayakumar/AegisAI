import re
from typing import Any, Dict, Optional
from app.schemas.chat import PolicyDecision, ProposedAction

def evaluate_high_risk_escalation(
    customer_message: str,
    agent_a_response: str,
    policy_def: Dict[str, Any],
) -> Optional[PolicyDecision]:
    """Policy: HIGH_RISK_ESCALATION_001
    Checks for fraud, legal threats, and severe escalation triggers.
    """
    policy_id = policy_def.get("policy_id", "HIGH_RISK_ESCALATION_001")
    version = policy_def.get("version", "v1.0")
    severity = policy_def.get("severity", "CRITICAL")
    keywords = policy_def.get("parameters", {}).get("escalation_keywords", [
        "fraud", "scam", "lawyer", "legal", "court", "sue", "police", "consumer court", "chargeback threat", "authorities", "stolen"
    ])
    
    combined_text = f"{customer_message} {agent_a_response}".lower()
    matched_keywords = [kw for kw in keywords if re.search(r'\b' + re.escape(kw) + r'\b', combined_text)]
    
    if matched_keywords:
        return PolicyDecision(
            decision="ESCALATE",
            policy_id=policy_id,
            policy_version=version,
            severity=severity,
            reason=f"High-risk triggers detected: {', '.join(matched_keywords)}.",
            evidence={"matched_keywords": matched_keywords, "customer_message": customer_message},
            requires_human_review=True,
            safe_response=policy_def.get("enforcement", {}).get(
                "safe_response",
                "I have escalated your concern immediately to our senior safety and legal compliance team. A supervisor will contact you directly."
            )
        )
    return None


def evaluate_pii_protection(
    customer_message: str,
    agent_a_response: str,
    proposed_action: Optional[ProposedAction],
    policy_def: Dict[str, Any],
) -> Optional[PolicyDecision]:
    """Policy: PII_PROTECTION_001
    Prevents leaking payment cards, unmasked phone numbers, or credentials.
    """
    policy_id = policy_def.get("policy_id", "PII_PROTECTION_001")
    version = policy_def.get("version", "v1.0")
    severity = policy_def.get("severity", "CRITICAL")
    
    # Check credit card pattern
    cc_pattern = r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11}|6(?:011|5[0-9]{2})[0-9]{12})\b'
    # Check unmasked 10-digit / international phone pattern
    phone_pattern = r'\b(?:\+91|0)?[6-9]\d{9}\b'
    
    content_to_check = f"{customer_message} {agent_a_response}"
    if proposed_action:
        content_to_check += f" {str(proposed_action.arguments)}"
        
    cc_matches = re.findall(cc_pattern, content_to_check)
    phone_matches = re.findall(phone_pattern, content_to_check)
    
    if cc_matches or phone_matches:
        evidence = {}
        if cc_matches:
            evidence["detected_credit_cards_count"] = len(cc_matches)
        if phone_matches:
            evidence["detected_phone_numbers_count"] = len(phone_matches)
            
        return PolicyDecision(
            decision="BLOCK",
            policy_id=policy_id,
            policy_version=version,
            severity=severity,
            reason="Response or action arguments contain exposed sensitive PII.",
            evidence=evidence,
            requires_human_review=True,
            safe_response=policy_def.get("enforcement", {}).get(
                "safe_response",
                "For your security, sensitive personal information cannot be shared in this channel."
            )
        )
    return None


def evaluate_customer_verification(
    proposed_action: Optional[ProposedAction],
    is_verified: bool,
    policy_def: Dict[str, Any],
) -> Optional[PolicyDecision]:
    """Policy: CUSTOMER_VERIFICATION_001
    Customer must be verified before sensitive order details or financial actions are accessed.
    """
    policy_id = policy_def.get("policy_id", "CUSTOMER_VERIFICATION_001")
    version = policy_def.get("version", "v1.0")
    severity = policy_def.get("severity", "HIGH")
    
    sensitive_tools = policy_def.get("parameters", {}).get("sensitive_tools", [
        "issue_refund", "cancel_order", "offer_discount", "get_order_status"
    ])
    
    if proposed_action and proposed_action.tool_name in sensitive_tools:
        if not is_verified:
            return PolicyDecision(
                decision="BLOCK",
                policy_id=policy_id,
                policy_version=version,
                severity=severity,
                reason="Customer identity verification required before accessing sensitive operations.",
                evidence={
                    "tool_name": proposed_action.tool_name,
                    "is_verified": False
                },
                requires_human_review=False,
                safe_response=policy_def.get("enforcement", {}).get(
                    "blocked_safe_response",
                    "Please verify your identity with your registered phone number or email before we can access order details or process transactions."
                )
            )
    return None


def evaluate_refund_limit(
    proposed_action: Optional[ProposedAction],
    manager_approved: bool,
    is_verified: bool,
    policy_def: Dict[str, Any],
) -> Optional[PolicyDecision]:
    """Policy: REFUND_LIMIT_001
    Refunds exceeding ₹500 require manager approval.
    """
    policy_id = policy_def.get("policy_id", "REFUND_LIMIT_001")
    version = policy_def.get("version", "v1.0")
    severity = policy_def.get("severity", "HIGH")
    
    if proposed_action and proposed_action.tool_name == "issue_refund":
        amount = float(proposed_action.arguments.get("amount", 0))
        max_auto = float(policy_def.get("parameters", {}).get("max_auto_refund_amount", 500))
        
        if amount > max_auto:
            if not manager_approved:
                return PolicyDecision(
                    decision="BLOCK",
                    policy_id=policy_id,
                    policy_version=version,
                    severity=severity,
                    reason=f"Refund amount of ₹{amount:,.2f} exceeds automatic threshold of ₹{max_auto:,.2f} and lacks manager authorization.",
                    evidence={
                        "refund_amount": amount,
                        "approval_limit": max_auto,
                        "manager_approved": False,
                        "order_id": proposed_action.arguments.get("order_id")
                    },
                    requires_human_review=True,
                    safe_response=policy_def.get("enforcement", {}).get(
                        "blocked_safe_response",
                        "This refund requires approval from our support team."
                    )
                )
            else:
                # Manager approved
                return PolicyDecision(
                    decision="ALLOW",
                    policy_id=policy_id,
                    policy_version=version,
                    severity="LOW",
                    reason=f"Refund of ₹{amount:,.2f} has been authorized by a manager.",
                    evidence={"refund_amount": amount, "manager_approved": True},
                    requires_human_review=False
                )
        else:
            # Under or equal to threshold
            if is_verified:
                return PolicyDecision(
                    decision="ALLOW",
                    policy_id=policy_id,
                    policy_version=version,
                    severity="LOW",
                    reason=f"Refund amount ₹{amount:,.2f} is within automated limit of ₹{max_auto:,.2f} for verified customer.",
                    evidence={"refund_amount": amount, "approval_limit": max_auto, "is_verified": True},
                    requires_human_review=False
                )
    return None


def evaluate_delivery_verification(
    agent_a_response: str,
    context: Dict[str, Any],
    policy_def: Dict[str, Any],
) -> Optional[PolicyDecision]:
    """Policy: DELIVERY_VERIFICATION_001
    Chatbot cannot promise a delivery date without verified order lookup.
    """
    policy_id = policy_def.get("policy_id", "DELIVERY_VERIFICATION_001")
    version = policy_def.get("version", "v1.0")
    severity = policy_def.get("severity", "MEDIUM")
    
    verified_delivery_date = context.get("verified_delivery_date")
    
    date_patterns = [
        r'\b\d{4}-\d{2}-\d{2}\b',
        r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?,?\s*\d{0,4}\b',
        r'\b\d{1,2}(?:st|nd|rd|th)?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\b',
        r'\b(?:tomorrow|by tomorrow|by Friday|by Monday)\b'
    ]
    
    matched_dates = []
    for pattern in date_patterns:
        matches = re.findall(pattern, agent_a_response, re.IGNORECASE)
        matched_dates.extend(matches)
        
    if matched_dates:
        # If there is a verified date and the mentioned date aligns with verified date
        if verified_delivery_date and any(verified_delivery_date.lower() in m.lower() or m.lower() in verified_delivery_date.lower() for m in matched_dates):
            return PolicyDecision(
                decision="ALLOW",
                policy_id=policy_id,
                policy_version=version,
                severity="LOW",
                reason="Delivery date mentioned matches verified order status lookup.",
                evidence={"verified_date": verified_delivery_date, "mentioned_dates": matched_dates},
                requires_human_review=False
            )
        else:
            # Unverified delivery date promise
            return PolicyDecision(
                decision="MODIFY",
                policy_id=policy_id,
                policy_version=version,
                severity=severity,
                reason="Chatbot made a delivery date commitment without verified order status lookup.",
                evidence={"unverified_dates": matched_dates, "verified_date_in_context": verified_delivery_date},
                requires_human_review=False,
                safe_response=policy_def.get("enforcement", {}).get(
                    "remediation_safe_response",
                    "I can check your estimated delivery date once you provide your verified order ID."
                )
            )
    return None
