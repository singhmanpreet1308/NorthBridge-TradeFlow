
"""Chat UI for the NorthBridge TradeFlow AI Operations Assistant.

Run from the Phase 6 folder (prediction API should be running on :8000):
    streamlit run chat_ui.py
"""

import base64
import os
from pathlib import Path

import requests
import streamlit as st

from assistant.llm_client import DEFAULT_MODEL
from assistant.ops_assistant import answer_question, extract_trade_id
from assistant.prediction_client import PREDICTION_API_URL
from assistant.retriever import KnowledgeRetriever


EXAMPLE_QUESTIONS = [
    "Why was T-1001 blocked and what action should be taken?",
    "Is T-1001 eligible for simulated reporting?",
    "How was the T-1001 notional corrected?",
    "Who should a notional mismatch be escalated to?",
]

st.set_page_config(
    page_title="TradeFlow Ops Assistant",
    page_icon="📊",
    layout="centered",
)

BACKGROUND_FILE = Path(__file__).resolve().parent / "assets" / "background.svg"


# 0. Theme: navy trade-operations background with glass chat panels
def apply_theme():
    background = ""
    if BACKGROUND_FILE.is_file():
        encoded = base64.b64encode(BACKGROUND_FILE.read_bytes()).decode()
        background = f'url("data:image/svg+xml;base64,{encoded}")'

    st.markdown(
        f"""
        <style>
        :root {{
            --navy: #071530;
            --panel: rgba(10, 27, 56, 0.72);
            --panel-border: rgba(111, 182, 255, 0.22);
            --accent: #F7931E;
            --accent-soft: rgba(247, 147, 30, 0.16);
            --blue: #4FA3FF;
            --text: #E8F1FF;
            --muted: #9DB4D3;
        }}

        [data-testid="stApp"] {{
            background: {background or "none"} center / cover fixed no-repeat, var(--navy);
            color: var(--text);
        }}
        [data-testid="stHeader"] {{ background: transparent; }}
        [data-testid="stBottom"], [data-testid="stBottom"] > div {{
            background: transparent;
        }}

        /* Sidebar */
        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, rgba(6,18,40,0.95), rgba(9,30,62,0.92));
            border-right: 1px solid var(--panel-border);
        }}
        [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {{
            color: var(--text);
        }}
        [data-testid="stSidebar"] .stButton button {{
            background: rgba(79, 163, 255, 0.08);
            border: 1px solid var(--panel-border);
            color: var(--text);
            text-align: left;
            transition: all 0.15s ease;
        }}
        [data-testid="stSidebar"] .stButton button:hover {{
            border-color: var(--accent);
            background: var(--accent-soft);
            color: #FFFFFF;
        }}

        /* Hero header */
        .hero {{
            background: linear-gradient(135deg, rgba(10,31,64,0.85), rgba(7,21,48,0.65));
            border: 1px solid var(--panel-border);
            border-radius: 18px;
            padding: 22px 26px 18px;
            margin-bottom: 18px;
            backdrop-filter: blur(6px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.35);
        }}
        .hero .eyebrow {{
            color: var(--blue);
            font-size: 0.78rem;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            font-weight: 600;
        }}
        .hero .title {{
            margin: 4px 0 6px;
            font-size: 2.1rem;
            font-weight: 700;
            line-height: 1.2;
            color: #FFFFFF;
        }}
        .hero .title .accent {{ color: var(--accent); }}
        .hero p {{ color: var(--muted); margin: 0 0 14px; font-size: 0.93rem; }}
        .flow {{ display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }}
        .flow .chip {{
            background: rgba(79,163,255,0.12);
            border: 1px solid rgba(79,163,255,0.3);
            color: var(--text);
            border-radius: 999px;
            padding: 3px 11px;
            font-size: 0.76rem;
            white-space: nowrap;
        }}
        .flow .chip.final {{
            background: var(--accent-soft);
            border-color: rgba(247,147,30,0.55);
        }}
        .flow .arrow {{ color: var(--accent); font-size: 0.8rem; }}

        /* Chat bubbles */
        [data-testid="stChatMessage"] {{
            background: var(--panel);
            border: 1px solid var(--panel-border);
            border-radius: 16px;
            padding: 14px 16px;
            backdrop-filter: blur(8px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.25);
        }}
        [data-testid="stChatMessage"] strong {{ color: #FFD29A; }}
        [data-testid="stExpander"] details {{
            background: rgba(5, 14, 31, 0.55);
            border: 1px solid var(--panel-border);
            border-radius: 10px;
        }}

        /* Chat input */
        [data-testid="stChatInput"] {{
            background: rgba(10, 27, 56, 0.9);
            border: 1px solid rgba(247,147,30,0.45);
            border-radius: 14px;
            box-shadow: 0 0 0 4px rgba(247,147,30,0.06);
        }}
        [data-testid="stChatInput"] textarea {{ color: var(--text); }}
        </style>
        """,
        unsafe_allow_html=True,
    )


