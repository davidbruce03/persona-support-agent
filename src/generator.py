"""
generator.py
------------
Persona-Adaptive Response Generator

Compiles a custom system prompt based on the detected customer persona,
injects retrieved knowledge base context, and calls Google Gemini to
generate a grounded, persona-appropriate support response.

The three persona prompt templates ensure:
  - Technical Expert   : Precise, structured, code-friendly responses
  - Frustrated User    : Empathetic, simple, reassuring, action-oriented
  - Business Executive : Concise, impact-focused, timeline-driven
"""

import os
from google import genai
from google.genai import types

from src.config import (
    GEMINI_API_KEY, LLM_MODEL,
    GENERATION_TEMPERATURE,
    CONFIDENCE_THRESHOLD
)
from src.escalator import should_escalate, generate_handoff_summary


# ── Persona System Prompt Templates ──────────────────────────────────────────

PERSONA_PROMPTS = {
    "Technical Expert": (
        "You are a Senior Systems Engineer and Technical Support Specialist with deep expertise "
        "in APIs, authentication, databases, and cloud infrastructure.\n\n"
        "Your communication style:\n"
        "- Lead with a precise root-cause analysis when applicable\n"
        "- Use technical terminology accurately and without over-explanation\n"
        "- Provide exact code snippets, configuration parameters, or command-line instructions\n"
        "- Structure your response with clear sections (e.g., Diagnosis, Steps, Verification)\n"
        "- Reference specific error codes, HTTP status codes, or log patterns where relevant\n"
        "- End with a verification step the engineer can run to confirm the fix"
    ),

    "Frustrated User": (
        "You are a compassionate and patient Customer Care Specialist who specializes in "
        "turning negative experiences into positive resolutions.\n\n"
        "Your communication style:\n"
        "- ALWAYS begin with genuine empathy: acknowledge their frustration before anything else\n"
        "- Use simple, everyday language — avoid technical jargon entirely\n"
        "- Break solutions into short, numbered steps (no more than 5-6 steps)\n"
        "- Be reassuring and positive: 'You are almost there', 'This is an easy fix'\n"
        "- Never blame the customer or imply they made a mistake\n"
        "- End with a warm closing that invites them to ask for more help if needed\n"
        "- Use contractions and conversational language to feel human and approachable"
    ),

    "Business Executive": (
        "You are a Client Relations Director communicating with a senior business stakeholder.\n\n"
        "Your communication style:\n"
        "- Lead with the direct answer or resolution status — no preamble\n"
        "- Include a clear timeline or ETA for full resolution\n"
        "- Quantify the business impact where possible (e.g., 'affecting <X%% of API calls')\n"
        "- Keep the response under 150 words unless technical detail is explicitly requested\n"
        "- Use professional, formal language with zero technical jargon\n"
        "- End with next steps and an escalation path if needed\n"
        "- Structure: [Current Status] → [Impact Assessment] → [Resolution Timeline] → [Next Steps]"
    )
}


def build_system_prompt(persona: str, context_chunks: list[dict]) -> str:
    """
    Assemble the complete system prompt by combining:
      1. The persona-specific communication instructions
      2. The retrieved knowledge base context (grounding)
      3. Critical anti-hallucination rules

    Args:
        persona        : Classified persona label
        context_chunks : Top-K retrieved knowledge base chunks

    Returns:
        Complete system prompt string for the LLM
    """
    persona_instructions = PERSONA_PROMPTS.get(persona, PERSONA_PROMPTS["Frustrated User"])

    # Format context chunks with their source labels
    context_sections = []
    for i, chunk in enumerate(context_chunks, 1):
        source_label = chunk.get("source", "unknown")
        score = chunk.get("score", 0.0)
        context_sections.append(
            f"[Context {i} | Source: {source_label} | Relevance: {score:.0%}]\n"
            f"{chunk['text']}"
        )
    formatted_context = "\n\n---\n\n".join(context_sections)

    full_prompt = (
        f"{persona_instructions}\n\n"
        "════════════════════════════════════════\n"
        "CRITICAL RULES — MUST FOLLOW:\n"
        "════════════════════════════════════════\n"
        "1. Base your response EXCLUSIVELY on the FACTUAL CONTEXT DOCUMENTS provided below.\n"
        "2. Do NOT invent, assume, or hallucinate facts, URLs, email addresses, or phone numbers "
        "   that are not explicitly stated in the provided context.\n"
        "3. If the context does not contain enough information to fully answer the question, "
        "   say so honestly and invite the customer to contact human support.\n"
        "4. Never contradict information found in the context documents.\n"
        "════════════════════════════════════════\n\n"
        "FACTUAL CONTEXT DOCUMENTS:\n"
        "────────────────────────────\n"
        f"{formatted_context}\n"
        "────────────────────────────\n"
    )

    return full_prompt


