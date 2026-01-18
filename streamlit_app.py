from typing import List, Dict, Optional
import os
import time
import uuid
import tempfile
from datetime import datetime
import asyncio

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


# ---------------------------
# Session State
# ---------------------------
def init_session_state():
    defaults = {
        "initialized": False,
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
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ---------------------------
# Qdrant Setup
# ---------------------------
def setup_qdrant_collection(
    qdrant_url: str,
    qdrant_api_key: str,
    collection_name: str = "docs_embeddings",
):
    client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)

    embedding_model = TextEmbedding()
    test_embedding = list(embedding_model.embed(["test"]))[0]
    embedding_dim = len(test_embedding)

    try:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=embedding_dim, distance=Distance.COSINE),
        )
    except Exception as e:
        if "already exists" not in str(e).lower():
            raise e

    return client, embedding_model


# ---------------------------
# Firecrawl (FIXED)
# ---------------------------
def crawl_documentation(
    firecrawl_api_key: str,
    url: str,
    limit: int = 5,
):
    firecrawl = FirecrawlApp(api_key=firecrawl_api_key)
    pages = []

    # UPDATED Firecrawl call (NO params=)
    response = firecrawl.crawl_url(
        url=url,
        limit=limit,
        scrape_options={
            "formats": ["markdown"]
        },
    )

    for page in response.get("data", []):
        content = page.get("markdown", "") or ""
        metadata = page.get("metadata", {}) or {}
        source_url = metadata.get("sourceURL", url)

        pages.append(
            {
                "content": content,
                "url": source_url,
                "metadata": {
                    "title": metadata.get("title", ""),
                    "description": metadata.get("description", ""),
                    "language": metadata.get("language", "en"),
                    "crawl_date": datetime.now().isoformat(),
                },
            }
        )

    return pages


# ---------------------------
# Store Embeddings
# ---------------------------
def store_embeddings(
    client: QdrantClient,
    embedding_model: TextEmbedding,
    pages: List[Dict],
    collection_name: str,
):
    for page in pages:
        if not page.get("content"):
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
                        **page["metadata"],
                    },
                )
            ],
        )


# ---------------------------
# Agents
# ---------------------------
def setup_agents(openai_api_key: str):
    os.environ["OPENAI_API_KEY"] = openai_api_key

    processor_agent = Agent(
        name="Documentation Processor",
        instructions="""
You are a helpful Shikhar Traders support assistant.

Rules:
- Answer in a friendly, professional tone.
- Keep answers short and clear.
- If user asks for final price, always say prices are approximate and confirm on call/WhatsApp.
- For payment confirmation, always ask customer to contact on phone/email.
- Mention products are UltraTech only.
- Provide store location link if asked.

Return response in a format easy to speak out loud.
""",
        model="gpt-4o",
    )

    tts_agent = Agent(
        name="Text-to-Speech Agent",
        instructions="""
Convert the response into natural spoken Hindi+English style (Hinglish).
Use short sentences, clear pauses, and friendly tone.
""",
        model="gpt-4o-mini-tts",
    )

    return processor_agent, tts_agent


# ---------------------------
# Query Processing
# ---------------------------
async def process_query(
    query: str,
    client: QdrantClient,
    embedding_model: TextEmbedding,
    processor_agent: Agent,
    tts_agent: Agent,
    collection_name: str,
    openai_api_key: str,
    voice: str,
):
    query_embedding = list(embedding_model.embed([query]))[0]

    search_response = client.query_points(
        collection_name=collection_name,
        query=query_embedding.tolist(),
        limit=3,
        with_payload=True,
    )

    search_results = search_response.points if hasattr(search_response, "points") else []

    if not search_results:
        return {
            "status": "error",
            "error": "No relevant documents found in the vector database.",
        }

    context = "Use the following knowledge base content:\n\n"
    sources = []

    for result in search_results:
        payload = result.payload or {}
        url = payload.get("url", "Unknown URL")
        content = payload.get("content", "")

        if url not in sources:
            sources.append(url)

        context += f"\nSOURCE: {url}\nCONTENT:\n{content}\n"

    context += f"\n\nUSER QUESTION: {query}\n"
    context += "\nAnswer now."

    processor_result = await Runner.run(processor_agent, context)
    processor_response = processor_result.final_output

    # TTS style guidance (optional)
    tts_result = await Runner.run(tts_agent, processor_response)
    tts_instructions = tts_result.final_output

    async_openai = AsyncOpenAI(api_key=openai_api_key)

    audio_response = await async_openai.audio.speech.create(
        model="gpt-4o-mini-tts",
        voice=voice,
        input=processor_response,
        instructions=tts_instructions,
        response_format="mp3",
    )

    temp_dir = tempfile.gettempdir()
    audio_path = os.path.join(temp_dir, f"response_{uuid.uuid4()}.mp3")

    with open(audio_path, "wb") as f:
        f.write(audio_response.content)

    return {
        "status": "success",
        "text_response": processor_response,
        "audio_path": audio_path,
        "sources": sources,
    }


