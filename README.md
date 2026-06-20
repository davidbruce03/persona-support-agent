# 🤖 Persona-Adaptive Customer Support Agent

An intelligent AI-powered customer support agent that automatically detects the type of customer (persona) and adapts its response tone, style, and depth accordingly — built with Google Gemini, ChromaDB, LangChain, and Streamlit.

---

## 🎯 Project Overview

Traditional support bots give the same robotic response to every user. This system is different.

When a message arrives, the agent:
1. **Classifies the customer persona** (Technical Expert / Frustrated User / Business Executive)
2. **Retrieves relevant knowledge** from a local document database using semantic search (RAG)
3. **Generates a persona-appropriate response** — code-heavy for engineers, empathetic for frustrated users, concise for executives
4. **Escalates to a human agent** when it cannot confidently resolve the issue

---

## 🏗️ Architecture Diagram

```
[User Message]
      │
      ▼
[Persona Classifier] ──► Gemini (structured JSON output)
      │                        │
      │              ┌─────────┘
      │         Persona Tag:
      │    Tech Expert / Frustrated / Executive
      │
      ▼
[RAG Pipeline]
  ├── text-embedding-004 (embed query)
  ├── ChromaDB (cosine similarity search)
  └── Top-K Chunks (with confidence scores)
      │
      ▼
[Escalation Check]
  ├── Confidence < 0.40? → ESCALATE
  ├── Sensitive keywords? → ESCALATE
  └── Repeated frustration? → ESCALATE
      │                    │
  (Pass)               (Trigger)
      │                    │
      ▼                    ▼
[Adaptive Generator]   [Handoff JSON]
  └── Persona prompt       └── Structured report
  └── Context injection         for human agent
  └── Gemini response
      │
      ▼
[Streamlit Chat UI]
```

---

## 🧩 Tech Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Language | Python | 3.11+ |
| LLM | Google Gemini 2.5 Flash | `gemini-2.5-flash` |
| Embeddings | Gemini Embeddings | `text-embedding-004` |
| Vector DB | ChromaDB | ≥0.4.0 |
| RAG Framework | LangChain | ≥0.1.0 |
| PDF Parsing | pypdf | ≥3.0.0 |
| UI | Streamlit | ≥1.30.0 |
| Env Management | python-dotenv | ≥1.0.0 |

---

## 📁 Project Structure

```
persona-support-agent/
│
├── data/                           ← Knowledge base documents
│   ├── api_troubleshooting.md      ← API error codes, auth, webhooks
│   ├── billing_policy.txt          ← Refund, subscription, billing policy
│   ├── account_management.md       ← Roles, MFA, SSO, data privacy
│   ├── onboarding_faq.md           ← Getting started, FAQ
│   ├── performance_sla.md          ← Uptime SLAs, incident response
│   └── password_reset_guide.pdf    ← Password & account recovery (PDF)
│
├── src/
│   ├── __init__.py
│   ├── config.py                   ← All tunable settings and thresholds
│   ├── classifier.py               ← Persona detection using Gemini
│   ├── rag_pipeline.py             ← Document ingestion + semantic retrieval
│   ├── generator.py                ← Adaptive prompt engine + LLM caller
│   └── escalator.py                ← Escalation logic + handoff JSON
│
├── app.py                          ← Streamlit chat UI (main entry point)
├── requirements.txt
├── .env.example                    ← Template for environment variables
└── README.md
```

---

## 🚀 Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/persona-support-agent.git
cd persona-support-agent
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure API Key
```bash
cp .env.example .env
# Edit .env and add your Gemini API key:
# GEMINI_API_KEY="your_actual_key_here"
```

Get a free Gemini API key at: https://aistudio.google.com/app/apikey

### 5. Run the Application
```bash
streamlit run app.py
```

### 6. Load the Knowledge Base
- Click **"Load / Refresh Knowledge Base"** in the sidebar
- Wait for document ingestion to complete (~30 seconds)
- Start chatting!

---

## 🔑 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | ✅ Yes | Your Google Gemini API key |

---

## 👤 Persona Detection Strategy

### Method: Gemini Structured Output Classification

The classifier sends the user's message to Gemini with a carefully engineered system prompt that describes the characteristics of each persona. Gemini returns a strict JSON response:

```json
{
  "persona": "Technical Expert",
  "confidence": 0.94,
  "reasoning": "User mentions OAuth 2.0, Bearer tokens, and HTTP 401 codes"
}
```

### Prompt Design
The system prompt lists concrete signal patterns for each persona:
- **Technical Expert**: API jargon, error codes, configuration requests, debugging language
- **Frustrated User**: Emotional language, exclamation marks, urgency, repeated failures
- **Business Executive**: Outcome focus, ROI language, timeline requests, SLA mentions

