"""
config.py
---------
Central configuration file for the Persona-Adaptive Support Agent.
All thresholds, model names, and tunable parameters live here.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── API Keys ────────────────────────────────────────────────────────────────
GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "")

# ── Model Names ──────────────────────────────────────────────────────────────
LLM_MODEL: str = "gemini-2.5-flash"          # Main generation model
EMBED_MODEL: str = "gemini-embedding-001"     # Embedding model

# ── RAG Pipeline Settings ────────────────────────────────────────────────────
CHUNK_SIZE: int = 500          # Characters per chunk
CHUNK_OVERLAP: int = 50        # Overlap between adjacent chunks
TOP_K_RESULTS: int = 3         # Number of top chunks to retrieve

# ── Vector Database ──────────────────────────────────────────────────────────
FAISS_INDEX_DIR: str = "./faiss_index"

# ── Data Directory ────────────────────────────────────────────────────────────
DATA_DIR: str = "./data"

# ── Escalation Thresholds ────────────────────────────────────────────────────
# Cosine similarity score below this triggers escalation
CONFIDENCE_THRESHOLD: float = 0.40

# Keywords that always trigger escalation regardless of confidence
SENSITIVE_KEYWORDS: list[str] = [
    "refund", "chargeback", "legal", "lawyer", "lawsuit",
    "fraud", "scam", "stolen", "hack", "breach",
    "delete my account", "gdpr", "data deletion",
    "billing dispute", "duplicate charge"
]

# Number of consecutive frustrated messages before auto-escalation
FRUSTRATION_TURN_LIMIT: int = 3

# ── Persona Labels ────────────────────────────────────────────────────────────
PERSONAS: list[str] = [
    "Technical Expert",
    "Frustrated User",
    "Business Executive"
]

# ── Generation Settings ───────────────────────────────────────────────────────
GENERATION_TEMPERATURE: float = 0.2    # Low temperature for factual grounding
CLASSIFICATION_TEMPERATURE: float = 0.1  # Very low for consistent classification
