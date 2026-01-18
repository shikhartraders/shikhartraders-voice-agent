import os
import time
import streamlit as st
from typing import List, Dict, Any

from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from fastembed import TextEmbedding

from firecrawl import FirecrawlApp


# =========================
# CONFIG
# =========================
COLLECTION_NAME = "shikhar_traders_kb"
EMBED_MODEL = "BAAI/bge-small-en-v1.5"  # FastEmbed model
OPENAI_MODEL = "gpt-4o-mini"  # fast + good for support
TTS_MODEL = "gpt-4o-mini-tts"


# =========================
# PREMIUM UI CSS
# =========================
CUSTOM_CSS = """
<style>
/* Background gradient + premium glass */
.stApp {
    background: radial-gradient(circle at top left, rgba(0,255,255,0.12), transparent 40%),
                radial-gradient(circle at bottom right, rgba(255,0,255,0.12), transparent 40%),
                linear-gradient(135deg, #05060a 0%, #070b18 50%, #05060a 100%);
    color: white;
}

/* Sidebar glass */
section[data-testid="stSidebar"] {
    background: rgba(255,255,255,0.04);
    border-right: 1px solid rgba(255,255,255,0.10);
    backdrop-filter: blur(14px);
}

/* Buttons */
.stButton > button {
    border-radius: 14px !important;
    padding: 10px 16px !important;
    background: linear-gradient(90deg, #00e5ff, #b100ff) !important;
    border: 0px !important;
    color: white !important;
    font-weight: 700 !important;
    box-shadow: 0px 10px 30px rgba(0,0,0,0.35);
    transition: transform 0.15s ease-in-out;
}
.stButton > button:hover {
    transform: translateY(-2px);
}

/* Cards */
.block-container {
    padding-top: 1.2rem;
}
.premium-card {
    padding: 16px;
    border-radius: 18px;
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.10);
    box-shadow: 0px 18px 40px rgba(0,0,0,0.25);
}

/* Animated Title */
@keyframes glow {
  0% { text-shadow: 0 0 8px rgba(0,229,255,0.35); }
  50% { text-shadow: 0 0 18px rgba(177,0,255,0.40); }
  100% { text-shadow: 0 0 8px rgba(0,229,255,0.35); }
}
.glow-title {
  animation: glow 2.2s infinite ease-in-out;
}
.small-muted {
  color: rgba(255,255,255,0.70);
  font-size: 0.95rem;
}
</style>
"""


# =========================
# HELPERS
# =========================
def chunk_text(text: str, chunk_size: int = 900) -> List[str]:
    """Simple chunking by length for embedding."""
    text = text.strip()
    if not text:
        return []
    chunks = []
    i = 0
    while i < len(text):
        chunks.append(text[i:i + chunk_size])
        i += chunk_size
    return chunks


def ensure_collection(qdrant: QdrantClient, vector_size: int):
    """Create collection if not exists."""
    existing = [c.name for c in qdrant.get_collections().collections]
    if COLLECTION_NAME not in existing:
        qdrant.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
        )


