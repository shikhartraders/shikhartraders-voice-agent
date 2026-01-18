import streamlit as st
import requests
import time

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="Shikhar Traders | Voice AI",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# PREMIUM CLEAN CSS
# =========================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.stApp {
    background: radial-gradient(circle at top right, #0a0c14, #05060b);
    color: #e0e0e0;
}

.glass-card {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.10);
    border-radius: 20px;
    padding: 22px;
    margin-bottom: 16px;
    backdrop-filter: blur(12px);
}

.hero-title {
    font-size: 3rem;
    font-weight: 900;
    background: linear-gradient(90deg, #00f5ff, #a855f7, #00ff88);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.4rem;
}

.subtext { color: rgba(255,255,255,0.55); font-size: 0.95rem; }

.badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 50px;
    font-size: 0.75rem;
    font-weight: 700;
    background: rgba(0, 245, 255, 0.08);
    color: #00f5ff;
    border: 1px solid rgba(0, 245, 255, 0.2);
    margin-right: 8px;
}

.chat-bubble {
    padding: 14px 16px;
    border-radius: 16px;
    margin-bottom: 10px;
    border: 1px solid rgba(255,255,255,0.06);
}
.user-bubble { background: rgba(168, 85, 247, 0.10); border-left: 4px solid #a855f7; }
.agent-bubble { background: rgba(0, 255, 136, 0.06); border-left: 4px solid #00ff88; }

.stButton>button {
    width: 100%;
    border-radius: 12px !important;
    background: rgba(255,255,255,0.06) !important;
    color: white !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    height: 3em;
    font-weight: 800 !important;
    transition: 0.2s ease;
}
.stButton>button:hover {
    border: 1px solid #00f5ff !important;
    color: #00f5ff !important;
    box-shadow: 0 0 14px rgba(0, 245, 255, 0.15);
    transform: translateY(-1px);
}
</style>
""", unsafe_allow_html=True)

# =========================
# BUSINESS DATA
# =========================
BUSINESS = {
    "name": "Shikhar Traders",
    "phones": ["07355969446", "09450805567"],
    "email": "shikhartraders@zohomail.com",
    "maps": "https://maps.app.goo.gl/22dertGs5oZxrWMb8",
    "website": "https://shikhartradersbs.odoo.com/",
    "note": "Prices are approximate. Final price/stock/payment confirmation must be done via call/WhatsApp/email."
}

# =========================
# HELPERS
# =========================
def fetch_docs_text(raw_url: str) -> str:
    """Download docs from RAW github link"""
    raw_url = (raw_url or "").strip()
    if not raw_url:
        raise ValueError("RAW docs URL is empty.")

    if "raw.githubusercontent.com" not in raw_url:
        raise ValueError("Please paste RAW GitHub URL (raw.githubusercontent.com).")

    r = requests.get(raw_url, timeout=25)
    if r.status_code != 200:
        raise ValueError(f"Docs fetch failed (HTTP {r.status_code}).")

    text = r.text.strip()
    if len(text) < 50:
        raise ValueError("Docs loaded but looks empty/too short.")
    return text


def openai_chat(api_key: str, question: str, docs_text: str, lang: str) -> str:
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    system_prompt = f"""
You are the official AI support assistant of {BUSINESS['name']} (UltraTech only).
Reply in {lang}.
Answer strictly using the DOCUMENTATION provided.
If user asks final price, stock, delivery charge, or payment -> ask them to call/WhatsApp {BUSINESS['phones'][0]} / {BUSINESS['phones'][1]} or email {BUSINESS['email']}.
Keep replies short, clear, and professional.
"""

    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": system_prompt.strip()},
            {"role": "user", "content": f"DOCUMENTATION:\n{docs_text}\n\nUSER QUESTION:\n{question}"}
        ],
        "temperature": 0.4
    }

    r = requests.post(url, headers=headers, json=payload, timeout=30)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()


def openai_tts(api_key: str, text: str, voice: str = "alloy") -> bytes:
    url = "https://api.openai.com/v1/audio/speech"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": "gpt-4o-mini-tts", "voice": voice, "input": text}
    r = requests.post(url, headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    return r.content


# =========================
# SESSION STATE
# =========================
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_answer" not in st.session_state:
    st.session_state.last_answer = ""
if "tts_last_time" not in st.session_state:
    st.session_state.tts_last_time = 0
if "docs_text" not in st.session_state:
    st.session_state.docs_text = ""
if "docs_loaded" not in st.session_state:
    st.session_state.docs_loaded = False

# =========================
# SIDEBAR
# =========================
with st.sidebar:
    st.markdown("### ⚙️ Settings")

    api_key = st.text_input("OpenAI API Key", type="password")

    docs_url = st.text_input(
        "Documentation RAW URL",
        placeholder="https://raw.githubusercontent.com/.../shikhartraders_support_docs_all_in_one.md"
    )

    lang = st.selectbox("Language", ["English", "Hinglish", "Hindi"])
    voice = st.selectbox("Voice", ["alloy", "coral", "sage", "verse"])
    auto_voice = st.toggle("Auto Voice Reply", value=False)

    if st.button("📥 Load Documentation"):
        try:
            with st.spinner("Loading documentation..."):
                st.session_state.docs_text = fetch_docs_text(docs_url)
                st.session_state.docs_loaded = True
            st.success("✅ Documentation loaded successfully!")
        except Exception as e:
            st.session_state.docs_loaded = False
            st.session_state.docs_text = ""
            st.error(f"❌ Docs not loaded: {e}")

    st.markdown("---")

    if st.button("🧹 Clear Chat"):
        st.session_state.messages = []
        st.session_state.last_answer = ""
        st.rerun()

# =========================
# HEADER
# =========================
st.markdown(f"""
<div class="glass-card">
    <div class="hero-title">{BUSINESS['name']} Voice AI</div>
    <div style="margin-bottom:12px;">
        <span class="badge">UltraTech Only</span>
        <span class="badge">Docs Based</span>
        <span class="badge">Premium AI</span>
    </div>
    <div class="subtext">
        📞 {BUSINESS['phones'][0]} / {BUSINESS['phones'][1]} &nbsp; | &nbsp;
        ✉️ {BUSINESS['email']} <br>
        📍 Store: {BUSINESS['maps']} <br>
        🌐 Website: {BUSINESS['website']}
    </div>
</div>
""", unsafe_allow_html=True)

# =========================
# QUICK ACTIONS
# =========================
st.markdown("### ⚡ Quick Actions")
c1, c2, c3, c4 = st.columns(4)

if c1.button("🧱 Cement Price"):
    st.session_state.messages.append({"role": "user", "content": "Tell me UltraTech cement prices."})
if c2.button("🛡️ Waterproofing"):
    st.session_state.messages.append({"role": "user", "content": "Tell me Weather Pro waterproofing prices and uses."})
if c3.button("🔩 Iron Ring"):
    st.session_state.messages.append({"role": "user", "content": "Tell me iron ring price and bulk order rule."})
if c4.button("📍 Store Info"):
    st.session_state.messages.append({"role": "user", "content": "Tell me store location, timing, and contact details."})

# =========================
# CHAT UI
# =========================
st.markdown("### 💬 Chat")

if len(st.session_state.messages) == 0:
    st.session_state.messages.append({
        "role": "assistant",
        "content": "Hi 👋 I’m Shikhar Traders Voice AI.\n\n➡️ First: Paste RAW docs link in sidebar and click **Load Documentation**."
    })

for m in st.session_state.messages:
    if m["role"] == "user":
        st.markdown(
            f"<div class='chat-bubble user-bubble'><b>You:</b><br>{m['content']}</div>",
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"<div class='chat-bubble agent-bubble'><b>Agent:</b><br>{m['content']}</div>",
            unsafe_allow_html=True
        )

prompt = st.chat_input("Ask about products / delivery / payment...")

if prompt:
    if not api_key.strip():
        st.error("Please add OpenAI API Key in sidebar.")
    elif not st.session_state.docs_loaded or not st.session_state.docs_text.strip():
        st.error("Docs not loaded. Paste RAW docs link and click **Load Documentation**.")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})

        try:
            with st.spinner("Thinking..."):
                reply = openai_chat(api_key.strip(), prompt, st.session_state.docs_text, lang)

            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.session_state.last_answer = reply

            # Auto voice reply with cooldown
            if auto_voice:
                now = time.time()
                if now - st.session_state.tts_last_time < 10:
                    st.warning("⏳ Voice cooldown: wait 10 seconds (to avoid 429).")
                else:
                    try:
                        audio = openai_tts(api_key.strip(), reply[:700], voice=voice)
                        st.audio(audio, format="audio/mp3")
                        st.session_state.tts_last_time = now
                    except:
                        st.error("🔊 Voice error (rate limit). Wait 10 sec & try again.")

        except Exception as e:
            st.error(f"Error: {e}")

        st.rerun()

# =========================
# SPEAK LAST ANSWER
# =========================
st.markdown("---")
if st.button("🎙️ Speak Last Answer"):
    if not api_key.strip():
        st.warning("Add OpenAI API key first.")
    elif not st.session_state.last_answer.strip():
        st.info("No answer yet.")
    else:
        now = time.time()
        if now - st.session_state.tts_last_time < 10:
            st.warning("⏳ Wait 10 seconds to avoid 429.")
        else:
            try:
                audio = openai_tts(api_key.strip(), st.session_state.last_answer[:700], voice=voice)
                st.audio(audio, format="audio/mp3")
                st.session_state.tts_last_time = now
            except:
                st.error("🔊 TTS rate limit hit. Please wait & try again.")

st.caption(f"⚠️ {BUSINESS['note']}")