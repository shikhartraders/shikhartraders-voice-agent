import os
import time
import streamlit as st
from typing import List

from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from fastembed import TextEmbedding

from firecrawl import FirecrawlApp


# =========================
# CONFIG
# =========================
COLLECTION_NAME = "shikhar_traders_kb"
EMBED_MODEL = "BAAI/bge-small-en-v1.5"
OPENAI_MODEL = "gpt-4o-mini"
TTS_MODEL = "gpt-4o-mini-tts"


# =========================
# PREMIUM UI CSS (3D + Animated)
# =========================
CUSTOM_CSS = """
<style>
/* Full premium animated background */
.stApp {
  background:
    radial-gradient(circle at 15% 10%, rgba(0,229,255,0.14), transparent 35%),
    radial-gradient(circle at 85% 90%, rgba(177,0,255,0.14), transparent 35%),
    radial-gradient(circle at 70% 20%, rgba(0,255,170,0.10), transparent 40%),
    linear-gradient(135deg, #04050a 0%, #060a18 50%, #04050a 100%);
  color: #fff;
}

/* Sidebar glass */
section[data-testid="stSidebar"] {
  background: rgba(255,255,255,0.04);
  border-right: 1px solid rgba(255,255,255,0.10);
  backdrop-filter: blur(14px);
}

/* Main container spacing */
.block-container {
  padding-top: 1.1rem;
  padding-bottom: 1.2rem;
}

/* Premium Card */
.premium-card {
  padding: 18px 18px;
  border-radius: 22px;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.10);
  box-shadow: 0px 18px 50px rgba(0,0,0,0.35);
}

/* 3D Hover Card */
.card3d {
  transform-style: preserve-3d;
  transition: transform 0.25s ease, box-shadow 0.25s ease;
}
.card3d:hover {
  transform: translateY(-4px) rotateX(2deg) rotateY(-2deg);
  box-shadow: 0px 25px 60px rgba(0,0,0,0.45);
}

/* Animated Title */
@keyframes glow {
  0% { text-shadow: 0 0 10px rgba(0,229,255,0.35); }
  50% { text-shadow: 0 0 22px rgba(177,0,255,0.45); }
  100% { text-shadow: 0 0 10px rgba(0,229,255,0.35); }
}
.glow-title {
  animation: glow 2.2s infinite ease-in-out;
  letter-spacing: 0.2px;
}

/* Small muted */
.small-muted {
  color: rgba(255,255,255,0.72);
  font-size: 0.95rem;
}

/* Gradient divider */
.hr-glow {
  height: 1px;
  border: none;
  background: linear-gradient(90deg, transparent, rgba(0,229,255,0.7), rgba(177,0,255,0.7), transparent);
  margin: 14px 0;
}

/* Buttons premium */
.stButton > button {
  border-radius: 14px !important;
  padding: 10px 14px !important;
  background: linear-gradient(90deg, #00e5ff, #b100ff) !important;
  border: 0px !important;
  color: white !important;
  font-weight: 800 !important;
  box-shadow: 0px 10px 30px rgba(0,0,0,0.35);
  transition: transform 0.15s ease-in-out;
}
.stButton > button:hover {
  transform: translateY(-2px);
}

/* Quick buttons (secondary) */
div[data-testid="column"] .stButton > button {
  width: 100%;
}

/* Chat bubble style improvement */
div[data-testid="stChatMessage"] {
  border-radius: 18px;
}

/* Hide Streamlit footer */
footer {visibility: hidden;}
</style>
"""


# =========================
# HELPERS
# =========================
def chunk_text(text: str, chunk_size: int = 900) -> List[str]:
    text = (text or "").strip()
    if not text:
        return []
    chunks = []
    i = 0
    while i < len(text):
        chunks.append(text[i:i + chunk_size])
        i += chunk_size
    return chunks


def ensure_collection(qdrant: QdrantClient, vector_size: int):
    existing = [c.name for c in qdrant.get_collections().collections]
    if COLLECTION_NAME not in existing:
        qdrant.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
        )


