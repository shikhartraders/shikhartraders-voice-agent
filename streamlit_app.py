import streamlit as st
import requests
from openai import OpenAI
import urllib.parse

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
.stApp {
    background: radial-gradient(circle at 10% 10%, rgba(0,255,255,0.10), transparent 45%),
                radial-gradient(circle at 90% 20%, rgba(255,0,255,0.12), transparent 45%),
                radial-gradient(circle at 40% 90%, rgba(0,255,140,0.10), transparent 50%),
                linear-gradient(135deg, #05060a 0%, #060a12 50%, #05060a 100%);
}
.glass {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 18px;
    padding: 18px;
    box-shadow: 0 12px 40px rgba(0,0,0,0.45);
}
.title-grad {
    font-size: 42px;
    font-weight: 900;
    line-height: 1.05;
    background: linear-gradient(90deg, #00E5FF, #8A2BE2, #FF2BD6, #00FF9A);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.sub {
    opacity: 0.88;
    font-size: 14px;
}
.pill {
    display:inline-block;
    padding:6px 10px;
    margin-right:8px;
    border-radius:999px;
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.12);
    font-size:12px;
    opacity:0.95;
}
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
.stChatInput textarea {
    border-radius: 16px !important;
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.14) !important;
}
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
""",
    unsafe_allow_html=True
)

# ----------------------------
# CONSTANTS (Shikhar Traders)
# ----------------------------
WHATSAPP_NUMBER = "917355969446"  # +91 7355969446 (without +)
CALL_1 = "07355969446"
CALL_2 = "09450805567"
EMAIL = "shikhartraders@zohomail.com"
MAPS_URL = "https://maps.app.goo.gl/22dertGs5oZxrWMb8"
WEBSITE_URL = "https://shikhartradersbs.odoo.com/"

DEFAULT_DOCS_RAW = "https://raw.githubusercontent.com/shikhartraders/shikhartraders-voice-agent/main/shikhartraders_support_docs_all_in_one.md"

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
Your job: help customers quickly with product price, availability, order booking, delivery guidance, and FAQs.

STRICT RULES:
- Only sell UltraTech products listed in docs.
- Prices are approximate.
- If customer asks final price, discount, stock confirmation, delivery charges, payment confirmation -> ask them to contact WhatsApp/Call/Email.
- If user speaks Hindi -> reply in Hindi.
- If user speaks Hinglish -> reply in Hinglish.
- If user speaks English -> reply in English.
- Keep replies short, clear, and sales-friendly.
- Always include next step CTA when needed.

Business contact:
- Call/WhatsApp: {CALL_1}, {CALL_2}
- Email: {EMAIL}
- Store Location: {MAPS_URL}
- Website: {WEBSITE_URL}

Knowledge Base (Docs):
----------------------
{docs_text}
----------------------
"""


def ask_ai(client: OpenAI, system_prompt: str, chat_history: list, user_message: str) -> str:
    messages = [{"role": "system", "content": system_prompt}]
    for m in chat_history[-10:]:
        messages.append(m)
    messages.append({"role": "user", "content": user_message})

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.2,
        max_tokens=280,
    )
    return resp.choices[0].message.content.strip()


def make_whatsapp_link(text: str) -> str:
    encoded = urllib.parse.quote(text)
    return f"https://wa.me/{WHATSAPP_NUMBER}?text={encoded}"


def tts_audio_bytes(client: OpenAI, text: str, voice: str = "coral") -> bytes:
    """
    Uses OpenAI TTS.
    Streamlit can play mp3 bytes using st.audio.
    """
    # Keep voice short and safe
    text = text.strip()
    if len(text) > 1200:
        text = text[:1200] + "..."

    audio_resp = client.audio.speech.create(
        model="gpt-4o-mini-tts",
        voice=voice,
        input=text
    )
    return audio_resp.read()


# ----------------------------
# SESSION STATE
# ----------------------------
if "docs_text" not in st.session_state:
    st.session_state.docs_text = ""
if "system_prompt" not in st.session_state:
    st.session_state.system_prompt = ""
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_answer" not in st.session_state:
    st.session_state.last_answer = ""
if "last_audio" not in st.session_state:
    st.session_state.last_audio = None

