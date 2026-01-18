import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime
from urllib.parse import quote

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(
    page_title="Shikhar Traders Premium",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------
# PREMIUM UI CSS
# -----------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
    
    html, body, [class*="st-"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background: radial-gradient(circle at 20% 20%, rgba(0, 245, 255, 0.05), transparent 40%),
                    radial-gradient(circle at 80% 80%, rgba(168, 85, 247, 0.08), transparent 40%),
                    #0a0b10;
        color: #e0e0e0;
    }

    .glow-title {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(90deg, #00f5ff, #a855f7, #00ff88);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }

    .glass-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 20px;
        padding: 25px;
        backdrop-filter: blur(12px);
        margin-bottom: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }

    .stButton>button {
        width: 100%;
        border-radius: 12px !important;
        background: linear-gradient(135deg, rgba(0, 245, 255, 0.1), rgba(168, 85, 247, 0.1)) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        transition: all 0.3s ease !important;
        font-weight: 600 !important;
    }

    .stButton>button:hover {
        border: 1px solid #00f5ff !important;
        background: rgba(0, 245, 255, 0.15) !important;
        transform: translateY(-2px);
    }

    .chat-bubble-user {
        background: rgba(168, 85, 247, 0.1);
        border: 1px solid rgba(168, 85, 247, 0.2);
        padding: 15px;
        border-radius: 15px 15px 0 15px;
        margin: 10px 0;
        text-align: right;
    }

    .chat-bubble-agent {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 15px;
        border-radius: 15px 15px 15px 0;
        margin: 10px 0;
    }

    .status-badge {
        padding: 4px 12px;
        border-radius: 50px;
        font-size: 0.8rem;
        background: rgba(0, 255, 136, 0.1);
        color: #00ff88;
        border: 1px solid rgba(0, 255, 136, 0.2);
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------
# BUSINESS LOGIC
# -----------------------------
BUSINESS = {
    "name": "Shikhar Traders",
    "phones": ["+917355969446", "+919450805567"],
    "email": "shikhartraders@zohomail.com",
    "website": "https://shikhartradersbs.odoo.com/",
    "kb": """You are the official Shikhar Traders AI. We only sell UltraTech products.
    Prices (Approx): 
    - Paper Bag: ₹405
    - Super: ₹415
    - Weather Plus: ₹420
    - Weather Pro (Waterproofing): 1L: ₹175, 5L: ₹750, 10L: ₹1450, 20L: ₹2500
    - Iron Ring: ₹12 (Bulk 120+ only).
    Note: Always tell users that stock and final price must be confirmed via WhatsApp/Call."""
}

# -----------------------------
# HELPER FUNCTIONS
# -----------------------------
def get_ai_response(api_key, messages, lang):
    headers = {"Authorization": f"Bearer {api_key}"}
    system_msg = f"Act as a helpful sales agent for Shikhar Traders. Answer in {lang}. Be concise."
    
    combined_messages = [{"role": "system", "content": system_msg + BUSINESS['kb']}] + messages
    
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json={
                "model": "gpt-4o-mini",
                "messages": combined_messages,
                "temperature": 0.7
            },
            timeout=15
        )
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"Error: {str(e)}"

def text_to_speech(api_key, text, voice_style):
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        response = requests.post(
            "https://api.openai.com/v1/audio/speech",
            headers=headers,
            json={"model": "tts-1", "voice": voice_style, "input": text},
            timeout=20
        )
        return response.content
    except:
        return None

# -----------------------------
# SIDEBAR
# -----------------------------
with st.sidebar:
    st.title("⚙️ Settings")
    api_key = st.text_input("OpenAI API Key", type="password")
    lang = st.selectbox("Language", ["English", "Hindi", "Hinglish"])
    voice_opt = st.selectbox("Voice Tone", ["alloy", "shimmer", "nova", "echo"])
    enable_voice = st.toggle("Enable Voice Output", value=True)
    
    st.divider()
    admin_pin = st.text_input("Admin Access", type="password")

# -----------------------------
# MAIN UI
# -----------------------------
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown(f"<div class='glow-title'>{BUSINESS['name']}</div>", unsafe_allow_html=True)
    st.markdown("<span class='status-badge'>● AI Agent Online</span>", unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class='glass-card' style='padding: 15px;'>
        <b>📞 Support:</b> {BUSINESS['phones'][0]}<br>
        <b>🌐 Web:</b> <a href='{BUSINESS['website']}' style='color:#00f5ff;'>Visit Site</a>
    </div>
    """, unsafe_allow_html=True)

# -----------------------------
# QUICK ACTIONS
# -----------------------------
st.markdown("### ⚡ Quick Queries")
q_cols = st.columns(4)
queries = ["Today's Cement Prices", "Waterproofing Range", "Bulk Iron Rings", "Delivery Terms"]

for i, q in enumerate(queries):
    if q_cols[i % 4].button(q):
        st.session_state.pending_query = q

# -----------------------------
# CHAT INTERFACE
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

chat_container = st.container()

with chat_container:
    for m in st.session_state.messages:
        role_class = "chat-bubble-user" if m["role"] == "user" else "chat-bubble-agent"
        st.markdown(f"<div class='{role_class}'>{m['content']}</div>", unsafe_allow_html=True)

# -----------------------------
# INPUT & PROCESSING
# -----------------------------
user_input = st.chat_input("Ask about UltraTech products...")
if "pending_query" in st.session_state:
    user_input = st.session_state.pop("pending_query")

if user_input:
    if not api_key:
        st.error("Please enter your OpenAI API Key in the sidebar.")
    else:
        # Display User Message
        st.session_state.messages.append({"role": "user", "content": user_input})
        with chat_container:
            st.markdown(f"<div class='chat-bubble-user'>{user_input}</div>", unsafe_allow_html=True)

        # Get AI Response
        with st.spinner("Consulting Shikhar Traders..."):
            ai_reply = get_ai_response(api_key, st.session_state.messages, lang)
            st.session_state.messages.append({"role": "assistant", "content": ai_reply})
            
            with chat_container:
                st.markdown(f"<div class='chat-bubble-agent'>{ai_reply}</div>", unsafe_allow_html=True)
                
                if enable_voice:
                    audio_data = text_to_speech(api_key, ai_reply, voice_opt)
                    if audio_data:
                        st.audio(audio_data, format="audio/mp3", autoplay=True)

# -----------------------------
# ORDER FORM
# -----------------------------
with st.expander("📦 Quick Order / Inquiry Form"):
    with st.form("order_form"):
        c1, c2 = st.columns(2)
        name = c1.text_input("Name")
        phone = c2.text_input("Phone Number")
        prod = st.selectbox("Product", ["UltraTech Cement", "Weather Pro", "Iron Rings"])
        qty = st.number_input("Quantity", min_value=1)
        
        if st.form_submit_button("Generate WhatsApp Link"):
            msg = f"Hi Shikhar Traders, I'm {name}. I want to inquire about {qty} units of {prod}."
            wa_url = f"https://wa.me/{BUSINESS['phones'][0].replace('+', '')}?text={quote(msg)}"
            st.markdown(f"👉 [Click to send WhatsApp]({wa_url})")

# -----------------------------
# ADMIN PANEL
# -----------------------------
if admin_pin == "1122":
    st.divider()
    st.subheader("📊 Business Analytics")
    st.info("Admin mode active. Chat logs and leads would be displayed here.")