def add_documents_to_qdrant(qdrant: QdrantClient, embedder: TextEmbedding, docs: List[str]):
    embeddings = list(embedder.embed(docs))
    points = []
    base_id = int(time.time() * 1000)

    for idx, (doc, vec) in enumerate(zip(docs, embeddings)):
        points.append(
            PointStruct(
                id=base_id + idx,
                vector=vec.tolist(),
                payload={"text": doc}
            )
        )
    qdrant.upsert(collection_name=COLLECTION_NAME, points=points)


def search_docs(qdrant: QdrantClient, embedder: TextEmbedding, query: str, top_k: int = 5) -> List[str]:
    qvec = list(embedder.embed([query]))[0].tolist()
    hits = qdrant.search(collection_name=COLLECTION_NAME, query_vector=qvec, limit=top_k)
    return [h.payload.get("text", "") for h in hits if h.payload]


def build_prompt(context_chunks: List[str], user_question: str) -> str:
    context = "\n\n---\n\n".join(context_chunks[:5])

    return f"""
You are Shikhar Traders AI Voice Agent.

RULES:
- We sell UltraTech products ONLY.
- Always be friendly, fast, and helpful.
- If user asks price: tell approximate price and confirm final price on call/WhatsApp.
- If user asks payment: tell them payment confirmation must be done on call/WhatsApp/email.
- If user asks order booking: ask for (name, location, quantity, delivery/pickup) and then give contact.
- If something is not in docs: politely say "please contact Shikhar Traders" and share phone/email.

CONTACT:
Phone/WhatsApp: 07355969446, 09450805567
Email: shikhartraders@zohomail.com

CONTEXT (Knowledge Base):
{context}

USER QUESTION:
{user_question}

Answer in same style as user: English / Hinglish / Hindi.
Keep answer clear + sales friendly + short.
""".strip()


def generate_answer(openai_client: OpenAI, prompt: str) -> str:
    resp = openai_client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": "You are a helpful customer support assistant for Shikhar Traders."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.25,
    )
    return resp.choices[0].message.content.strip()


def generate_tts(openai_client: OpenAI, text: str, voice: str) -> bytes:
    audio = openai_client.audio.speech.create(
        model=TTS_MODEL,
        voice=voice,
        input=text
    )
    return audio.read()


def set_user_question(text: str):
    st.session_state.quick_question = text


