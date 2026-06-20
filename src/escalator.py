"""
escalator.py
------------
Escalation Decision Engine

Determines whether a customer conversation should be escalated to a human
support agent, and generates a structured handoff JSON report when triggered.

Escalation Triggers:
  1. Low Retrieval Confidence  : Best chunk score < CONFIDENCE_THRESHOLD (0.40)
  2. Sensitive Keywords        : Billing disputes, legal threats, fraud, GDPR requests
  3. Repeated Frustration      : Frustrated User persona across N consecutive turns
  4. No Context Found          : Empty retrieval results
"""

import json
from datetime import datetime, timezone

from src.config import (
    CONFIDENCE_THRESHOLD,
    SENSITIVE_KEYWORDS,
    FRUSTRATION_TURN_LIMIT
)


def check_sensitive_keywords(user_message: str) -> tuple[bool, list[str]]:
    """
    Check if the user's message contains any sensitive escalation keywords.

    Args:
        user_message: Raw text from the customer

    Returns:
        (triggered: bool, matched_keywords: list[str])
    """
    message_lower = user_message.lower()
    matched = [kw for kw in SENSITIVE_KEYWORDS if kw in message_lower]
    return (len(matched) > 0, matched)


def count_consecutive_frustration(conversation_history: list[dict]) -> int:
    """
    Count how many consecutive recent turns have been classified as 'Frustrated User'.

    Args:
        conversation_history: List of turn dicts, each with 'persona' key

    Returns:
        Number of consecutive frustrated turns from the most recent message backwards
    """
    count = 0
    for turn in reversed(conversation_history):
        if turn.get("persona") == "Frustrated User":
            count += 1
        else:
            break
    return count


def should_escalate(
    user_message: str,
    persona: str,
    context_chunks: list[dict],
    conversation_history: list[dict]
) -> tuple[bool, str]:
    """
    Central escalation decision function.

    Evaluates all escalation triggers and returns a decision with reason.

    Args:
        user_message         : Current raw user message
        persona              : Classified persona string
        context_chunks       : Retrieved knowledge base chunks with scores
        conversation_history : List of previous conversation turns

    Returns:
        (escalate: bool, reason: str)
    """
    # Trigger 1: No context found at all
    if not context_chunks:
        return True, "no_context_found"

    # Trigger 2: Low retrieval confidence
    best_score = max(chunk["score"] for chunk in context_chunks)
    if best_score < CONFIDENCE_THRESHOLD:
        return True, f"low_confidence (best score: {best_score:.3f}, threshold: {CONFIDENCE_THRESHOLD})"

    # Trigger 3: Sensitive keyword detected
    is_sensitive, matched_keywords = check_sensitive_keywords(user_message)
    if is_sensitive:
        return True, f"sensitive_keywords: {matched_keywords}"

    # Trigger 4: Repeated frustration across multiple turns
    if persona == "Frustrated User":
        # Add current turn's persona to history for this check
        temp_history = conversation_history + [{"persona": persona}]
        consecutive_count = count_consecutive_frustration(temp_history)
        if consecutive_count >= FRUSTRATION_TURN_LIMIT:
            return True, f"repeated_frustration ({consecutive_count} consecutive turns)"

    return False, "none"


def generate_handoff_summary(
    user_message: str,
    persona: str,
    context_chunks: list[dict],
    conversation_history: list[dict],
    escalation_reason: str
) -> str:
    """
    Generate a structured JSON handoff report for the human support agent.

    This summary contains everything the human agent needs to immediately
    understand the situation and take over without making the customer repeat themselves.

    Args:
        user_message         : The triggering user message
        persona              : Detected customer persona
        context_chunks       : Retrieved knowledge base chunks
        conversation_history : Full conversation history
        escalation_reason    : Why escalation was triggered

    Returns:
        Formatted JSON string
    """
    # Extract the conversation so far
    history_summary = []
    for turn in conversation_history[-10:]:  # Last 10 turns max
        history_summary.append({
            "role": turn.get("role", "unknown"),
            "message": turn.get("content", "")[:200] + ("..." if len(turn.get("content", "")) > 200 else ""),
            "persona": turn.get("persona", "N/A")
        })

    # Collect attempted steps from retrieved documents
    sources_used = list({chunk["source"] for chunk in context_chunks})

    # Determine recommended next action based on escalation reason
    recommended_action = _get_recommendation(escalation_reason, persona)

    handoff = {
        "escalation_id": f"ESC-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "customer": {
            "persona": persona,
            "sentiment": _get_sentiment(persona),
            "priority": _get_priority(persona, escalation_reason)
        },
        "issue": {
            "current_message": user_message[:300],
            "escalation_reason": escalation_reason,
            "retrieval_confidence": max((c["score"] for c in context_chunks), default=0.0)
        },
        "knowledge_base": {
            "documents_consulted": sources_used,
            "chunks_retrieved": len(context_chunks),
            "best_match_score": max((c["score"] for c in context_chunks), default=0.0)
        },
        "conversation_history": history_summary,
        "handoff_notes": {
            "recommended_action": recommended_action,
            "do_not": "Do not ask the customer to repeat information already provided",
            "context": f"Customer has been communicating as a {persona}. Adjust your tone accordingly."
        }
    }

    return json.dumps(handoff, indent=2)


def _get_sentiment(persona: str) -> str:
    """Map persona to a sentiment label for human agent context."""
    mapping = {
        "Frustrated User": "Negative / Urgent",
        "Technical Expert": "Neutral / Analytical",
        "Business Executive": "Professional / Impatient"
    }
    return mapping.get(persona, "Neutral")


def _get_priority(persona: str, reason: str) -> str:
    """Determine ticket priority based on persona and escalation reason."""
    if "sensitive_keywords" in reason or persona == "Business Executive":
        return "HIGH"
    if persona == "Frustrated User" or "low_confidence" in reason:
        return "MEDIUM"
    return "NORMAL"


def _get_recommendation(reason: str, persona: str) -> str:
    """Generate a recommended action string for the human agent."""
    if "sensitive_keywords" in reason:
        return "Review billing records or legal concern directly. Do not attempt automated resolution."
    if "low_confidence" in reason or "no_context_found" in reason:
        return "The AI could not find a relevant answer. Human expertise needed for this query."
    if "repeated_frustration" in reason:
        return "Customer is highly frustrated. Lead with empathy, offer a concrete resolution or compensation."
    return "Review conversation history and provide a direct, personalised resolution."


# ── Quick test when running directly ─────────────────────────────────────────
if __name__ == "__main__":
    test_message = "I have a duplicate charge on my account and I want a refund immediately!"
    test_chunks = [{"source": "billing_policy.txt", "score": 0.35, "text": "Refund policy..."}]
    test_history = [
        {"role": "user", "content": "My account is broken!", "persona": "Frustrated User"},
        {"role": "assistant", "content": "Let me help you...", "persona": None},
        {"role": "user", "content": "It's still not working!", "persona": "Frustrated User"},
    ]

    escalate, reason = should_escalate(test_message, "Frustrated User", test_chunks, test_history)
    print(f"Escalate: {escalate} | Reason: {reason}")

    if escalate:
        summary = generate_handoff_summary(test_message, "Frustrated User", test_chunks, test_history, reason)
        print("\nHandoff JSON:")
        print(summary)
