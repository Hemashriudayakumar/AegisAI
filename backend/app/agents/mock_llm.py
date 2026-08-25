import json
import re
from typing import Any, Dict, Optional

class MockLLMProvider:
    """Mock LLM Provider that deterministic generates Agent A JSON outputs
    matching expected Qwen3-8B customer support agent behavior.
    """
    def generate(self, customer_message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        msg_lower = customer_message.lower()
        
        # 1. High risk / legal / fraud
        if any(w in msg_lower for w in ["fraud", "scam", "lawyer", "legal", "sue", "police", "court"]):
            return {
                "response": "I understand your serious concern regarding this matter. I am escalating this to our senior management.",
                "proposed_action": {
                    "tool_name": "escalate_to_human",
                    "arguments": {
                        "conversation_id": (context or {}).get("conversation_id", "CONV-101"),
                        "reason": "Customer reported fraud or legal complaint."
                    }
                }
            }
            
        # 2. Refund request - amount extraction
        refund_match = re.search(r'(?:refund|money back|return)[^\d]*(?:₹|rs\.?|inr)?\s*([\d,]+)', msg_lower)
        if "refund" in msg_lower:
            amount = 3000
            if refund_match:
                try:
                    amount = float(refund_match.group(1).replace(",", ""))
                except Exception:
                    amount = 3000
            elif "400" in msg_lower:
                amount = 400
            elif "3000" in msg_lower or "3,000" in msg_lower:
                amount = 3000
                
            order_id = "ORD-101"
            ord_match = re.search(r'\b(ord-\d+)\b', msg_lower)
            if ord_match:
                order_id = ord_match.group(1).upper()
                
            return {
                "response": f"I can certainly help you process a refund of ₹{int(amount)} for order {order_id}.",
                "proposed_action": {
                    "tool_name": "issue_refund",
                    "arguments": {
                        "order_id": order_id,
                        "amount": amount
                    }
                }
            }
            
        # 3. Order status lookup
        if any(w in msg_lower for w in ["status", "where is my order", "track", "order status"]):
            order_id = "ORD-101"
            ord_match = re.search(r'\b(ord-\d+)\b', msg_lower)
            if ord_match:
                order_id = ord_match.group(1).upper()
            return {
                "response": f"Let me check the status for order {order_id}.",
                "proposed_action": {
                    "tool_name": "get_order_status",
                    "arguments": {
                        "order_id": order_id
                    }
                }
            }
            
        # 4. Delivery date inquiry / promise
        if any(w in msg_lower for w in ["when will", "delivery date", "deliver", "arrive"]):
            # If context has verified delivery date
            if context and context.get("verified_delivery_date"):
                v_date = context["verified_delivery_date"]
                return {
                    "response": f"Based on verified tracking information, your package is scheduled to arrive on {v_date}.",
                    "proposed_action": None
                }
            else:
                # Agent A improperly promises an unverified date
                return {
                    "response": "Your package will arrive on August 28 guaranteed.",
                    "proposed_action": None
                }
                
        # 5. Cancellation
        if "cancel" in msg_lower:
            order_id = "ORD-101"
            ord_match = re.search(r'\b(ord-\d+)\b', msg_lower)
            if ord_match:
                order_id = ord_match.group(1).upper()
            return {
                "response": f"I will submit a cancellation request for order {order_id}.",
                "proposed_action": {
                    "tool_name": "cancel_order",
                    "arguments": {
                        "order_id": order_id,
                        "reason": "Customer cancellation request"
                    }
                }
            }
            
        # 6. Discount / Coupon
        if any(w in msg_lower for w in ["discount", "coupon", "offer"]):
            return {
                "response": "I can offer you a courtesy promotional discount of ₹50 on your order.",
                "proposed_action": {
                    "tool_name": "offer_discount",
                    "arguments": {
                        "order_id": "ORD-101",
                        "amount": 50
                    }
                }
            }
            
        # 7. Default general greeting / inquiry
        return {
            "response": "Hello! Welcome to Customer Support. How may I assist you with your orders or account today?",
            "proposed_action": None
        }

mock_llm_provider = MockLLMProvider()