# =========================
# APP
# =========================
st.set_page_config(page_title="Shikhar Traders Voice Agent", page_icon="🎙️", layout="wide")
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Title / Hero
st.markdown(
    """
    <div class="premium-card card3d">
        <h1 class="glow-title">🎙️ Shikhar Traders Voice Agent</h1>
        <p class="small-muted">
            Premium AI support + Voice replies (UltraTech Only) • Built for fast customer answers & order booking
        </p>
        <hr class="hr-glow" />
        <p class="small-muted">
            📞 WhatsApp/Call: <b>07355969446</b>, <b>09450805567</b> &nbsp; | &nbsp;
            📧 <b>shikhartraders@zohomail.com</b>
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

st.write("")

# Sidebar
with st.sidebar:
    st.markdown("## 🔑 Configuration")

    qdrant_url = st.text_input("Qdrant URL", type="default")
    qdrant_api_key = st.text_input("Qdrant API Key", type="password")
    firecrawl_api_key = st.text_input("Firecrawl API Key", type="password")
    openai_api_key = st.text_input("OpenAI API Key", type="password")

    st.markdown("---")
    doc_url = st.text_input("Documentation URL", placeholder="Paste RAW GitHub doc link")

    st.markdown("## 🎤 Voice Settings")
    voice = st.selectbox(
        "Select Voice",
        ["alloy", "ash", "ballad", "coral", "echo", "fable", "onyx", "nova", "sage", "shimmer", "verse"],
        index=3
    )

    crawl_limit = st.slider("Crawl Pages Limit", 1, 10, 5)

    init_btn = st.button("🚀 Initialize System")
    st.markdown("---")
    clear_btn = st.button("🧹 Clear Chat")


# State
if "messages" not in st.session_state:
    st.session_state.messages = []

if "quick_question" not in st.session_state:
    st.session_state.quick_question = ""

if clear_btn:
    st.session_state.messages = []
    st.session_state.quick_question = ""
    st.success("Chat cleared ✅")


# Quick Buttons Panel
st.markdown(
    """
    <div class="premium-card card3d">
        <h3>⚡ Quick Actions (Tap)</h3>
        <p class="small-muted">One-tap questions for customers (Hindi / Hinglish friendly)</p>
    </div>
    """,
    unsafe_allow_html=True
)

c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    st.button("🧱 Cement Price", on_click=set_user_question, args=("UltraTech cement ka price kya hai?",))
with c2:
    st.button("🛡️ Waterproofing", on_click=set_user_question, args=("Weather Pro waterproofing price list batao",))
with c3:
    st.button("🔩 Iron Ring", on_click=set_user_question, args=("Iron ring ka price aur bulk order kaise kare?",))
with c4:
    st.button("🛒 Book Order", on_click=set_user_question, args=("Mujhe cement ka order book karna hai, process batao",))
with c5:
    st.button("📍 Store Location", on_click=set_user_question, args=("Shikhar Traders shop location aur timing bhejo",))

st.write("")


# Initialize
if init_btn:
    if not (qdrant_url and qdrant_api_key and firecrawl_api_key and openai_api_key and doc_url):
        st.error("Please fill all keys + Documentation URL first.")
    else:
        try:
            st.info("Initializing... please wait ⏳")

            st.write("🔗 Connecting Qdrant...")
            qdrant = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)

            st.write("🧠 Loading Embeddings...")
            embedder = TextEmbedding(model_name=EMBED_MODEL)
            vector_size = len(list(embedder.embed(["test"]))[0])
            ensure_collection(qdrant, vector_size)

            st.write("🔥 Crawling documentation with Firecrawl...")
            firecrawl = FirecrawlApp(api_key=firecrawl_api_key)

            # ✅ Correct Firecrawl usage
            crawl_data = firecrawl.crawl_url(
                doc_url,
                params={
                    "limit": crawl_limit,
                    "scrapeOptions": {"formats": ["markdown"]}
                }
            )

            pages = crawl_data.get("data", [])
            all_text = ""
            for p in pages:
                md = p.get("markdown", "") or ""
                all_text += "\n\n" + md

            if not all_text.strip():
                st.error("No text found from documentation URL. Please check your RAW link.")
            else:
                st.write("📦 Creating Knowledge Base...")
                chunks = chunk_text(all_text, chunk_size=900)
                add_documents_to_qdrant(qdrant, embedder, chunks)

                st.session_state.qdrant = qdrant
                st.session_state.embedder = embedder
                st.session_state.openai = OpenAI(api_key=openai_api_key)

                st.success("System Initialized ✅ Now ask questions!")

        except Exception as e:
            st.error(f"Setup failed: {e}")


# Chat history render
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("audio_bytes"):
            st.audio(msg["audio_bytes"], format="audio/mp3")


# Input (auto fill from quick buttons)
default_text = st.session_state.quick_question if st.session_state.quick_question else ""
user_question = st.chat_input("Ask about UltraTech products / order / delivery / payment...")

# If quick button used, simulate sending
if st.session_state.quick_question and not user_question:
    user_question = st.session_state.quick_question
    st.session_state.quick_question = ""


if user_question:
    if "qdrant" not in st.session_state or "embedder" not in st.session_state or "openai" not in st.session_state:
        st.error("Please Initialize System first from the sidebar.")
    else:
        st.session_state.messages.append({"role": "user", "content": user_question})

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                qdrant = st.session_state.qdrant
                embedder = st.session_state.embedder
                openai_client = st.session_state.openai

                context_chunks = search_docs(qdrant, embedder, user_question, top_k=5)
                prompt = build_prompt(context_chunks, user_question)
                answer = generate_answer(openai_client, prompt)

                st.markdown(answer)

                # Voice
                audio_bytes = None
                try:
                    audio_bytes = generate_tts(openai_client, answer, voice=voice)
                    st.audio(audio_bytes, format="audio/mp3")
                except Exception as e:
                    st.warning(f"TTS error: {e}")

        st.session_state.messages.append({"role": "assistant", "content": answer, "audio_bytes": audio_bytes})