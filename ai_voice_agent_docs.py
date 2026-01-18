from typing import List, Dict, Optional
import os
import uuid
import tempfile
import asyncio
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

from firecrawl import FirecrawlApp
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams
from fastembed import TextEmbedding

from agents import Agent, Runner
from openai import AsyncOpenAI

load_dotenv()

# -----------------------------
# UI Glass Style (Optional)
# -----------------------------
def apply_glass_ui():
    st.markdown("""
    <style>
    .stApp {
        background: radial-gradient(circle at top left, rgba(0,213,255,0.12), transparent 40%),
                    radial-gradient(circle at bottom right, rgba(255,0,200,0.10), transparent 45%),
                    #05060A;
    }
    section[data-testid="stSidebar"] {
        background: rgba(10, 15, 30, 0.55) !important;
        backdrop-filter: blur(14px);
        border-right: 1px solid rgba(255,255,255,0.08);
    }
    button[kind="primary"] {
        border-radius: 14px !important;
        background: linear-gradient(90deg, #00D5FF, #7C3AED) !important;
        border: none !important;
        box-shadow: 0px 0px 20px rgba(0,213,255,0.25);
        transition: 0.2s ease-in-out;
    }
    button[kind="primary"]:hover {
        transform: scale(1.02);
        box-shadow: 0px 0px 35px rgba(0,213,255,0.40);
    }
    </style>
    """, unsafe_allow_html=True)


