import streamlit as st
import requests
import pandas as pd
from datetime import datetime
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
# PREMIUM CSS (MODERN & CLEAN)
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

    /* Glass Cards */
    .glass-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 25px;
        margin-bottom: 20px;
        backdrop-filter: blur(10px);
        transition: transform 0.3s ease;
    }

    /* Animated Title */
    .hero-title {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(90deg, #00f5ff, #a855f7, #00ff88);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }

    /* Status Badges */
    .badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 50px;
        font-size: 0.75rem;
        font-weight: 600;
        background: rgba(0, 245, 255, 0.1);
        color: #00f5ff;
        border: 1px solid rgba(0, 245, 255, 0.2);
        margin-right: 8px;
    }

    /* Custom Chat Styling */
    .chat-bubble {
        padding: 15px;
        border-radius: 15px;
        margin-bottom: 10px;
        border: 1px solid rgba(255,255,255,0.05);
    }
    .user-bubble { background: rgba(168, 85, 247, 0.1); border-left: 4px solid #a855f7; }
    .agent-bubble { background: rgba(0, 255, 136, 0.05); border-left: 4px solid #00ff88; }

    /* Button Styling */
    .stButton>button {
        width: 100%;
        border-radius: 12px !important;
        background: linear-gradient(135deg, rgba(255,255,255,0.1), rgba(255,255,255,0.05)) !important;
        color: white !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        height: 3em;
    }
    .stButton>button:hover {
        border: 1px solid #00f5ff !important;
        color: #00f5ff !important;
        box-shadow: 0 0 15px rgba(0, 245, 255, 0.2);
    }
</style>
""", unsafe_allow_html=True)

# =========================
# CONSTANTS & BUSINESS DATA
# =========================
BUSINESS = {
    "name": "Shikhar Traders",
    "phones": ["+91 7355969446", "+91 9450805567"],
    "email": "shikhartraders@zohomail.com",
    "maps": "https://maps.google.com/?q=Shikhar+Traders",
    "website": "https://shikhartradersbs.odoo.com/"
}

# =========================
# CORE FUNCTIONS
# =========================

def openai_chat(api_key, question, kb_text, lang):
    """Corrected OpenAI Chat Completion Logic"""
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    system_prompt = f"""
    You are the official AI representative of {BUSINESS['name']}. 
    Focus strictly on UltraTech products. 
    Language: {lang}. 
    Tone: Professional, helpful, concise.
    Constraint: For final pricing, availability, or payments, always direct them to: {BUSINESS['phones'][0]}.
    """
    
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Context:\n{kb_text}\n\nQuestion: {question}"}
        ],
        "temperature": 0.7
    }

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        r.raise_for_status()
        return r.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"Support is currently offline. Please call {BUSINESS['phones'][0]}. (Error: {str(e)})"

def openai_tts(api_key, text, voice_model):
    url = "https://api.openai.com/v1/audio/speech"
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {"model": "tts-1", "voice": voice_model, "input": text}
    r = requests.post(url, headers=headers, json=payload, timeout=30)
    r.raise_for_status()
    return r.content

# =========================
# SESSION STATE
# =========================
for key in ["messages", "orders", "last_answer", "docs_text", "tts_cooldown"]:
    if key not in st.session_state:
        if key == "messages": st.session_state[key] = []
        elif key == "orders": st.session_state[key] = []
        elif key == "tts_cooldown": st.session_state[key] = 0
        else: st.session_state[key] = ""

# =========================
# SIDEBAR
# =========================
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/en/b/b5/UltraTech_Cement_Logo.svg", width=150)
    st.markdown("### 🛠️ Control Panel")
    api_key = st.text_input("OpenAI Key", type="password")
    lang = st.selectbox("Language", ["English", "Hindi", "Hinglish"])
    voice_opt = st.selectbox("Voice Tone", ["shimmer", "alloy", "echo", "nova"])
    auto_tts = st.toggle("Auto-Voice Reply", value=False)
    
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# =========================
# MAIN UI
# =========================
st.markdown(f"""
<div class="glass-card">
    <div class="hero-title">{BUSINESS['name']}</div>
    <div style="margin-bottom:15px;">
        <span class="badge">UltraTech Certified</span>
        <span class="badge">Direct Dealer</span>
        <span class="badge">Fast Delivery</span>
    </div>
    <p style="color:rgba(255,255,255,0.6); font-size:0.9rem;">
        📍 Kanpur - Lucknow Highway | 📞 {BUSINESS['phones'][0]} | ✉️ {BUSINESS['email']}
    </p>
</div>
""", unsafe_allow_html=True)

# ⚡ QUICK ACTIONS
cols = st.columns(4)
actions = ["Cement Price", "Waterproofing", "Iron Ring", "Delivery Areas"]
for i, col in enumerate(cols):
    if col.button(actions[i]):
        st.session_state.messages.append({"role": "user", "content": f"Tell me about {actions[i]}"})

# 💬 CHAT INTERFACE
st.markdown("### 💬 Assistant")
chat_container = st.container(height=400)

with chat_container:
    if not st.session_state.messages:
        st.info("Ask about UltraTech Paper Bag, Weather Plus, or Waterproofing solutions.")
    for m in st.session_state.messages:
        cls = "user-bubble" if m["role"] == "user" else "agent-bubble"
        st.markdown(f"<div class='chat-bubble {cls}'><b>{'You' if m['role']=='user' else 'Agent'}:</b><br>{m['content']}</div>", unsafe_allow_html=True)

# ⌨️ INPUT
if prompt := st.chat_input("Type your message here..."):
    if not api_key:
        st.error("Please enter an API Key in the sidebar.")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Generate Response
        kb = "Products: Cement (Paper Bag 405, Super 415, Weather Plus 420), Waterproofing (1L-20L), Iron Rings."
        response = openai_chat(api_key, prompt, kb, lang)
        
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.session_state.last_answer = response
        
        # Handle Auto TTS
        if auto_tts:
            try:
                audio = openai_tts(api_key, response[:400], voice_opt)
                st.audio(audio, autoplay=True)
            except: pass
        st.rerun()

# =========================
# ORDER FORM
# =========================
with st.expander("📦 Place a Quick Order"):
    with st.form("order_form"):
        c1, c2 = st.columns(2)
        name = c1.text_input("Name")
        phone = c2.text_input("Phone")
        prod = st.selectbox("Product", ["UltraTech Paper Bag", "UltraTech Weather Plus", "Weather Pro Waterproofing"])
        qty = st.number_input("Quantity", min_value=1)
        
        if st.form_submit_button("Submit Order"):
            order_text = f"New Order: {qty}x {prod} for {name} ({phone})"
            st.session_state.orders.append(order_text)
            st.success("Order request saved! We will contact you for payment.")

# =========================
# FOOTER
# =========================
st.markdown("---")
st.caption("© 2024 Shikhar Traders. Authorized UltraTech Cement Partner.")

