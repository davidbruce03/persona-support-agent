"""
app.py
------
Persona-Adaptive Customer Support Agent — Streamlit Web UI

Main entry point for the application. This orchestrates the full pipeline:
  User Message → Persona Classification → RAG Retrieval → Adaptive Generation → Escalation Check

Run with:
    streamlit run app.py
"""

import os
import json
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ── Page Configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Support Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Main app background */
    .stApp { background-color: #0F172A; color: #E2E8F0; }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #1E293B;
        border-right: 1px solid #334155;
    }

    /* Chat message bubbles */
    .user-bubble {
        background: linear-gradient(135deg, #1E40AF, #1D4ED8);
        color: white;
        padding: 14px 18px;
        border-radius: 18px 18px 4px 18px;
        margin: 6px 0;
        max-width: 80%;
        margin-left: auto;
        word-wrap: break-word;
        font-size: 0.95rem;
        line-height: 1.5;
    }

    .assistant-bubble {
        background: #1E293B;
        border: 1px solid #334155;
        color: #E2E8F0;
        padding: 14px 18px;
        border-radius: 18px 18px 18px 4px;
        margin: 6px 0;
        max-width: 85%;
        word-wrap: break-word;
        font-size: 0.95rem;
        line-height: 1.6;
    }

    .escalated-bubble {
        background: #1A0A0A;
        border: 1px solid #DC2626;
        color: #FCA5A5;
        padding: 14px 18px;
        border-radius: 18px 18px 18px 4px;
        margin: 6px 0;
        max-width: 85%;
        font-size: 0.95rem;
    }

    /* Persona badge */
    .persona-badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-bottom: 6px;
    }
    .badge-tech { background: #1E3A8A; color: #BFDBFE; }
    .badge-frus { background: #7F1D1D; color: #FECACA; }
    .badge-exec { background: #064E3B; color: #A7F3D0; }
    .badge-none { background: #374151; color: #D1D5DB; }

    /* Source chip */
    .source-chip {
        display: inline-block;
        background: #0F2040;
        border: 1px solid #1E40AF;
        color: #93C5FD;
        font-size: 0.7rem;
        padding: 2px 8px;
        border-radius: 10px;
        margin: 2px 2px;
    }

    /* Escalation banner */
    .esc-banner {
        background: linear-gradient(135deg, #7F1D1D, #991B1B);
        border: 1px solid #DC2626;
        color: #FEF2F2;
        padding: 10px 15px;
        border-radius: 8px;
        margin: 6px 0;
        font-size: 0.85rem;
    }

    /* Confidence bar wrapper */
    .conf-label { font-size: 0.75rem; color: #94A3B8; margin-top: 4px; }

    /* Input area */
    .stChatInput > div { background: #1E293B !important; }

    /* Metric cards */
    .metric-card {
        background: #1E293B;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 12px;
        text-align: center;
        margin: 4px 0;
    }
    .metric-value { font-size: 1.5rem; font-weight: 700; color: #60A5FA; }
    .metric-label { font-size: 0.75rem; color: #94A3B8; }

    /* Handoff JSON expander */
    .handoff-json {
        background: #0A0F1A;
        border: 1px solid #1E3A8A;
        border-radius: 8px;
        padding: 12px;
        font-family: monospace;
        font-size: 0.8rem;
        color: #7DD3FC;
        white-space: pre-wrap;
    }

    /* Status indicator */
    .status-dot {
        display: inline-block;
        width: 8px; height: 8px;
        border-radius: 50%;
        margin-right: 6px;
    }
    .dot-online { background: #22C55E; }
    .dot-offline { background: #EF4444; }

    /* ── Sidebar text visibility fixes ── */
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] div {
        color: #E2E8F0 !important;
    }

    [data-testid="stSidebar"] .stMarkdown h3 {
        color: #93C5FD !important;
        font-size: 0.85rem !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    [data-testid="stSidebar"] .stMarkdown h2 {
        color: #FFFFFF !important;
    }

    [data-testid="stSidebar"] .stButton button {
        color: #E2E8F0 !important;
        background-color: #334155 !important;
        border: 1px solid #475569 !important;
    }

    [data-testid="stSidebar"] .stButton button:hover {
        background-color: #1E40AF !important;
        border-color: #3B82F6 !important;
    }

    [data-testid="stSidebar"] .stMarkdown p {
        color: #CBD5E1 !important;
    }

    [data-testid="stSidebar"] hr {
        border-color: #334155 !important;
    }

    [data-testid="stSidebar"] .stAlert p {
        color: #1E293B !important;
    }
</style>
""", unsafe_allow_html=True)


# ── Session State Initialization ──────────────────────────────────────────────
def init_session_state():
    """Initialize all session state variables on first load."""
    if "messages" not in st.session_state:
        st.session_state.messages = []          # List of chat turn dicts
    if "rag_pipeline" not in st.session_state:
        st.session_state.rag_pipeline = None    # LocalRAGPipeline instance
    if "kb_loaded" not in st.session_state:
        st.session_state.kb_loaded = False      # Whether KB has been ingested
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []  # For escalation tracking
    if "total_queries" not in st.session_state:
        st.session_state.total_queries = 0
    if "escalation_count" not in st.session_state:
        st.session_state.escalation_count = 0
    if "persona_counts" not in st.session_state:
        st.session_state.persona_counts = {
            "Technical Expert": 0,
            "Frustrated User": 0,
            "Business Executive": 0
        }


init_session_state()


# ── Helper Functions ──────────────────────────────────────────────────────────

def get_persona_badge_class(persona: str) -> str:
    mapping = {
        "Technical Expert": "badge-tech",
        "Frustrated User": "badge-frus",
        "Business Executive": "badge-exec"
    }
    return mapping.get(persona, "badge-none")


def get_persona_emoji(persona: str) -> str:
    mapping = {
        "Technical Expert": "🔧",
        "Frustrated User": "😤",
        "Business Executive": "💼"
    }
    return mapping.get(persona, "👤")


def check_api_key() -> bool:
    """Verify that the Gemini API key is configured."""
    key = os.environ.get("GEMINI_API_KEY","")
    return bool(key and len(key) > 10)


@st.cache_resource(show_spinner=False)
def load_rag_pipeline():
    """
    Load and return the RAG pipeline (cached across Streamlit reruns).
    
    Using @st.cache_resource ensures ChromaDB is only initialized once,
    not on every user interaction rerun.
    """
    from src.rag_pipeline import LocalRAGPipeline
    pipeline = LocalRAGPipeline()
    return pipeline


def process_user_message(user_input: str) -> dict:
    """
    Run the full pipeline for a single user message.

    1. Classify persona
    2. Retrieve relevant knowledge base chunks
    3. Generate adaptive response (with escalation check)

    Returns the full result dict from the generator.
    """
    from src.classifier import classify_customer_persona
    from src.generator import generate_adaptive_response

    pipeline = st.session_state.rag_pipeline

    # Step 1: Classify persona
    classification = classify_customer_persona(user_input)
    persona = classification["persona"]
    confidence = classification["confidence"]
    reasoning = classification["reasoning"]

    # Step 2: Retrieve context
    context_chunks = pipeline.retrieve_context(user_input)

    # Step 3: Generate response (includes escalation logic)
    result = generate_adaptive_response(
        user_query=user_input,
        persona=persona,
        context_chunks=context_chunks,
        conversation_history=st.session_state.conversation_history
    )

    # Enrich result with classification metadata
    result["classification_confidence"] = confidence
    result["classification_reasoning"] = reasoning
    result["context_chunks"] = context_chunks

    return result


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🤖 Support Agent")
    st.markdown("---")

    # API Key status
    api_ok = check_api_key()
    dot_class = "dot-online" if api_ok else "dot-offline"
    status_text = "Gemini API Connected" if api_ok else "API Key Not Set"
    st.markdown(
        f'<div><span class="status-dot {dot_class}"></span>{status_text}</div>',
        unsafe_allow_html=True
    )

    st.markdown("---")

    # Knowledge Base Management
    st.markdown("### 📚 Knowledge Base")

    if not api_ok:
        st.warning("Set GEMINI_API_KEY in .env to enable the agent.")
    else:
        if st.button("🔄 Load / Refresh Knowledge Base", use_container_width=True):
            with st.spinner("Loading pipeline and ingesting documents..."):
                pipeline = load_rag_pipeline()
                st.session_state.rag_pipeline = pipeline
                stats = pipeline.get_collection_stats()

                if stats["total_chunks"] == 0:
                    pipeline.ingest_all_documents()
                    stats = pipeline.get_collection_stats()

                st.session_state.kb_loaded = True
                st.success(f"✅ {stats['total_chunks']} chunks indexed")

        if st.session_state.kb_loaded and st.session_state.rag_pipeline:
            stats = st.session_state.rag_pipeline.get_collection_stats()
            st.markdown(
                f'<div class="metric-card">'
                f'<div class="metric-value">{stats["total_chunks"]}</div>'
                f'<div class="metric-label">Indexed Chunks</div>'
                f'</div>',
                unsafe_allow_html=True
            )

    st.markdown("---")

    # Session Analytics
    st.markdown("### 📊 Session Analytics")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(
            f'<div class="metric-card">'
            f'<div class="metric-value">{st.session_state.total_queries}</div>'
            f'<div class="metric-label">Queries</div></div>',
            unsafe_allow_html=True
        )
    with col_b:
        st.markdown(
            f'<div class="metric-card">'
            f'<div class="metric-value" style="color:#EF4444">{st.session_state.escalation_count}</div>'
            f'<div class="metric-label">Escalations</div></div>',
            unsafe_allow_html=True
        )

    pc = st.session_state.persona_counts
    total = sum(pc.values()) or 1
    for persona, emoji in [
        ("Technical Expert", "🔧"),
        ("Frustrated User", "😤"),
        ("Business Executive", "💼")
    ]:
        pct = int(pc[persona] / total * 100)
        st.markdown(f"{emoji} **{persona}**: {pc[persona]} ({pct}%)")

    st.markdown("---")

    # Clear conversation
    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.conversation_history = []
        st.session_state.total_queries = 0
        st.session_state.escalation_count = 0
        st.session_state.persona_counts = {k: 0 for k in st.session_state.persona_counts}
        st.rerun()

    st.markdown("---")

    # Quick Test Prompts
    st.markdown("### 💡 Example Queries")
    examples = [
        ("🔧 Tech", "My OAuth 2.0 Bearer token returns 401 Unauthorized. Client credentials are correct. Please review the header parameter requirements."),
        ("😤 Frustrated", "This is unacceptable!! I have been trying to log in for hours and nothing works! I'm about to cancel my subscription!"),
        ("💼 Executive", "Our service uptime dropped to 98.5%% this month. What is the SLA credit we are entitled to and what is the resolution timeline?"),
        ("💳 Billing", "I see a duplicate charge on my account and I demand a refund immediately!"),
        ("🔒 Password", "I lost my MFA device and I don't have my backup codes. How do I recover my account?"),
    ]
    for label, prompt in examples:
        if st.button(label, use_container_width=True, key=f"example_{label}"):
            st.session_state["prefill_prompt"] = prompt
            st.rerun()


# ── Main Chat Area ────────────────────────────────────────────────────────────

st.markdown("# 🤖 Persona-Adaptive Customer Support Agent")
st.markdown(
    "Powered by **Google Gemini** + **ChromaDB RAG** | "
    "Automatically adapts tone for Technical, Frustrated, and Executive customers"
)
st.markdown("---")

# API Key warning if not set
if not api_ok:
    st.error(
        "⚠️ **Gemini API key not configured.**\n\n"
        "1. Copy `.env.example` to `.env`\n"
        "2. Add your key: `GEMINI_API_KEY=your_key_here`\n"
        "3. Restart the app"
    )
    st.stop()

# KB not loaded warning
if not st.session_state.kb_loaded:
    st.info("👈 **Click 'Load / Refresh Knowledge Base'** in the sidebar to start.")

# ── Render Chat History ───────────────────────────────────────────────────────
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f'<div class="user-bubble">{msg["content"]}</div>', unsafe_allow_html=True)
    else:
        # Render persona badge
        persona = msg.get("persona", "")
        if persona:
            badge_class = get_persona_badge_class(persona)
            emoji = get_persona_emoji(persona)
            st.markdown(
                f'<span class="persona-badge {badge_class}">{emoji} {persona}</span>',
                unsafe_allow_html=True
            )

        # Render response bubble
        bubble_class = "escalated-bubble" if msg.get("escalated") else "assistant-bubble"
        st.markdown(
            f'<div class="{bubble_class}">{msg["content"]}</div>',
            unsafe_allow_html=True
        )

        # Show source chips
        sources = msg.get("sources", [])
        if sources:
            chips = "".join(f'<span class="source-chip">📄 {s}</span>' for s in sources)
            conf = msg.get("confidence", 0)
            st.markdown(
                f'<div style="margin-top:4px">{chips}</div>'
                f'<div class="conf-label">Retrieval confidence: {conf:.0%}</div>',
                unsafe_allow_html=True
            )

        # Escalation banner
        if msg.get("escalated"):
            reason = msg.get("escalation_reason", "unknown")
            st.markdown(
                f'<div class="esc-banner">🚨 <strong>Escalated to Human Agent</strong> — Reason: {reason}</div>',
                unsafe_allow_html=True
            )

        # Handoff JSON expander
        if msg.get("handoff_summary"):
            with st.expander("📋 View Human Handoff Report (JSON)"):
                st.markdown(
                    f'<div class="handoff-json">{msg["handoff_summary"]}</div>',
                    unsafe_allow_html=True
                )

        # Classification details expander
        if msg.get("classification_reasoning"):
            with st.expander("🔍 Persona Classification Details"):
                cl_conf = msg.get("classification_confidence", 0)
                st.markdown(f"**Confidence:** {cl_conf:.5%}")
                st.markdown(f"**Reasoning:** {msg['classification_reasoning']}")

    st.markdown("<br>", unsafe_allow_html=True)


# ── Chat Input ────────────────────────────────────────────────────────────────
prefill = st.session_state.pop("prefill_prompt", "")
user_input = st.chat_input(
    "Type your support question here...",
)
# Handle prefill from sidebar buttons
if prefill and not user_input:
    user_input = prefill

if user_input:
    if not st.session_state.kb_loaded or not st.session_state.rag_pipeline:
        st.warning("⚠️ Please load the Knowledge Base first using the sidebar button.")
        st.stop()

    # Add user message to display
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })
    st.session_state.conversation_history.append({
        "role": "user",
        "content": user_input,
        "persona": None
    })

    # Process with full pipeline
    with st.spinner("🔍 Analyzing persona · Retrieving context · Generating response..."):
        try:
            result = process_user_message(user_input)

            persona = result["persona"]
            st.session_state.total_queries += 1
            st.session_state.persona_counts[persona] = (
                st.session_state.persona_counts.get(persona, 0) + 1
            )
            if result["escalated"]:
                st.session_state.escalation_count += 1

            # Store assistant message
            st.session_state.messages.append({
                "role": "assistant",
                "content": result["response"],
                "persona": persona,
                "escalated": result["escalated"],
                "escalation_reason": result.get("escalation_reason", ""),
                "sources": result.get("sources_used", []),
                "confidence": result.get("confidence_score", 0.0),
                "handoff_summary": result.get("handoff_summary"),
                "classification_confidence": result.get("classification_confidence", 0),
                "classification_reasoning": result.get("classification_reasoning", "")
            })

            # Update conversation history for escalation tracking
            st.session_state.conversation_history.append({
                "role": "assistant",
                "content": result["response"],
                "persona": persona
            })

        except Exception as e:
            st.error(f"❌ Pipeline error: {str(e)}")
            st.info("Check your API key and ensure the knowledge base is loaded.")

    st.rerun()
