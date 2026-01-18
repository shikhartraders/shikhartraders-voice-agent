import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime
from urllib.parse import quote

# -----------------------------
# PREMIUM UI & BRANDING CLEANUP
# -----------------------------
st.set_page_config(
    page_title="Shikhar Traders AI",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="collapsed" # Hide sidebar by default for a clean look
)

# Custom CSS to hide Streamlit header, footer, and menu
st.markdown("""
    <style>
        /* Hide Streamlit Branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Premium Background & Glassmorphism */
        .stApp {
            background: radial-gradient(circle at 10% 10%, rgba(0, 245, 255, 0.05), transparent 30%),
                        linear-gradient(135deg, #05060b 0%, #0a0b1e 100%);
            color: #ffffff;
        }
        
        /* Clean Chat Bubbles */
        .user-bubble {
            background: rgba(0, 245, 255, 0.1);
            border: 1px solid rgba(0, 245, 255, 0.2);
            padding: 1rem;
            border-radius: 15px 15px 0 15px;
            margin: 10px 0;
            margin-left: 20%;
            text-align: right;
        }
        
        .agent-bubble {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 1rem;
            border-radius: 15px 15px 15px 0;
            margin: 10px 0;
            margin-right: 20%;
        }

        .premium-card {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 20px;
            backdrop-filter: blur(10px);
        }
        
        .glow-text {
            font-weight: 800;
            background: linear-gradient(90deg, #00f5ff, #a855f7);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
    </style>
""", unsafe_allow_html=True)

# -----------------------------
# CONFIGURATION
# -----------------------------
# Directly set your configurations here for the integrated app
OPENAI_API_KEY = "your-api-key-here" # Replace with your key
CONTACT_NUMBER = "+917355969446"

# -----------------------------
# CORE AI LOGIC
# -----------------------------
def get_ai_response(messages):
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    system_prompt = "You are the Shikhar Traders AI Sales Agent. Be professional and helpful. Focus on UltraTech products."
    
    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "system", "content": system_prompt}] + messages,
        "temperature": 0.7
    }
    
    try:
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        return response.json()['choices'][0]['message']['content']
    except:
        return "I'm having trouble connecting. Please call Shikhar Traders directly at 07355969446."

# -----------------------------
# MAIN APP INTERFACE
# -----------------------------
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("<h1 class='glow-text'>Shikhar Traders AI</h1>", unsafe_allow_html=True)
    st.caption("Official UltraTech Sales Assistant • Online")

with col2:
    st.markdown(f"""
    <div class='premium-card'>
        📞 <b>Support:</b> {CONTACT_NUMBER}<br>
        📍 <b>Location:</b> Deoria, UP
    </div>
    """, unsafe_allow_html=True)

# Chat Session History
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Container for chat display
chat_display = st.container()

with chat_display:
    for message in st.session_state.chat_history:
        div_class = "user-bubble" if message["role"] == "user" else "agent-bubble"
        st.markdown(f"<div class='{div_class}'>{message['content']}</div>", unsafe_allow_html=True)

# User Input
user_query = st.chat_input("Ask about UltraTech cement or book an order...")

if user_query:
    # Add user message
    st.session_state.chat_history.append({"role": "user", "content": user_query})
    
    # Get AI response
    with st.spinner("Processing..."):
        ai_reply = get_ai_response(st.session_state.chat_history)
        st.session_state.chat_history.append({"role": "assistant", "content": ai_reply})
    
    # Refresh app to show new messages
    st.rerun()

# -----------------------------
# QUICK WHATSAPP ORDER
# -----------------------------
st.markdown("---")
with st.expander("🚀 Instant Order Booking"):
    with st.form("quick_order"):
        c1, c2 = st.columns(2)
        u_name = c1.text_input("Customer Name")
        u_qty = c2.text_input("Quantity")
        u_prod = st.selectbox("Product", ["UltraTech Cement", "Weather Pro", "Iron Rings"])
        
        if st.form_submit_button("Book via WhatsApp"):
            msg = f"Order Inquiry:\nName: {u_name}\nProduct: {u_prod}\nQty: {u_qty}"
            wa_link = f"https://wa.me/{CONTACT_NUMBER.replace('+', '')}?text={quote(msg)}"
            st.markdown(f"✅ [Click here to send details to Shikhar Traders]({wa_link})")