# ----------------------------
# SIDEBAR CONFIG
# ----------------------------
with st.sidebar:
    st.markdown("## 🔑 Configuration")

    openai_key = st.text_input("OpenAI API Key", type="password")

    docs_url = st.text_input(
        "Documentation (RAW Markdown URL)",
        value=DEFAULT_DOCS_RAW
    )

    st.markdown("---")
    st.markdown("### 🎙️ Voice Settings")
    enable_voice = st.toggle("Enable Voice Reply (TTS)", value=True)
    tts_voice = st.selectbox("Select Voice", ["coral", "alloy", "verse", "sage"], index=0)

    st.markdown("---")
    st.markdown("### ⚡ Speed Settings")
    ultra_fast = st.toggle("Ultra Fast Replies", value=True)

    st.markdown("---")
    st.markdown("### 🧹 Controls")
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.session_state.last_answer = ""
        st.session_state.last_audio = None
        st.rerun()

# ----------------------------
# LOAD DOCS ONCE
# ----------------------------
if docs_url and (st.session_state.docs_text == ""):
    with st.spinner("📄 Loading documentation..."):
        st.session_state.docs_text = download_docs(docs_url)
        st.session_state.system_prompt = build_system_prompt(st.session_state.docs_text)

# ----------------------------
# BLOCKERS
# ----------------------------
if not openai_key:
    st.info("👈 Add your OpenAI API Key in sidebar to start.")
    st.stop()

if not st.session_state.docs_text:
    st.error("❌ Documentation not loaded. Please check RAW markdown URL.")
    st.stop()

client = OpenAI(api_key=openai_key)

# ----------------------------
# HEADER
# ----------------------------
left, right = st.columns([1.35, 1])

with left:
    st.markdown(
        f"""
<div class="glass">
  <div class="title-grad">Shikhar Traders Voice Agent</div>
  <div class="sub">Premium AI support • UltraTech Only • Fast answers • Order booking • Voice replies</div>
  <br>
  <span class="pill">📞 {CALL_1}</span>
  <span class="pill">📞 {CALL_2}</span>
  <span class="pill">✉️ {EMAIL}</span>
  <br><br>
  <span class="pill">📍 Store Location</span>
  <span class="pill">🛒 Website</span>
</div>
""",
        unsafe_allow_html=True
    )

with right:
    st.markdown(
        """
<div class="glass">
  <b>🧱 Products (Approx Prices)</b><br><br>
  <b>Cement</b><br>
  • UltraTech Paper Bag ~ ₹405<br>
  • UltraTech Super ~ ₹415<br>
  • UltraTech Weather Plus ~ ₹420<br><br>
  <b>Waterproofing (Weather Pro)</b><br>
  • 1L ~ ₹175 • 5L ~ ₹750<br>
  • 10L ~ ₹1450 • 20L ~ ₹2500<br><br>
  <b>Iron Ring</b><br>
  • ₹12/pc (Bulk 120+ online)<br>
</div>
""",
        unsafe_allow_html=True
    )

st.write("")

# ----------------------------
# QUICK CONTACT BUTTONS
# ----------------------------
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.link_button("📍 Open Store Location", MAPS_URL)
with c2:
    st.link_button("🛒 Visit Website", WEBSITE_URL)
with c3:
    st.link_button("💬 WhatsApp Now", make_whatsapp_link("Hi Shikhar Traders, I want to place an order."))
with c4:
    st.link_button("✉️ Email", f"mailto:{EMAIL}")

st.write("")

# ----------------------------
# QUICK ACTIONS
# ----------------------------
st.markdown("### ⚡ Quick Actions (Tap)")
qa_cols = st.columns(6)
quick_questions = [
    "UltraTech Paper Bag price?",
    "UltraTech Super price?",
    "Weather Pro 5 litre price?",
    "Iron Ring bulk order rule?",
    "How to book an order?",
    "Store location & timing?"
]

for i, q in enumerate(quick_questions):
    with qa_cols[i]:
        if st.button(q):
            st.session_state.messages.append({"role": "user", "content": q})

st.write("")

# ----------------------------
# ORDER BOOKING FORM (Premium)
# ----------------------------
st.markdown("## 🧾 Quick Order Booking Form")

