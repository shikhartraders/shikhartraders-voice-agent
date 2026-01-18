import streamlit as st
import requests
from openai import OpenAI

# ----------------------------
# PAGE CONFIG
# ----------------------------
st.set_page_config(
    page_title="Shikhar Traders Voice Agent",
    page_icon="🎙️",
    layout="wide",
)

# ----------------------------
# PREMIUM UI CSS
# ----------------------------
st.markdown(
    """
<style>
/* Background */
.stApp {
    background: radial-gradient(circle at 10% 10%, rgba(0,255,255,0.10), transparent 45%),
                radial-gradient(circle at 90% 20%, rgba(255,0,255,0.12), transparent 45%),
                radial-gradient(circle at 40% 90%, rgba(0,255,140,0.10), transparent 50%),
                linear-gradient(135deg, #05060a 0%, #060a12 50%, #05060a 100%);
}

/* Glass cards */
.glass {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 18px;
    padding: 18px;
    box-shadow: 0 12px 40px rgba(0,0,0,0.45);
}

/* Title gradient */
.title-grad {
    font-size: 42px;
    font-weight: 800;
    line-height: 1.1;
    background: linear-gradient(90deg, #00E5FF, #8A2BE2, #FF2BD6, #00FF9A);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* Subtitle */
.sub {
    opacity: 0.85;
    font-size: 14px;
}

/* Buttons */
.stButton button {
    border-radius: 14px !important;
    padding: 10px 14px !important;
    border: 1px solid rgba(255,255,255,0.16) !important;
    background: rgba(255,255,255,0.06) !important;
    color: white !important;
    transition: 0.2s ease-in-out;
}
.stButton button:hover {
    transform: translateY(-2px);
    background: rgba(255,255,255,0.10) !important;
}

/* Chat input */
.stChatInput textarea {
    border-radius: 16px !important;
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.14) !important;
}

/* Hide Streamlit menu */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
""",
    unsafe_allow_html=True
)

# ----------------------------
# HELPERS
# ----------------------------
def download_docs(raw_url: str) -> str:
    try:
        r = requests.get(raw_url, timeout=12)
        if r.status_code != 200:
            return ""
        return r.text.strip()
    except:
        return ""


def build_system_prompt(docs_text: str) -> str:
    return f"""
You are "Shikhar Traders Voice Agent" for Shikhar Traders (UltraTech products only).
You must answer in a friendly, fast, professional style.

Rules:
- Always be helpful and short.
- If user asks final price, delivery, stock, payment confirmation -> tell them to contact on WhatsApp/Call or Email.
- Never invent products that are not in the docs.
- Prices are approximate.
- Prefer Hinglish if user speaks Hinglish.
- If user speaks Hindi, reply in Hindi.
- If user speaks English, reply in English.

Business contact:
- Call/WhatsApp: 07355969446, 09450805567
- Email: shikhartraders@zohomail.com
- Store Location: https://maps.app.goo.gl/22dertGs5oZxrWMb8
- Website: https://shikhartradersbs.odoo.com/

Knowledge Base (Docs):
----------------------
{docs_text}
----------------------
"""


def ask_ai(client: OpenAI, system_prompt: str, chat_history: list, user_message: str) -> str:
    # keep it fast and cheap
    messages = [{"role": "system", "content": system_prompt}]

    # last 8 messages only (speed)
    for m in chat_history[-8:]:
        messages.append(m)

    messages.append({"role": "user", "content": user_message})

    # Use a fast model (works with most OpenAI accounts)
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.2,
        max_tokens=250,
    )
    return resp.choices[0].message.content.strip()