### Why Gemini vs. Rules?
Simple keyword rules would misclassify edge cases. Gemini understands semantic nuance — "My account isn't working!!" (frustrated) vs. "Can you clarify the account role structure?" (technical/neutral) even though both mention "account".

---

## 📦 RAG Pipeline Design

### 1. Chunking Strategy
- **Algorithm**: `RecursiveCharacterTextSplitter` (LangChain)
- **Chunk Size**: 500 characters
- **Overlap**: 50 characters
- **Separators**: `\n\n` → `\n` → ` ` → `""` (natural language boundaries first)

This preserves paragraph and sentence integrity, preventing important context (like an API endpoint or step sequence) from being cut mid-thought.

### 2. Embedding Model
- **Model**: `text-embedding-004` (Google Gemini)
- **Dimensions**: 768
- Chosen for its strong semantic understanding and tight integration with Gemini's generation models.

### 3. Vector Database
- **ChromaDB** with persistent local storage (`./chroma_db`)
- Uses **cosine similarity** (`hnsw:space: cosine`)
- Persistent storage prevents re-indexing on every session restart

### 4. Retrieval Strategy
- **K = 3** top chunks retrieved per query
- Confidence score = `1.0 - cosine_distance` (normalized to [0, 1])
- Chunks from multiple documents are merged into a single context block for the LLM

---

## 🚨 Escalation Logic

### Triggers (Configurable in `src/config.py`)

| Trigger | Condition | Default |
|---------|-----------|---------|
| Low confidence | `best_score < CONFIDENCE_THRESHOLD` | 0.40 |
| Sensitive topic | Keyword match (billing, legal, fraud, GDPR…) | See config |
| Repeated frustration | N consecutive "Frustrated User" turns | 3 turns |
| No context found | Empty retrieval results | Always |

### Handoff JSON Structure
```json
{
  "escalation_id": "ESC-20250115-143022",
  "timestamp": "2025-01-15T14:30:22+00:00",
  "customer": {
    "persona": "Frustrated User",
    "sentiment": "Negative / Urgent",
    "priority": "HIGH"
  },
  "issue": {
    "current_message": "I demand a refund for the duplicate charge!",
    "escalation_reason": "sensitive_keywords: ['refund', 'duplicate charge']",
    "retrieval_confidence": 0.38
  },
  "knowledge_base": {
    "documents_consulted": ["billing_policy.txt"],
    "chunks_retrieved": 2,
    "best_match_score": 0.38
  },
  "handoff_notes": {
    "recommended_action": "Review billing records directly.",
    "do_not": "Do not ask customer to repeat information already provided"
  }
}
```

---

## 💬 Example Queries

| # | User Message | Expected Persona | Expected Behavior |
|---|-------------|-----------------|-------------------|
| 1 | "My OAuth Bearer token returns 401. Client credentials look correct." | Technical Expert | Root cause analysis, header format, code snippet |
| 2 | "I've been trying for HOURS and nothing works!! I'm going to cancel!" | Frustrated User | Empathy first, simple numbered steps |
| 3 | "Our uptime dropped to 98.5%%. What SLA credits are we entitled to?" | Business Executive | Direct answer, credit schedule, timeline |
| 4 | "I see a duplicate charge and demand a refund immediately!" | Frustrated User | **Escalation triggered** — billing sensitive keyword |
| 5 | "I lost my MFA device and backup codes. How do I access my account?" | Frustrated User | Step-by-step identity verification process |

---

## ⚠️ Known Limitations

1. **No persistent memory across sessions**: Conversation history resets when the browser tab closes.
2. **English-only**: Persona classification and responses are optimized for English.
3. **PDF text quality**: Scanned PDFs (image-based) will not extract correctly — only text-layer PDFs are supported.
4. **Gemini rate limits**: Free tier has request-per-minute limits; heavy testing may hit rate limits.
5. **Hallucination guard relies on retrieval quality**: If knowledge base documents don't cover a topic, the model may still attempt to answer from training data despite the prompt guardrails.

### Future Improvements
- [ ] Add multi-turn memory with SQLite persistence
- [ ] Implement LangGraph for agentic workflow orchestration
- [ ] Add sentiment analysis scoring overlay
- [ ] Build analytics dashboard for support team
- [ ] Support DOCX documents in addition to TXT/MD/PDF
- [ ] Add human approval workflow for escalated tickets

---

## 🔐 Security Notes

- Never commit your `.env` file (it's in `.gitignore`)
- API keys are loaded via `python-dotenv` — never hardcoded
- The `.env.example` file contains only placeholder values