def add_documents_to_qdrant(qdrant: QdrantClient, embedder: TextEmbedding, docs: List[str]):
    """Embed and upload docs."""
    embeddings = list(embedder.embed(docs))
    points = []
    for idx, (doc, vec) in enumerate(zip(docs, embeddings)):
        points.append(
            PointStruct(
                id=int(time.time() * 1000) + idx,
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

Your job:
- Answer customer queries about UltraTech products ONLY.
- Use simple, friendly tone.
- If price is asked, tell it is approximate and confirm on call/WhatsApp.
- For payment/order confirmation, ask customer to contact directly.
- If question is not in docs, respond politely and provide contact.

CONTACT:
Phone/WhatsApp: 07355969446, 09450805567
Email: shikhartraders@zohomail.com

CONTEXT (Knowledge Base):
{context}

USER QUESTION:
{user_question}

Answer in the same language style as user (English / Hinglish / Hindi).
Keep it clear, short, helpful, and sales-friendly.
""".strip()


def generate_answer(openai_client: OpenAI, prompt: str) -> str:
    resp = openai_client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": "You are a helpful customer support agent."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
    )
    return resp.choices[0].message.content.strip()


def generate_tts(openai_client: OpenAI, text: str, voice: str) -> bytes:
    audio = openai_client.audio.speech.create(
        model=TTS_MODEL,
        voice=voice,
        input=text
    )
    return audio.read()


# =========================
# STREAMLIT APP
# =========================
st.set_page_config(page_title="Shikhar Traders Voice Agent", page_icon="🎙️", layout="wide")
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Title
st.markdown(
    """
    <div class="premium-card">
        <h1 class="glow-title">🎙️ Shikhar Traders Voice Agent</h1>
        <p class="small-muted">ChatGPT-style support + Voice replies (UltraTech Only)</p>
    </div>
    """,
    unsafe_allow_html=True
)

st.write("")

# Sidebar configuration
with st.sidebar:
    st.markdown("## 🔑 Configuration")

    qdrant_url = st.text_input("Qdrant URL", type="default")
    qdrant_api_key = st.text_input("Qdrant API Key", type="password")
    firecrawl_api_key = st.text_input("Firecrawl API Key", type="password")
    openai_api_key = st.text_input("OpenAI API Key", type="password")

    st.markdown("---")
    doc_url = st.text_input("Documentation URL", placeholder="Paste RAW GitHub doc link here")

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


# Chat state
if "messages" not in st.session_state:
    st.session_state.messages = []

if clear_btn:
    st.session_state.messages = []
    st.success("Chat cleared ✅")


# Initialize system
if init_btn:
    if not (qdrant_url and qdrant_api_key and firecrawl_api_key and openai_api_key and doc_url):
        st.error("Please fill all keys + Documentation URL first.")
    else:
        try:
            st.info("Initializing... please wait ⏳")

            # Qdrant
            st.write("🔗 Connecting Qdrant...")
            qdrant = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)

            # Embedder
            embedder = TextEmbedding(model_name=EMBED_MODEL)
            vector_size = len(list(embedder.embed(["test"]))[0])
            ensure_collection(qdrant, vector_size)

            # Firecrawl
            st.write("🔥 Crawling documentation...")
            firecrawl = FirecrawlApp(api_key=firecrawl_api_key)

            # ✅ FIXED CALL (NO limit= directly)
            crawl_data = firecrawl.crawl_url(
                doc_url,
                params={
                    "limit": crawl_limit,
                    "scrapeOptions": {"formats": ["markdown"]}
                }
            )

            # Extract markdown text
            pages = crawl_data.get("data", [])
            all_text = ""
            for p in pages:
                md = p.get("markdown", "") or ""
                all_text += "\n\n" + md

            if not all_text.strip():
                st.error("No text found from documentation URL. Please check the link.")
            else:
                # Chunk + store
                chunks = chunk_text(all_text, chunk_size=900)
                add_documents_to_qdrant(qdrant, embedder, chunks)

                st.session_state.qdrant = qdrant
                st.session_state.embedder = embedder
                st.session_state.openai = OpenAI(api_key=openai_api_key)

                st.success("System Initialized ✅ Now ask questions!")

        except Exception as e:
            st.error(f"Setup failed: {e}")


# Show chat messages
st.write("")
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("audio_bytes"):
            st.audio(msg["audio_bytes"], format="audio/mp3")


# Chat input
user_question = st.chat_input("Ask about UltraTech products / order / delivery / payment...")

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

                # Generate Voice
                try:
                    audio_bytes = generate_tts(openai_client, answer, voice=voice)
                    st.audio(audio_bytes, format="audio/mp3")
                except Exception as e:
                    audio_bytes = None
                    st.warning(f"TTS error: {e}")

        st.session_state.messages.append({"role": "assistant", "content": answer, "audio_bytes": audio_bytes})