# ----------------------------
# SIDEBAR CONFIG
# ----------------------------
with st.sidebar:
    st.markdown("## 🔑 Configuration")

    openai_key = st.text_input("OpenAI API Key", type="password")
    docs_url = st.text_input(
        "Documentation (RAW Markdown URL)",
        value="https://raw.githubusercontent.com/shikhartraders/shikhartraders-voice-agent/main/shikhartraders_support_docs_all_in_one.md"
    )

    st.markdown("---")
    st.markdown("### ⚡ Quick Speed Mode")
    speed_mode = st.toggle("Ultra Fast Mode (recommended)", value=True)

    st.markdown("---")
    st.markdown("### 🧹 Controls")
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.session_state.docs_text = ""
        st.session_state.system_prompt = ""
        st.rerun()

# ----------------------------
# MAIN HEADER
# ----------------------------
colA, colB = st.columns([1.2, 1])
with colA:
    st.markdown(
        """
<div class="glass">
  <div class="title-grad">Shikhar Traders Voice Agent</div>
  <div class="sub">UltraTech Only • Fast customer support • Order help • Delivery guidance • FAQs</div>
  <br>
  <div class="sub">📞 07355969446 • 09450805567 &nbsp;&nbsp; ✉️ shikhartraders@zohomail.com</div>
</div>
""",
        unsafe_allow_html=True
    )

with colB:
    st.markdown(
        """
<div class="glass">
  <b>🛒 Products (Approx)</b><br><br>
  🧱 UltraTech Paper Bag ~ ₹405<br>
  🧱 UltraTech Super ~ ₹415<br>
  🧱 UltraTech Weather Plus ~ ₹420<br><br>
  💧 Weather Pro 1L ~ ₹175 | 5L ~ ₹750 | 10L ~ ₹1450 | 20L ~ ₹2500<br>
  🔩 Iron Ring ~ ₹12/pc (bulk 120+ online)<br>
</div>
""",
        unsafe_allow_html=True
    )

st.write("")

# ----------------------------
# LOAD DOCS ONCE (FAST CACHE)
# ----------------------------
if "docs_text" not in st.session_state:
    st.session_state.docs_text = ""

if "system_prompt" not in st.session_state:
    st.session_state.system_prompt = ""

if "messages" not in st.session_state:
    st.session_state.messages = []

# Auto load docs when URL is present
if docs_url and (st.session_state.docs_text == ""):
    with st.spinner("📄 Loading documentation..."):
        st.session_state.docs_text = download_docs(docs_url)
        st.session_state.system_prompt = build_system_prompt(st.session_state.docs_text)

if not openai_key:
    st.info("👈 Please add your OpenAI API Key in sidebar to start.")
    st.stop()

if not st.session_state.docs_text:
    st.error("❌ Documentation not loaded. Please check your RAW markdown URL.")
    st.stop()

# ----------------------------
# QUICK ACTIONS
# ----------------------------
st.markdown("### ⚡ Quick Actions (Tap)")
qa_cols = st.columns(5)
quick_questions = [
    "UltraTech Paper Bag price?",
    "Weather Pro 5 litre price?",
    "Iron Ring bulk order rule?",
    "Book an order (cement + delivery)",
    "Store location & timing?"
]

for i, q in enumerate(quick_questions):
    with qa_cols[i]:
        if st.button(q):
            st.session_state.messages.append({"role": "user", "content": q})

# ----------------------------
# CHAT UI
# ----------------------------
for m in st.session_state.messages:
    with st.chat_message("user" if m["role"] == "user" else "assistant"):
        st.markdown(m["content"])

user_input = st.chat_input("Ask about UltraTech cement / waterproofing / delivery / payment...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    with st.chat_message("assistant"):
        with st.spinner("⚡ Thinking..."):
            try:
                client = OpenAI(api_key=openai_key)

                # Ultra Fast Mode = shorter answer
                if speed_mode:
                    extra = "\nKeep replies under 4 lines unless user asks details."
                    system_prompt = st.session_state.system_prompt + extra
                else:
                    system_prompt = st.session_state.system_prompt

                answer = ask_ai(client, system_prompt, st.session_state.messages, st.session_state.messages[-1]["content"])
                st.markdown(answer)

                st.session_state.messages.append({"role": "assistant", "content": answer})

            except Exception as e:
                st.error(f"❌ Error: {e}")