with st.expander("✅ Open Order Form (Tap)", expanded=True):
    f1, f2 = st.columns(2)

    with f1:
        customer_name = st.text_input("Customer Name")
        customer_mobile = st.text_input("Mobile Number (WhatsApp preferred)")
        delivery_city = st.text_input("Delivery City / Area")
        delivery_address = st.text_area("Delivery Address (Optional)", height=80)

    with f2:
        product_type = st.selectbox(
            "Select Product",
            [
                "UltraTech Paper Bag Cement",
                "UltraTech Super Cement",
                "UltraTech Weather Plus Cement",
                "Weather Pro Waterproofing 1L",
                "Weather Pro Waterproofing 5L",
                "Weather Pro Waterproofing 10L",
                "Weather Pro Waterproofing 20L",
                "Iron Ring (Bulk Order 120+)"
            ],
            index=0
        )

        quantity = st.number_input("Quantity", min_value=1, max_value=5000, value=10)
        delivery_required = st.selectbox("Delivery Required?", ["Yes", "No"], index=0)
        payment_mode = st.selectbox("Payment Mode", ["Cash", "UPI", "Bank Transfer", "Not Sure"], index=0)

    note = st.text_area("Extra Notes (Optional)", placeholder="Example: urgent delivery / best price / confirm stock", height=80)

    order_message = f"""
New Order Request - Shikhar Traders

Customer Name: {customer_name}
Mobile: {customer_mobile}
Product: {product_type}
Quantity: {quantity}
Delivery Required: {delivery_required}
City/Area: {delivery_city}
Address: {delivery_address}
Payment Mode: {payment_mode}
Notes: {note}

Please confirm latest price, stock availability and delivery charges.
""".strip()

    b1, b2, b3 = st.columns(3)
    with b1:
        st.link_button("💬 Send Order on WhatsApp", make_whatsapp_link(order_message))
    with b2:
        st.link_button("✉️ Send Order on Email", f"mailto:{EMAIL}?subject=Order%20Request%20-%20Shikhar%20Traders&body={urllib.parse.quote(order_message)}")
    with b3:
        st.info("📞 For final price & payment confirmation: Call/WhatsApp us.")

st.write("")

# ----------------------------
# CHAT SECTION
# ----------------------------
st.markdown("## 💬 Chat Support (Like ChatGPT)")

for m in st.session_state.messages:
    with st.chat_message("user" if m["role"] == "user" else "assistant"):
        st.markdown(m["content"])

user_input = st.chat_input("Ask about UltraTech products / order / delivery / payment...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

# ----------------------------
# AI RESPONSE + VOICE
# ----------------------------
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    with st.chat_message("assistant"):
        with st.spinner("⚡ Thinking..."):
            try:
                system_prompt = st.session_state.system_prompt

                if ultra_fast:
                    system_prompt += "\nReply in maximum 4 lines. Be direct and helpful."

                answer = ask_ai(
                    client=client,
                    system_prompt=system_prompt,
                    chat_history=st.session_state.messages,
                    user_message=st.session_state.messages[-1]["content"],
                )

                st.session_state.last_answer = answer
                st.markdown(answer)

                # Optional voice reply
                if enable_voice:
                    try:
                        audio_bytes = tts_audio_bytes(client, answer, voice=tts_voice)
                        st.session_state.last_audio = audio_bytes
                        st.audio(audio_bytes, format="audio/mp3")
                    except Exception as e:
                        st.warning("⚠️ Voice reply failed (TTS). You can still use text chat.")

                st.session_state.messages.append({"role": "assistant", "content": answer})

            except Exception as e:
                st.error(f"❌ Error: {e}")

# ----------------------------
# EXTRA PREMIUM FOOTER
# ----------------------------
st.write("")
st.markdown(
    f"""
<div class="glass">
<b>📌 Payment & Final Confirmation</b><br>
Prices shown are approximate. For final price, stock confirmation, delivery charges and payment confirmation please contact:<br>
📞 {CALL_1}, {CALL_2} | ✉️ {EMAIL}<br><br>
<b>⭐ Shikhar Traders (UltraTech Only)</b><br>
📍 Store Location: {MAPS_URL}<br>
🛒 Website: {WEBSITE_URL}
</div>
""",
    unsafe_allow_html=True
)