# ---------------------------
# Sidebar UI
# ---------------------------
def sidebar_config():
    with st.sidebar:
        st.title("🔑 Configuration")

        st.session_state.qdrant_url = st.text_input(
            "Qdrant URL", value=st.session_state.qdrant_url, type="password"
        )
        st.session_state.qdrant_api_key = st.text_input(
            "Qdrant API Key", value=st.session_state.qdrant_api_key, type="password"
        )
        st.session_state.firecrawl_api_key = st.text_input(
            "Firecrawl API Key", value=st.session_state.firecrawl_api_key, type="password"
        )
        st.session_state.openai_api_key = st.text_input(
            "OpenAI API Key", value=st.session_state.openai_api_key, type="password"
        )

        st.markdown("---")

        st.session_state.doc_url = st.text_input(
            "Documentation URL",
            value=st.session_state.doc_url,
            placeholder="Paste RAW docs link here",
        )

        st.markdown("---")

        voices = [
            "alloy",
            "ash",
            "ballad",
            "coral",
            "echo",
            "fable",
            "onyx",
            "nova",
            "sage",
            "shimmer",
            "verse",
        ]

        st.session_state.selected_voice = st.selectbox(
            "Select Voice",
            options=voices,
            index=voices.index(st.session_state.selected_voice),
        )

        st.session_state.crawl_limit = st.slider("Crawl Pages Limit", 1, 10, 5)

        if st.button("Initialize System", type="primary"):
            if all(
                [
                    st.session_state.qdrant_url,
                    st.session_state.qdrant_api_key,
                    st.session_state.firecrawl_api_key,
                    st.session_state.openai_api_key,
                    st.session_state.doc_url,
                ]
            ):
                try:
                    st.info("Connecting Qdrant...")
                    client, embedding_model = setup_qdrant_collection(
                        st.session_state.qdrant_url,
                        st.session_state.qdrant_api_key,
                        "docs_embeddings",
                    )

                    st.info("Crawling documentation...")
                    pages = crawl_documentation(
                        st.session_state.firecrawl_api_key,
                        st.session_state.doc_url,
                        limit=st.session_state.crawl_limit,
                    )

                    st.info("Storing embeddings...")
                    store_embeddings(client, embedding_model, pages, "docs_embeddings")

                    processor_agent, tts_agent = setup_agents(st.session_state.openai_api_key)

                    st.session_state.client = client
                    st.session_state.embedding_model = embedding_model
                    st.session_state.processor_agent = processor_agent
                    st.session_state.tts_agent = tts_agent
                    st.session_state.setup_complete = True

                    st.success(f"✅ Initialized successfully! Pages crawled: {len(pages)}")
                except Exception as e:
                    st.error(f"❌ Setup failed: {str(e)}")
            else:
                st.error("Please fill in all required fields!")


# ---------------------------
# Main App
# ---------------------------
def run_streamlit():
    st.set_page_config(
        page_title="Shikhar Traders Voice Agent",
        page_icon="🎙️",
        layout="wide",
    )

    init_session_state()
    sidebar_config()

    st.title("🎙️ Shikhar Traders Voice Agent")
    st.caption("ChatGPT-style support + voice replies (UltraTech Only)")

    if not st.session_state.setup_complete:
        st.info("👈 Add keys + docs URL and click Initialize System.")
        return

    query = st.text_input(
        "Ask a question (English / Hinglish / Hindi)",
        placeholder="Example: UltraTech Super ka price kya hai?",
    )

    if query:
        with st.status("Processing...", expanded=True) as status:
            try:
                result = asyncio.run(
                    process_query(
                        query=query,
                        client=st.session_state.client,
                        embedding_model=st.session_state.embedding_model,
                        processor_agent=st.session_state.processor_agent,
                        tts_agent=st.session_state.tts_agent,
                        collection_name="docs_embeddings",
                        openai_api_key=st.session_state.openai_api_key,
                        voice=st.session_state.selected_voice,
                    )
                )

                if result["status"] == "success":
                    status.update(label="✅ Done", state="complete")
                    st.subheader("Answer")
                    st.write(result["text_response"])

                    st.subheader(f"🔊 Audio ({st.session_state.selected_voice})")
                    st.audio(result["audio_path"], format="audio/mp3")

                    st.subheader("Sources")
                    for s in result["sources"]:
                        st.write("-", s)
                else:
                    status.update(label="❌ Error", state="error")
                    st.error(result.get("error", "Unknown error"))

            except Exception as e:
                status.update(label="❌ Error", state="error")
                st.error(str(e))


if __name__ == "__main__":
    run_streamlit()