def generate_adaptive_response(
    user_query: str,
    persona: str,
    context_chunks: list[dict],
    conversation_history: list[dict]
) -> dict:
    """
    Main response generation function.

    Orchestrates the complete pipeline:
      1. Check escalation conditions
      2. Build persona-specific system prompt with context
      3. Call Gemini to generate the response
      4. Return structured result dict

    Args:
        user_query           : Current user message
        persona              : Classified persona
        context_chunks       : Retrieved knowledge base chunks
        conversation_history : Previous conversation turns for escalation check

    Returns:
        dict with keys:
            - escalated        (bool)    : Whether escalation was triggered
            - persona          (str)     : The detected persona
            - response         (str)     : Generated text response (or escalation message)
            - sources_used     (list)    : Source document names used
            - confidence_score (float)   : Best retrieval confidence
            - escalation_reason(str)     : Reason for escalation (if applicable)
            - handoff_summary  (str|None): JSON handoff report (if escalated)
    """
    # ── Step 1: Escalation Check ──────────────────────────────────────────────
    escalate, escalation_reason = should_escalate(
        user_query, persona, context_chunks, conversation_history
    )

    best_score = max((c["score"] for c in context_chunks), default=0.0)
    sources_used = list({c["source"] for c in context_chunks})

    if escalate:
        handoff_json = generate_handoff_summary(
            user_query, persona, context_chunks, conversation_history, escalation_reason
        )
        return {
            "escalated": True,
            "persona": persona,
            "response": (
                "I sincerely apologize, but I want to make sure you get the best possible help. "
                "I'm connecting you with a member of our specialist human support team who can "
                "resolve this directly. They'll have full context of our conversation so you "
                "won't need to repeat yourself."
            ),
            "sources_used": sources_used,
            "confidence_score": best_score,
            "escalation_reason": escalation_reason,
            "handoff_summary": handoff_json
        }

    # ── Step 2: Build persona-adaptive system prompt ──────────────────────────
    system_prompt = build_system_prompt(persona, context_chunks)

    # ── Step 3: Build conversation messages for multi-turn context ────────────
    messages = []

    # Include recent conversation history for context (last 6 turns)
    recent_history = conversation_history[-6:] if conversation_history else []
    for turn in recent_history:
        if turn.get("role") and turn.get("content"):
            messages.append({
                "role": turn["role"],
                "parts": [{"text": turn["content"]}]
            })

    # Add the current user query
    messages.append({
        "role": "user",
        "parts": [{"text": user_query}]
    })

    # ── Step 4: Generate response with Gemini ─────────────────────────────────
    client = genai.Client(api_key=GEMINI_API_KEY)

    response = client.models.generate_content(
        model=LLM_MODEL,
        contents=messages,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=GENERATION_TEMPERATURE
        )
    )

    return {
        "escalated": False,
        "persona": persona,
        "response": response.text,
        "sources_used": sources_used,
        "confidence_score": best_score,
        "escalation_reason": "none",
        "handoff_summary": None
    }


# ── Quick test when running directly ─────────────────────────────────────────
if __name__ == "__main__":
    # Mock data for testing without a full pipeline
    mock_chunks = [
        {
            "text": "To reset your password, go to app.example.com/login and click 'Forgot Password?'. Enter your email and follow the instructions.",
            "source": "password_reset_guide.pdf",
            "score": 0.82
        }
    ]

    test_cases = [
        ("I keep getting a 401 error on my API calls. My Bearer token is set correctly.", "Technical Expert"),
        ("I just can't log in!! I've tried everything and it's not working at all!!", "Frustrated User"),
        ("What is the resolution time for the authentication issues our team is facing?", "Business Executive")
    ]

    for query, persona in test_cases:
        print(f"\n{'='*60}")
        print(f"👤 Persona : {persona}")
        print(f"❓ Query   : {query[:60]}...")
        result = generate_adaptive_response(query, persona, mock_chunks, [])
        print(f"🤖 Response: {result['response'][:200]}...")
        print(f"📊 Score   : {result['confidence_score']:.2f} | Escalated: {result['escalated']}")
