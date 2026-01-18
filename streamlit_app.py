from typing import List, Dict, Optional
import os
import uuid
import tempfile
import asyncio
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams

from fastembed import TextEmbedding

from agents import Agent, Runner
from openai import AsyncOpenAI

import requests
import nest_asyncio

load_dotenv()
nest_asyncio.apply()


# -----------------------------
# UI THEME + PAGE CONFIG
# -----------------------------
st.set_page_config(
    page_title="Shikhar Traders Voice Agent",
    page_icon="🎙️",
    layout="wide"
)


# -----------------------------
# HELPERS
# -----------------------------
def init_session_state():
    defaults = {
        "setup_complete": False,
        "client": None,
        "embedding_model": None,
        "processor_agent": None,
        "tts_agent": None,
        "selected_voice": "coral",
        "collection_name": "docs_embeddings",
        "chat": [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def premium_css():
    st.markdown(
        """
        <style>
        .stApp {
            background: radial-gradient(circle at top left, #0f172a, #020617);
            color: white;
        }
        .glass-card {
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,255,255,0.12);
            border-radius: 18px;
            padding: 18px;
            box-shadow: 0 12px 40px rgba(0,0,0,0.45);
            backdrop-filter: blur(12px);
        }
        .titleGlow {
            font-size: 40px;
            font-weight: 800;
            letter-spacing: 0.5px;
            background: linear-gradient(90deg, #22c55e, #06b6d4, #a855f7, #ec4899);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: shimmer 4s infinite linear;
        }
        @keyframes shimmer {
            0% { filter: drop-shadow(0 0 2px rgba(34,197,94,0.4)); }
            50% { filter: drop-shadow(0 0 18px rgba(168,85,247,0.7)); }
            100% { filter: drop-shadow(0 0 2px rgba(236,72,153,0.4)); }
        }
        .subText {
            color: rgba(255,255,255,0.7);
            font-size: 14px;
        }
        .chip {
            display: inline-block;
            padding: 6px 10px;
            border-radius: 999px;
            background: rgba(255,255,255,0.08);
            border: 1px solid rgba(255,255,255,0.12);
            margin-right: 8px;
            font-size: 12px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )


def setup_qdrant_collection(qdrant_url: str, qdrant_api_key: str, collection_name: str):
    client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
    embedding_model = TextEmbeddingEmbedding()

    test_embedding = list(embedding_model.embed(["test"]))[0]
    embedding_dim = len(test_embedding)

    try:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=embedding_dim, distance=Distance.COSINE)
        )
    except Exception as e:
        if "already exists" not in str(e).lower():
            raise e

    return client, embedding_model


# FIX: fastembed model wrapper name
class TextEmbeddingWrapper:
    def __init__(self):
        self.model = TextEmbedding()

    def embed(self, texts: List[str]):
        return self.model.embed(texts)


def download_markdown_doc(raw_url: str) -> str:
    """
    Downloads a RAW markdown file and returns text.
    Works perfectly for GitHub raw links.
    """
    r = requests.get(raw_url, timeout=30)
    r.raise_for_status()
    return r.text


def store_embeddings(client: QdrantClient, embedding_model: TextEmbeddingWrapper, text: str, source_url: str, collection_name: str):
    """
    Store ONE big markdown doc as chunks.
    """
    # Basic chunking (safe for Streamlit)
    chunk_size = 1200
    chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

    for idx, chunk in enumerate(chunks):
        embedding = list(embedding_model.embed([chunk]))[0]

        client.upsert(
            collection_name=collection_name,
            points=[
                models.PointStruct(
                    id=str(uuid.uuid4()),
                    vector=embedding.tolist(),
                    payload={
                        "content": chunk,
                        "url": source_url,
                        "title": "Shikhar Traders Support Docs",
                        "chunk_index": idx,
                        "crawl_date": datetime.now().isoformat(),
                    }
                )
            ]
        )


def setup_agents(openai_api_key: str):
    os.environ["OPENAI_API_KEY"] = openai_api_key

    processor_agent = Agent(
        name="Shikhar Traders Support Agent",
        instructions="""
You are a premium customer support assistant for Shikhar Traders (UltraTech only).

Rules:
- Always answer in a friendly tone.
- Give short + clear answers.
- If user asks for payment, booking, delivery, or final price → tell them to confirm via call/WhatsApp/email.
- Use these contacts:
  Call/WhatsApp: 07355969446, 09450805567
  Email: shikhartraders@zohomail.com
- Mention that prices are approximate.
- Support English + Hinglish + Hindi depending on user's style.
""",
        model="gpt-4o"
    )

    tts_agent = Agent(
        name="TTS Speech Styler",
        instructions="""
Convert the answer into natural spoken speech.
Add pauses, emphasis, and speak clearly.
Keep it short and friendly.
""",
        model="gpt-4o-mini"
    )

    return processor_agent, tts_agent


async def process_query(
    query: str,
    client: QdrantClient,
    embedding_model: TextEmbeddingWrapper,
    processor_agent: Agent,
    tts_agent: Agent,
    collection_name: str,
    openai_api_key: str,
    voice: str
):
    query_embedding = list(embedding_model.embed([query]))[0]

    search_response = client.query_points(
        collection_name=collection_name,
        query=query_embedding.tolist(),
        limit=4,
        with_payload=True
    )

    points = search_response.points if hasattr(search_response, "points") else []
    if not points:
        return {"status": "error", "error": "No relevant documents found."}

    context = "Use this knowledge base content:\n\n"
    sources = []

    for p in points:
        payload = p.payload or {}
        sources.append(payload.get("url", "Unknown URL"))
        context += f"\n---\nSOURCE: {payload.get('url','')}\nCONTENT:\n{payload.get('content','')}\n"

    context += f"\n\nUser Question: {query}\nAnswer now:"

    processor_result = await Runner.run(processor_agent, context)
    answer_text = processor_result.final_output

    tts_style = await Runner.run(tts_agent, answer_text)
    tts_instructions = tts_style.final_output

    async_openai = AsyncOpenAI(api_key=openai_api_key)
    audio_response = await async_openai.audio.speech.create(
        model="gpt-4o-mini-tts",
        voice=voice,
        input=answer_text,
        instructions=tts_instructions,
        response_format="mp3"
    )

    audio_path = os.path.join(tempfile.gettempdir(), f"shikhartraders_voice_{uuid.uuid4()}.mp3")
    with open(audio_path, "wb") as f:
        f.write(audio_response.content)

    return {
        "status": "success",
        "text": answer_text,
        "audio_path": audio_path,
        "sources": list(dict.fromkeys(sources))  # unique
    }


# -----------------------------
# MAIN APP
# -----------------------------
init_session_state()
premium_css()

# SIDEBAR
with st.sidebar:
    st.markdown("## 🔑 Configuration")

    qdrant_url = st.text_input("Qdrant URL", type="password")
    qdrant_api_key = st.text_input("Qdrant API Key", type="password")
    openai_api_key = st.text_input("OpenAI API Key", type="password")

    st.markdown("---")
    st.markdown("### 📄 Documentation (RAW Markdown URL)")

    doc_url = st.text_input(
        "Documentation URL",
        value="https://raw.githubusercontent.com/shikhartraders/shikhartraders-voice-agent/main/shikhartraders_support_docs_all_in_one.md"
    )

    st.markdown("---")
    st.markdown("### 🎤 Voice Settings")
    voices = ["alloy", "ash", "ballad", "coral", "echo", "fable", "onyx", "nova", "sage", "shimmer", "verse"]
    st.session_state.selected_voice = st.selectbox("Select Voice", voices, index=voices.index(st.session_state.selected_voice))

    st.markdown("---")

    if st.button("🚀 Initialize System", use_container_width=True):
        if not (qdrant_url and qdrant_api_key and openai_api_key and doc_url):
            st.error("Please fill all required fields.")
        else:
            try:
                with st.status("Initializing...", expanded=True) as status:
                    st.write("🔌 Connecting Qdrant...")
                    collection_name = st.session_state.collection_name

                    # setup qdrant + embedding
                    client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
                    embedding_model = TextEmbeddingWrapper()

                    # create collection if not exists
                    test_embedding = list(embedding_model.embed(["test"]))[0]
                    dim = len(test_embedding)
                    try:
                        client.create_collection(
                            collection_name=collection_name,
                            vectors_config=VectorParams(size=dim, distance=Distance.COSINE)
                        )
                    except Exception as e:
                        if "already exists" not in str(e).lower():
                            raise e

                    st.write("📥 Downloading markdown documentation...")
                    md_text = download_markdown_doc(doc_url)

                    st.write("🧠 Creating embeddings...")
                    store_embeddings(client, embedding_model, md_text, doc_url, collection_name)

                    st.write("🤖 Loading agents...")
                    processor_agent, tts_agent = setup_agents(openai_api_key)

                    st.session_state.client = client
                    st.session_state.embedding_model = embedding_model
                    st.session_state.processor_agent = processor_agent
                    st.session_state.tts_agent = tts_agent
                    st.session_state.setup_complete = True

                    status.update(label="✅ System Ready!", state="complete")

                    st.success("System initialized successfully! Now ask questions below.")
            except Exception as e:
                st.session_state.setup_complete = False
                st.error(f"Setup failed: {str(e)}")

    if st.button("🧹 Clear Chat", use_container_width=True):
        st.session_state.chat = []


# MAIN UI
st.markdown(
    f"""
    <div class="glass-card">
        <div class="titleGlow">Shikhar Traders Voice Agent</div>
        <div class="subText">
            Premium AI support + voice replies (UltraTech Only) • Order help • Delivery guidance • FAQs
        </div>
        <div style="margin-top:10px;">
            <span class="chip">📞 07355969446</span>
            <span class="chip">📞 09450805567</span>
            <span class="chip">✉️ shikhartraders@zohomail.com</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("")

# QUICK ACTIONS
col1, col2, col3, col4, col5 = st.columns(5)
quick_questions = [
    ("🧱 Cement Price", "UltraTech cement price list?"),
    ("🛡 Waterproofing", "Weather Pro waterproofing price list?"),
    ("🔩 Iron Ring", "Iron ring price and bulk order rules?"),
    ("📦 Book Order", "How can I place an order and confirm payment?"),
    ("📍 Store", "Where is Shikhar Traders store location and timing?")
]

for i, (label, q) in enumerate(quick_questions):
    if [col1, col2, col3, col4, col5][i].button(label, use_container_width=True):
        st.session_state.chat.append({"role": "user", "content": q})


st.markdown("---")

# CHAT INPUT
query = st.chat_input("Ask about UltraTech products / order / delivery / payment...")

if query:
    st.session_state.chat.append({"role": "user", "content": query})

# DISPLAY CHAT
for msg in st.session_state.chat:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# ANSWER
if st.session_state.chat and st.session_state.chat[-1]["role"] == "user":
    if not st.session_state.setup_complete:
        st.info("👈 Please initialize system from sidebar first.")
    else:
        last_user = st.session_state.chat[-1]["content"]

        with st.chat_message("assistant"):
            with st.spinner("Thinking + generating voice..."):
                result = asyncio.run(
                    process_query(
                        last_user,
                        st.session_state.client,
                        st.session_state.embedding_model,
                        st.session_state.processor_agent,
                        st.session_state.tts_agent,
                        st.session_state.collection_name,
                        openai_api_key,
                        st.session_state.selected_voice
                    )
                )

                if result["status"] == "success":
                    st.write(result["text"])
                    st.audio(result["audio_path"], format="audio/mp3")

                    with st.expander("Sources"):
                        for s in result["sources"]:
                            st.write(s)

                    st.session_state.chat.append({"role": "assistant", "content": result["text"]})
                else:
                    st.error(result.get("error", "Unknown error"))