apply_theme()


# 1. Cached resources and status checks
@st.cache_resource
def get_retriever():
    return KnowledgeRetriever()


@st.cache_data(ttl=30)
def prediction_api_status():
    health_url = PREDICTION_API_URL.rsplit("/", 1)[0] + "/health"
    try:
        response = requests.get(health_url, timeout=3)
        response.raise_for_status()
        return True, response.json().get("model_version", "?")
    except requests.RequestException:
        return False, None


# 2. Sidebar
with st.sidebar:
    st.header("TradeFlow Ops Assistant")
    st.caption(
        "Read-only assistant. Answers are grounded in trade records, "
        "validation history, model risk and cited knowledge notes."
    )

    st.subheader("Status")
    api_ok, model_version = prediction_api_status()
    if api_ok:
        st.success(f"Prediction API online (model {model_version})")
    else:
        st.warning(
            "Prediction API offline - model risk will show as NOT AVAILABLE. "
            "Start it with: uvicorn app.main:app --port 8000"
        )

    if os.getenv("EURI_API_KEY"):
        st.success(f"LLM key loaded ({os.getenv('EURI_MODEL', DEFAULT_MODEL)})")
    else:
        st.error("EURI_API_KEY missing - add it to Phase 6 .env")

    st.subheader("Settings")
    top_k = st.slider("Knowledge notes to retrieve (top_k)", 3, 8, 5)
    show_evidence = st.toggle("Show evidence sent to the LLM", value=False)

    st.subheader("Try asking")
    for example in EXAMPLE_QUESTIONS:
        if st.button(example, use_container_width=True):
            st.session_state.pending_question = example

    if st.button("Clear chat", type="secondary", use_container_width=True):
        st.session_state.messages = []
        st.session_state.last_trade_id = None
        st.rerun()


# 3. Chat state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_trade_id" not in st.session_state:
    st.session_state.last_trade_id = None


def render_details(details):
    """Citations, warnings and evidence under an assistant reply."""
    if not details:
        return

    for warning in details.get("warnings", []):
        st.warning(warning, icon="⚠️")

    risk = details.get("model_risk") or {}
    if risk.get("status") == "available":
        st.caption(
            f"Model risk (separate from validation): score "
            f"{risk['risk_score']:.4f} - {risk['risk_band']} "
            f"(threshold {risk['threshold']}, model {risk['model_version']}, "
            f"scored v{risk['scored_version']})"
        )

    with st.expander(f"Sources ({len(details.get('citations_used', []))} cited)"):
        if details.get("trade_id"):
            st.markdown(f"**Trade:** `{details['trade_id']}`")
        st.markdown("**Cited in answer:**")
        for citation in details.get("citations_used", []) or ["none"]:
            st.markdown(f"- `{citation}`")
        st.markdown("**Knowledge sections retrieved:**")
        for source in details.get("kb_sources", []):
            st.markdown(f"- `{source}`")

    if details.get("evidence_pack") and details.get("show_evidence"):
        with st.expander("Evidence sent to the LLM"):
            st.code(details["evidence_pack"], language="text")


st.markdown(
    """
    <div class="hero">
      <div class="eyebrow">NorthBridge TradeFlow</div>
      <div class="title">AI Operations <span class="accent">Assistant</span></div>
      <p>Ask why a trade was blocked, what procedure applies, or whether it is
         eligible for reporting. Follow-up questions reuse the last trade ID.</p>
      <div class="flow">
        <span class="chip">Trade lookup</span><span class="arrow">&#10140;</span>
        <span class="chip">Validation history</span><span class="arrow">&#10140;</span>
        <span class="chip">ML risk</span><span class="arrow">&#10140;</span>
        <span class="chip">Knowledge notes</span><span class="arrow">&#10140;</span>
        <span class="chip final">Cited answer</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        render_details(message.get("details"))


# 4. Handle a new question (typed or from an example button)
typed = st.chat_input("Ask about a trade, e.g. Why was T-1001 blocked?")
question = typed or st.session_state.pop("pending_question", None)

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    # Follow-ups like "is it eligible for reporting?" keep the last trade
    trade_id = extract_trade_id(question) or st.session_state.last_trade_id

    with st.chat_message("assistant"):
        with st.spinner("Looking up trade, validation history, model risk and knowledge notes..."):
            result = answer_question(
                question,
                trade_id=trade_id,
                retriever=get_retriever(),
                top_k=top_k,
            )

        if result["status"] == "success":
            content = result["answer"]
            if result["trade_id"]:
                st.session_state.last_trade_id = result["trade_id"]
        else:
            content = f"**Assistant error:** {result['message']}"

        details = {**result, "show_evidence": show_evidence}
        st.markdown(content)
        render_details(details)

    st.session_state.messages.append(
        {"role": "assistant", "content": content, "details": details}
    )
