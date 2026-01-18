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

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: radial-gradient(circle at top right, #0a0c14, #05060b);
    color: #e0e0e0;
}

/* Glass Card */
.glass-card {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 20px;
    padding: 22px;
    margin-bottom: 16px;
    backdrop-filter: blur(12px);
}

/* Title */
.hero-title {
    font-size: 3rem;
    font-weight: 900;
    background: linear-gradient(90deg, #00f5ff, #a855f7, #00ff88);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.4rem;
}

/* Subtitle */
.subtext {
    color: rgba(255,255,255,0.55);
    font-size: 0.95rem;
}

/* Badges */
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

/* Chat bubbles */
.chat-bubble {
    padding: 14px 16px;
    border-radius: 16px;
    margin-bottom: 10px;
    border: 1px solid rgba(255,255,255,0.06);
}
.user-bubble {
    background: rgba(168, 85, 247, 0.10);
    border-left: 4px solid #a855f7;
}
.agent-bubble {
    background: rgba(0, 255, 136, 0.06);
    border-left: 4px solid #00ff88;
}

/* Buttons */
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
# KNOWLEDGE BASE (FAST)
# =========================
KB = f"""
You are Shikhar Traders AI Assistant. We only sell UltraTech products.

CONTACT:
Call/WhatsApp: {BUSINESS['phones'][0]}, {BUSINESS['phones'][1]}
Email: {BUSINESS['email']}
Store Location: {BUSINESS['maps']}
Website: {BUSINESS['website']}

PRODUCTS + Approx Prices:
CEMENT:
- UltraTech Paper Bag: ₹405 approx / bag
- UltraTech Super: ₹415 approx / bag
- UltraTech Weather Plus: ₹420 approx / bag

WATERPROOFING (Weather Pro):
- 1L ₹175 approx
- 5L ₹750 approx
- 10L ₹1450 approx
- 20L ₹2500 approx

IRON RING:
- ₹12 per piece (bulk order only, online 120+)

RULE:
If user asks final price, payment, or stock -> tell them to call/WhatsApp or email.
"""

# =========================
# OPENAI CHAT
# =========================
def openai_chat(api_key, question, lang):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    system_prompt = f"""
You are the official AI support assistant of {BUSINESS['name']} (UltraTech only).
Reply in {lang}.
Keep answers short, clear, professional.
If asked about final price/stock/payment -> ask to call/WhatsApp {BUSINESS['phones'][0]} / {BUSINESS['phones'][1]} or email {BUSINESS['email']}.
"""

    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": system_prompt.strip()},
            {"role": "user", "content": f"KNOWLEDGE:\n{KB}\n\nUSER QUESTION:\n{question}"}
        ],
        "temperature": 0.4
    }

    r = requests.post(url, headers=headers, json=payload, timeout=30)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()

# =========================
# OPENAI TTS (OPTIONAL)
# =========================
def openai_tts(api_key, text, voice="alloy"):
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

# =========================
# SIDEBAR
# =========================
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    api_key = st.text_input("OpenAI API Key", type="password")
    lang = st.selectbox("Language", ["English", "Hinglish", "Hindi"])
    voice = st.selectbox("Voice", ["alloy", "coral", "sage", "verse"])
    auto_voice = st.toggle("Auto Voice Reply", value=False)

    st.markdown("---")
    if st.button("🧹 Clear Chat"):
        st.session_state.messages = []
        st.session_state.last_answer = ""
        st.rerun()

# =========================
# HEADER CARD
# =========================
st.markdown(f"""
<div class="glass-card">
    <div class="hero-title">{BUSINESS['name']} Voice AI</div>
    <div style="margin-bottom:12px;">
        <span class="badge">UltraTech Only</span>
        <span class="badge">Fast Support</span>
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
if c4.button("💳 Payment"):
    st.session_state.messages.append({"role": "user", "content": "How can I confirm payment and final price?"})

# =========================
# CHAT UI
# =========================
st.markdown("### 💬 Chat")

if len(st.session_state.messages) == 0:
    st.session_state.messages.append({
        "role": "assistant",
        "content": "Hi 👋 I’m Shikhar Traders Voice AI. Ask me about UltraTech cement / waterproofing / iron rings."
    })

chat_box = st.container()

with chat_box:
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
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})

        try:
            with st.spinner("Thinking..."):
                reply = openai_chat(api_key.strip(), prompt, lang)

            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.session_state.last_answer = reply

            # Auto voice reply with cooldown (avoid 429)
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
                        st.error("🔊 Voice error (rate limit). Please wait 10 sec & try again.")

        except Exception as e:
            st.error(f"Error: {e}")

        st.rerun()

# =========================
# SPEAK LAST ANSWER (OPTIONAL BUTTON)
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