import streamlit as st
import requests
import time
from datetime import datetime
from urllib.parse import quote

# -----------------------------
# TOTAL BRANDING CLEANUP (No Docs, No Sidebar)
# -----------------------------
st.set_page_config(
    page_title="Shikhar Traders AI",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Deep CSS to enforce Premium Glassmorphism and Hide all Streamlit UI elements
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
        
        /* Remove Streamlit Elements */
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        footer {visibility: hidden;}
        [data-testid="stSidebar"] {display: none;}
        [data-testid="collapsedControl"] {display: none;}
        .stDeployButton {display:none;}
        
        /* Premium Background */
        .stApp {
            background: radial-gradient(circle at 20% 20%, rgba(0, 245, 255, 0.08), transparent 40%),
                        radial-gradient(circle at 80% 80%, rgba(168, 85, 247, 0.1), transparent 40%),
                        #05060b;
            color: #ffffff;
            font-family: 'Inter', sans-serif;
        }

        /* Glassmorphism Cards */
        .glass-panel {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 20px;
            backdrop-filter: blur(15px);
            margin-bottom: 20px;
        }

        /* Chat Bubbles */
        .chat-bubble {
            padding: 15px 20px;
            border-radius: 20px;
            margin: 10px 0;
            max-width: 80%;
            font-size: 16px;
            line-height: 1.5;
        }
        .agent-bubble {
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-bottom-left-radius: 4px;
        }
        .user-bubble {
            background: linear-gradient(135deg, rgba(0, 245, 255, 0.2), rgba(168, 85, 247, 0.2));
            border: 1px solid rgba(0, 245, 255, 0.3);
            border-bottom-right-radius: 4px;
            margin-left: auto;
            text-align: right;
        }

        /* Title Styling */
        .brand-text {
            font-weight: 900;
            background: linear-gradient(90deg, #00f5ff, #a855f7, #00ff88);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 3.5rem;
            margin: 0;
        }
    </style>
""", unsafe_allow_html=True)

# -----------------------------
# CONFIGURATION (Hardcoded for your app)
# -----------------------------
OPENAI_KEY = "YOUR_OPENAI_API_KEY"  # Enter your API Key here
PHONE_MAIN = "07355969446"
PHONE_SEC = "09450805567"

# -----------------------------
# AI ENGINE
# -----------------------------
def get_ai_response(messages):
    headers = {"Authorization": f"Bearer {OPENAI_KEY}"}
    system_data = """You are the official Shikhar Traders AI. 
    Product Catalog:
    - UltraTech Paper Bag Cement: ₹405
    - UltraTech Super: ₹415
    - UltraTech Weather Plus: ₹420
    - Weather Pro Waterproofing: 1L(₹175), 5L(₹750), 10L(₹1450), 20L(₹2500)
    - Iron Ring: ₹12 (Bulk 120+).
    Guidelines: Polite, fast, only UltraTech. Ask customers to confirm stock via WhatsApp."""
    
    try:
        r = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "system", "content": system_data}] + messages
            },
            timeout=10
        )
        return r.json()['choices'][0]['message']['content']
    except:
        return f"Service currently busy. Please call us at {PHONE_MAIN}."

def speak_text(text):
    headers = {"Authorization": f"Bearer {OPENAI_KEY}"}
    try:
        r = requests.post(
            "https://api.openai.com/v1/audio/speech",
            headers=headers,
            json={"model": "gpt-4o-mini-tts", "voice": "coral", "input": text},
            timeout=10
        )
        return r.content
    except:
        return None

# -----------------------------
# MAIN UI
# -----------------------------
st.markdown("<h1 class='brand-text'>Shikhar Traders</h1>", unsafe_allow_html=True)
st.markdown("### Premium UltraTech Sales Agent")

# Contact Dashboard
st.markdown(f"""
<div class='glass-panel'>
    <div style='display: flex; justify-content: space-between; align-items: center;'>
        <div>📞 <b>Hotline:</b> {PHONE_MAIN} | {PHONE_SEC}</div>
        <div>🌐 <b>Website:</b> <a href='https://shikhartradersbs.odoo.com/' style='color:#00f5ff;'>Official Site</a></div>
        <div>📍 <b>Status:</b> <span style='color:#00ff88;'>● Active</span></div>
    </div>
</div>
""", unsafe_allow_html=True)

# Session State for Messages
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display Chat
for msg in st.session_state.messages:
    style = "user-bubble" if msg["role"] == "user" else "agent-bubble"
    st.markdown(f"<div class='chat-bubble {style}'>{msg['content']}</div>", unsafe_allow_html=True)

# User Chat Input
user_input = st.chat_input("Ask about UltraTech cement prices or booking...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.spinner("AI is thinking..."):
        reply = get_ai_response(st.session_state.messages)
        st.session_state.messages.append({"role": "assistant", "content": reply})
        
        # Audio Reply
        audio = speak_text(reply)
        if audio:
            st.audio(audio, format="audio/mp3", autoplay=True)
    st.rerun()

# -----------------------------
# ORDER FORM (Instant WhatsApp)
# -----------------------------
st.write("---")
with st.expander("📦 Quick Order Inquiry"):
    with st.form("whatsapp_order"):
        c1, c2 = st.columns(2)
        c_name = c1.text_input("Your Name")
        c_prod = c2.selectbox("Product", ["UltraTech Cement", "Weather Pro", "Iron Rings"])
        c_qty = st.text_input("Quantity Required")
        
        if st.form_submit_button("Send to WhatsApp"):
            msg = f"Order Inquiry:\nName: {c_name}\nProduct: {c_prod}\nQty: {c_qty}"
            wa_link = f"https://wa.me/91{PHONE_MAIN[1:]}?text={quote(msg)}"
            st.markdown(f"👉 [Click here to send to WhatsApp]({wa_link})")