# -----------------------------
# Session State
# -----------------------------
def init_session_state():
    defaults = {
        "qdrant_url": "",
        "qdrant_api_key": "",
        "firecrawl_api_key": "",
        "openai_api_key": "",
        "doc_url": "",
        "setup_complete": False,
        "client": None,
        "embedding_model": None,
        "processor_agent": None,
        "tts_agent": None,
        "selected_voice": "coral",
        "crawl_limit": 5,
        "chat": []  # ChatGPT style history
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# -----------------------------
# Setup Qdrant
# -----------------------------
def setup_qdrant_collection(qdrant_url: str, qdrant_api_key: str, collection_name="docs_embeddings"):
    client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
    embedding_model = TextEmbedding()

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


# -----------------------------
# Crawl docs (Firecrawl FIXED)
# -----------------------------
def crawl_documentation(firecrawl_api_key: str, url: str, limit: int = 5):
    firecrawl = FirecrawlApp(api_key=firecrawl_api_key)

    response = firecrawl.crawl(
        url=url,
        params={
            "limit": limit,
            "scrapeOptions": {"formats": ["markdown"]}
        }
    )

    pages = []
    for page in response.get("data", []):
        content = page.get("markdown", "") or ""
        metadata = page.get("metadata", {}) or {}
        source_url = metadata.get("sourceURL", url)

        pages.append({
            "content": content,
            "url": source_url,
            "metadata": {
                "title": metadata.get("title", ""),
                "description": metadata.get("description", ""),
                "language": metadata.get("language", "en"),
                "crawl_date": datetime.now().isoformat()
            }
        })
    return pages


# -----------------------------
# Store embeddings
# -----------------------------
def store_embeddings(client: QdrantClient, embedding_model: TextEmbedding, pages: List[Dict], collection_name: str):
    for page in pages:
        if not page["content"].strip():
            continue

        embedding = list(embedding_model.embed([page["content"]]))[0]

        client.upsert(
            collection_name=collection_name,
            points=[
                models.PointStruct(
                    id=str(uuid.uuid4()),
                    vector=embedding.tolist(),
                    payload={
                        "content": page["content"],
                        "url": page["url"],
                        **page["metadata"]
                    }
                )
            ]
        )


# -----------------------------
# Agents
# -----------------------------
def setup_agents(openai_api_key: str):
    os.environ["OPENAI_API_KEY"] = openai_api_key

    processor_agent = Agent(
        name="Shikhar Traders Support Agent",
        instructions=(
            "You are Shikhar Traders customer support assistant.\n"
            "Rules:\n"
            "- Answer from documentation context only.\n"
            "- Be short, clear, professional.\n"
            "- Prices are approximate.\n"
            "- For payment confirmation and final price, tell customer to contact:\n"
            "  Call/WhatsApp: 07355969446 or 09450805567\n"
            "  Email: shikhartraders@zohomail.com\n"
        ),
        model="gpt-4o"
    )

    tts_agent = Agent(
        name="Text-to-Speech Agent",
        instructions="Convert response into natural spoken speech. Friendly and clear.",
        model="gpt-4o-mini-tts"
    )

    return processor_agent, tts_agent


# -----------------------------
# Answer + Voice
# -----------------------------
async def answer_with_voice(query: str):
    query_embedding = list(st.session_state.embedding_model.embed([query]))[0]

    search_response = st.session_state.client.query_points(
        collection_name="docs_embeddings",
        query=query_embedding.tolist(),
        limit=3,
        with_payload=True
    )

    results = search_response.points if hasattr(search_response, "points") else []
    if not results:
        return None, None, []

    context = ""
    sources = []
    for r in results:
        payload = r.payload or {}
        sources.append(payload.get("url", "Unknown URL"))
        context += f"Source: {payload.get('url','')}\n{payload.get('content','')}\n\n"

    context += f"User Question: {query}\n"

    processor_result = await Runner.run(st.session_state.processor_agent, context)
    text_answer = processor_result.final_output

    tts_result = await Runner.run(st.session_state.tts_agent, text_answer)
    tts_instructions = tts_result.final_output

    async_openai = AsyncOpenAI(api_key=st.session_state.openai_api_key)
    audio_response = await async_openai.audio.speech.create(
        model="gpt-4o-mini-tts",
        voice=st.session_state.selected_voice,
        input=text_answer,
        instructions=tts_instructions,
        response_format="mp3"
    )

    audio_path = os.path.join(tempfile.gettempdir(), f"voice_{uuid.uuid4()}.mp3")
    with open(audio_path, "wb") as f:
        f.write(audio_response.content)

    return text_answer, audio_path, list(dict.fromkeys(sources))


# -----------------------------
# Sidebar
# -----------------------------
def sidebar():
    with st.sidebar:
        st.title("🔑 Configuration")

        st.session_state.qdrant_url = st.text_input("Qdrant URL", value=st.session_state.qdrant_url, type="password")
        st.session_state.qdrant_api_key = st.text_input("Qdrant API Key", value=st.session_state.qdrant_api_key, type="password")
        st.session_state.firecrawl_api_key = st.text_input("Firecrawl API Key", value=st.session_state.firecrawl_api_key, type="password")
        st.session_state.openai_api_key = st.text_input("OpenAI API Key", value=st.session_state.openai_api_key, type="password")

        st.session_state.doc_url = st.text_input("Documentation URL", value=st.session_state.doc_url)

        voices = ["alloy", "ash", "ballad", "coral", "echo", "fable", "onyx", "nova", "sage", "shimmer", "verse"]
        st.session_state.selected_voice = st.selectbox("Select Voice", voices, index=voices.index(st.session_state.selected_voice))

        st.session_state.crawl_limit = st.slider("Crawl Pages Limit", 1, 10, st.session_state.crawl_limit)

        if st.button("Initialize System", type="primary"):
            try:
                with st.status("Initializing...", expanded=True) as status:
                    st.write("Connecting Qdrant...")
                    client, embedding_model = setup_qdrant_collection(st.session_state.qdrant_url, st.session_state.qdrant_api_key)
                    st.session_state.client = client
                    st.session_state.embedding_model = embedding_model

                    st.write("Crawling documentation...")
                    pages = crawl_documentation(st.session_state.firecrawl_api_key, st.session_state.doc_url, st.session_state.crawl_limit)

                    st.write("Saving embeddings...")
                    store_embeddings(client, embedding_model, pages, "docs_embeddings")

                    st.write("Setting up AI agents...")
                    processor, tts = setup_agents(st.session_state.openai_api_key)
                    st.session_state.processor_agent = processor
                    st.session_state.tts_agent = tts

                    st.session_state.setup_complete = True
                    status.update(label="✅ System Ready!", state="complete")

            except Exception as e:
                st.session_state.setup_complete = False
                st.error(f"❌ Setup failed: {e}")

        st.markdown("---")
        if st.button("🧹 Clear Chat"):
            st.session_state.chat = []
            st.rerun()


# -----------------------------
# Main App
# -----------------------------
def main():
    st.set_page_config(page_title="Shikhar Traders Voice Agent", page_icon="🎙️", layout="wide")
    init_session_state()
    apply_glass_ui()
    sidebar()

    st.title("🎙️ Shikhar Traders Voice Agent")
    st.caption("ChatGPT-style support + voice replies")

    if not st.session_state.setup_complete:
        st.info("👈 Add keys + docs URL and click Initialize System.")
        return

    # Chat history
    for msg in st.session_state.chat:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("audio"):
                st.audio(msg["audio"], format="audio/mp3")

    user_query = st.chat_input("Ask something... (Example: UltraTech cement price?)")

    if user_query:
        st.session_state.chat.append({"role": "user", "content": user_query})

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                text_answer, audio_path, sources = asyncio.run(answer_with_voice(user_query))

            if not text_answer:
                text_answer = "Sorry, I couldn't find that in the documentation. Please try again or re-initialize the system."
                st.markdown(text_answer)
                st.session_state.chat.append({"role": "assistant", "content": text_answer})
            else:
                st.markdown(text_answer)
                st.audio(audio_path, format="audio/mp3")

                st.markdown("**Sources:**")
                for s in sources:
                    st.markdown(f"- {s}")

                st.session_state.chat.append({"role": "assistant", "content": text_answer, "audio": audio_path})

        st.rerun()


if __name__ == "__main__":
    main()
