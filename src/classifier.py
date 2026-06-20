"""
classifier.py
-------------
Persona Detection Module

Analyzes incoming user messages and classifies them into one of three
customer personas using Google Gemini with structured JSON output.

Personas:
  - Technical Expert    : Uses jargon, asks about APIs/configs/logs
  - Frustrated User     : Emotional language, urgency, repeated complaints
  - Business Executive  : Outcome-focused, brief, ROI/timeline concerned
"""

import os
import json
from google import genai
from google.genai import types
from src.config import GEMINI_API_KEY, LLM_MODEL, CLASSIFICATION_TEMPERATURE, PERSONAS


def classify_customer_persona(user_message: str) -> dict:
    """
    Classify the user's message into one of the three target personas.

    Args:
        user_message: The raw text message from the customer.

    Returns:
        dict with keys:
            - persona      (str)   : One of the three persona labels
            - confidence   (float) : 0.0 – 1.0 classification confidence
            - reasoning    (str)   : One-sentence justification
    """
    client = genai.Client(api_key=GEMINI_API_KEY)

    system_instruction = (
        "You are an expert customer persona classification engine trained on thousands "
        "of support conversations. Analyze the sentiment, vocabulary, tone, and intent "
        "of the incoming support message and classify it into EXACTLY ONE of these personas:\n\n"

        "1. 'Technical Expert'\n"
        "   - Uses technical terminology (API, SDK, OAuth, payload, endpoint, etc.)\n"
        "   - Requests logs, configurations, error codes, or debugging information\n"
        "   - Asks step-by-step technical explanations or architecture details\n"
        "   - Example: 'My POST request returns a 422 Unprocessable Entity. The payload schema looks correct. Can you check the field validation rules?'\n\n"

        "2. 'Frustrated User'\n"
        "   - Uses emotional or urgent language ('nothing works', 'this is ridiculous')\n"
        "   - Mentions repeated failed attempts or wasted time\n"
        "   - Uses exclamation marks, capital letters, or expresses desperation\n"
        "   - Example: 'I have been trying for HOURS and nothing works!! I am about to cancel!'\n\n"

        "3. 'Business Executive'\n"
        "   - Focuses on business impact, operational continuity, or financial cost\n"
        "   - Asks about timelines, SLAs, or resolution ETAs\n"
        "   - Prefers concise, outcome-oriented communication\n"
        "   - Example: 'Our service uptime dropped to 98.5%% this month. What is the ETA for resolution?'\n\n"

        "Respond ONLY with a valid JSON object matching the schema provided. "
        "Do NOT include any explanation outside the JSON."
    )

    # Structured response schema — forces Gemini to return valid JSON
    response_schema = {
        "type": "OBJECT",
        "properties": {
            "persona": {
                "type": "STRING",
                "enum": PERSONAS
            },
            "confidence": {
                "type": "NUMBER",
                "description": "A float between 0.0 and 1.0 indicating classification certainty"
            },
            "reasoning": {
                "type": "STRING",
                "description": "One sentence explaining why this persona was chosen"
            }
        },
        "required": ["persona", "confidence", "reasoning"]
    }

    response = client.models.generate_content(
        model=LLM_MODEL,
        contents=user_message,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            response_schema=response_schema,
            temperature=CLASSIFICATION_TEMPERATURE
        )
    )

    result = json.loads(response.text)
    return result


def get_persona_emoji(persona: str) -> str:
    """Return a display emoji for each persona type (used in the UI)."""
    mapping = {
        "Technical Expert":   "🔧",
        "Frustrated User":    "😤",
        "Business Executive": "💼"
    }
    return mapping.get(persona, "👤")


def get_persona_color(persona: str) -> str:
    """Return a hex color for each persona (used in the Streamlit UI)."""
    mapping = {
        "Technical Expert":   "#1E40AF",   # Blue
        "Frustrated User":    "#DC2626",   # Red
        "Business Executive": "#065F46"    # Green
    }
    return mapping.get(persona, "#374151")


# ── Quick test when running this module directly ──────────────────────────────
if __name__ == "__main__":
    test_messages = [
        "My OAuth 2.0 token keeps returning a 401. I'm using the correct client_id and client_secret.",
        "This is absolutely ridiculous! Nothing works and I've wasted the entire day!!",
        "What is the estimated resolution time for the API degradation? This is affecting our SLA."
    ]

    for msg in test_messages:
        print(f"\nMessage: {msg[:60]}...")
        result = classify_customer_persona(msg)
        emoji = get_persona_emoji(result["persona"])
        print(f"  {emoji} Persona    : {result['persona']}")
        print(f"  Confidence  : {result['confidence']:.0%}")
        print(f"  Reasoning   : {result['reasoning']}")
