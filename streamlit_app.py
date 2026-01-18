import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(
    page_title="Shikhar Traders Voice Agent (V6 Premium)",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------
# PREMIUM UI CSS
# -----------------------------
st.markdown("""
<style>
.stApp{
    background:#05060b;
    color:#fff;
}
.bg{
    position:fixed; inset:0; z-index:-5;
    background:
        radial-gradient(circle at 18% 12%, rgba(0,255,255,0.22), transparent 45%),
        radial-gradient(circle at 85% 22%, rgba(168,85,247,0.24), transparent 42%),
        radial-gradient(circle at 55% 95%, rgba(0,255,120,0.18), transparent 50%),
        linear-gradient(120deg, #05060b, #070a14, #05060b);
    animation:bgPulse 10s ease-in-out infinite;
}
@keyframes bgPulse{
    0%{filter:hue-rotate(0deg) brightness(1); transform:scale(1);}
    50%{filter:hue-rotate(25deg) brightness(1.15); transform:scale(1.02);}
    100%{filter:hue-rotate(0deg) brightness(1); transform:scale(1);}
}
.card{
    border-radius:22px;
    padding:18px;
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.12);
    box-shadow: 0 22px 70px rgba(0,0,0,0.48);
    backdrop-filter: blur(16px);
}
.glow-title{
    font-size: 44px;
    font-weight: 950;
    background: linear-gradient(90deg, #00f5ff, #a855f7, #ff4fd8, #00ff88);
    -webkit-background-clip:text;
    -webkit-text-fill-color:transparent;
}
.badge{
    display:inline-block;
    padding: 6px 10px;
    border-radius: 999px;
    font-weight: 950;
    font-size: 12px;
    border: 1px solid rgba(255,255,255,0.10);
    background: rgba(255,255,255,0.06);
}
.chatbox{
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 18px;
    padding: 14px 16px;
    margin: 10px 0px;
    backdrop-filter: blur(14px);
}
</style>
<div class="bg"></div>
""", unsafe_allow_html=True)

# -----------------------------
# BUSINESS DATA
# -----------------------------
BUSINESS = {
    "name": "Shikhar Traders",
    "phones": ["07355969446", "09450805567"],
    "email": "shikhartraders@zohomail.com",
    "maps": "https://maps.app.goo.gl/22dertGs5oZxrWMb8",
    "website": "https://shikhartradersbs.odoo.com/",
    "note": "Prices are approximate. Final price/stock/payment confirmation must be done via call/WhatsApp/email."
}

LOCAL_KB = f"""
You are Shikhar Traders AI Voice Agent (UltraTech Only).
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
- ₹12 per piece (bulk only, online 120+)

RULES:
- Only UltraTech products.
- Final price/stock/payment confirmation on call/WhatsApp/email.
"""

# -----------------------------
# HELPERS
# -----------------------------
def load_docs(raw_url: str) -> str:
    """Fetch documentation markdown from RAW github link."""
    if not raw_url or "raw.githubusercontent.com" not in raw_url:
        return ""
    try:
        r = requests.get(raw_url, timeout=20)
        if r.status_code == 200:
            return r.text
        return ""
    except:
        return ""

def openai_chat(api_key, question, kb_text, lang="English"):
    url = "https://api.openai.com/v1/responses"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    system_prompt = f"""
You are a premium customer support agent for {BUSINESS['name']} (UltraTech only).
Always answer in {lang}.
Be short, clear, and friendly.
If user asks final price/stock/payment confirmation -> ask them to call/WhatsApp {BUSINESS['phones'][0]} / {BUSINESS['phones'][1]} or email {BUSINESS['email']}.
"""

    payload = {
        "model": "gpt-4o-mini",
        "input": [
            {"role": "system", "content": system_prompt.strip()},
            {"role": "user", "content": f"KNOWLEDGE BASE:\n{kb_text}\n\nUSER QUESTION:\n{question}"}
        ],
        "max_output_tokens": 350
    }

    r = requests.post(url, headers=headers, json=payload, timeout=45)
    r.raise_for_status()
    data = r.json()

    out = ""
    for item in data.get("output", []):
        if item.get("type") == "message":
            for c in item.get("content", []):
                if c.get("type") == "output_text":
                    out += c.get("text", "")
    return out.strip() if out.strip() else "Sorry, I couldn't answer. Please try again."

def openai_tts(api_key, text, voice="coral"):
    url = "https://api.openai.com/v1/audio/speech"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": "gpt-4o-mini-tts", "voice": voice, "input": text}
    r = requests.post(url, headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    return r.content

def make_whatsapp_link(phone, message):
    phone_clean = phone.replace(" ", "")
    if phone_clean.startswith("0"):
        phone_clean = phone_clean[1:]
    if not phone_clean.startswith("91"):
        phone_clean = "91" + phone_clean
    msg = requests.utils.quote(message)
    return f"https://wa.me/{phone_clean}?text={msg}"

# -----------------------------
# SESSION
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "orders" not in st.session_state:
    st.session_state.orders = []
if "last_answer" not in st.session_state:
    st.session_state.last_answer = ""
if "docs_text" not in st.session_state:
    st.session_state.docs_text = ""

# -----------------------------
# SIDEBAR CONFIG
# -----------------------------
st.sidebar.markdown("## ⚙️ Configuration")
openai_key = st.sidebar.text_input("OpenAI API Key", value="", type="password")

docs_url = st.sidebar.text_input(
    "Documentation RAW URL",
    value="https://raw.githubusercontent.com/shikhartraders/shikhartraders-voice-agent/main/shikhartraders_support_docs_all_in_one.md"
)

lang = st.sidebar.selectbox("🌍 Language", ["English", "Hinglish", "Hindi"])
voice = st.sidebar.selectbox("🎙️ Voice", ["coral", "alloy", "verse", "sage"])
auto_voice = st.sidebar.toggle("🔊 Auto Voice Reply", value=True)

if st.sidebar.button("📥 Load Documentation"):
    st.session_state.docs_text = load_docs(docs_url)
    if st.session_state.docs_text:
        st.sidebar.success("✅ Documentation loaded!")
    else:
        st.sidebar.error("❌ Docs not loaded. Check RAW URL.")

st.sidebar.markdown("---")
if st.sidebar.button("🧹 Clear Chat"):
    st.session_state.messages = []
    st.session_state.last_answer = ""

# -----------------------------
# HEADER
# -----------------------------
left, right = st.columns([1.7, 1.0])
with left:
    st.markdown(f"<div class='glow-title'>{BUSINESS['name']} Voice Agent</div>", unsafe_allow_html=True)
    st.caption("UltraTech Only • Premium UI • Fast + Stable • Voice Replies")

with right:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown(f"📞 **{BUSINESS['phones'][0]}** | **{BUSINESS['phones'][1]}**")
    st.markdown(f"✉️ **{BUSINESS['email']}**")
    st.markdown(f"📍 [Store Location]({BUSINESS['maps']})")
    st.markdown(f"🌐 [Website]({BUSINESS['website']})")
    st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------
# QUICK ACTIONS
# -----------------------------
st.markdown("<div class='card'>", unsafe_allow_html=True)
st.markdown("### ⚡ Quick Actions")

c1, c2, c3, c4, c5 = st.columns(5)
if c1.button("🧱 Cement Price"):
    st.session_state.messages.append({"role": "user", "content": "Tell me UltraTech cement prices."})
if c2.button("🛡️ Waterproofing"):
    st.session_state.messages.append({"role": "user", "content": "Tell me Weather Pro waterproofing prices and uses."})
if c3.button("🔩 Iron Ring"):
    st.session_state.messages.append({"role": "user", "content": "Iron ring price and bulk order rules?"})
if c4.button("📦 Book Order"):
    st.session_state.messages.append({"role": "user", "content": "I want to book an order. What details do you need?"})
if c5.button("💳 Payment"):
    st.session_state.messages.append({"role": "user", "content": "How can I pay? Confirm payment options."})
st.markdown("</div>", unsafe_allow_html=True)

st.write("")

# -----------------------------
# ORDER FORM
# -----------------------------
st.markdown("<div class='card'>", unsafe_allow_html=True)
st.markdown("### 📦 Order Booking Form")

a, b, c = st.columns(3)
with a:
    name = st.text_input("Customer Name")
with b:
    mobile = st.text_input("Mobile Number")
with c:
    product = st.selectbox(
        "Product",
        [
            "UltraTech Paper Bag Cement (₹405 approx)",
            "UltraTech Super Cement (₹415 approx)",
            "UltraTech Weather Plus Cement (₹420 approx)",
            "Weather Pro 1 Litre (₹175 approx)",
            "Weather Pro 5 Litre (₹750 approx)",
            "Weather Pro 10 Litre (₹1450 approx)",
            "Weather Pro 20 Litre (₹2500 approx)",
            "Iron Ring (₹12 / piece, Bulk 120+ online)"
        ]
    )

q1, q2 = st.columns(2)
with q1:
    qty = st.text_input("Quantity")
with q2:
    city = st.text_input("City / Area")

address = st.text_area("Address (optional)")
note = st.text_area("Extra Note (optional)")

if st.button("✅ Save Order + WhatsApp Link"):
    order_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    order = {
        "time": order_time,
        "name": name,
        "mobile": mobile,
        "product": product,
        "quantity": qty,
        "city": city,
        "address": address,
        "note": note
    }
    st.session_state.orders.append(order)

    msg = f"""Hello Shikhar Traders,
I want to place an order (UltraTech Only).

Name: {name}
Mobile: {mobile}
Product: {product}
Quantity: {qty}
City/Area: {city}
Address: {address}
Note: {note}

Please confirm final price, stock, delivery charges and payment details.
"""
    wa = make_whatsapp_link(BUSINESS["phones"][0], msg)
    st.success("✅ Order saved!")
    st.markdown(f"📲 WhatsApp Link: [Send Order]({wa})")
    st.info(BUSINESS["note"])

st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------
# ORDERS DASHBOARD
# -----------------------------
st.markdown("<div class='card'>", unsafe_allow_html=True)
st.markdown("### 📊 Orders Dashboard (Open)")

if len(st.session_state.orders) == 0:
    st.warning("No orders saved yet.")
else:
    df = pd.DataFrame(st.session_state.orders)
    st.dataframe(df, use_container_width=True)
    st.download_button(
        "⬇️ Download Orders CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="shikhartraders_orders.csv",
        mime="text/csv"
    )
st.markdown("</div>", unsafe_allow_html=True)

st.write("")

# -----------------------------
# CHAT
# -----------------------------
st.markdown("<div class='card'>", unsafe_allow_html=True)
st.markdown("### 💬 Chat")

if len(st.session_state.messages) == 0:
    st.session_state.messages.append({"role": "assistant", "content": "Hi! I’m Shikhar Traders Voice Agent 👋 How can I help you today?"})

for m in st.session_state.messages:
    if m["role"] == "user":
        st.markdown(f"<div class='chatbox'><span class='badge'>You</span><br>{m['content']}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='chatbox'><span class='badge'>Agent</span><br>{m['content']}</div>", unsafe_allow_html=True)

question = st.chat_input("Ask about UltraTech products / order booking / delivery / payment…")

if question:
    st.session_state.messages.append({"role": "user", "content": question})

    if not openai_key.strip():
        st.session_state.messages.append({"role": "assistant", "content": "⚠️ Please add OpenAI API Key in sidebar."})
    else:
        kb_text = LOCAL_KB
        if st.session_state.docs_text.strip():
            kb_text = kb_text + "\n\nDOCUMENTATION:\n" + st.session_state.docs_text[:12000]

        try:
            with st.spinner("Thinking..."):
                reply = openai_chat(openai_key.strip(), question, kb_text, lang=lang)

            st.session_state.last_answer = reply
            st.session_state.messages.append({"role": "assistant", "content": reply})

            if auto_voice:
                try:
                    audio = openai_tts(openai_key.strip(), reply[:900], voice=voice)
                    st.audio(audio, format="audio/mp3")
                except:
                    pass

        except Exception as e:
            st.session_state.messages.append({"role": "assistant", "content": f"⚠️ Error: {e}"})

st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------
# SPEAK LAST ANSWER
# -----------------------------
st.markdown("<div class='card'>", unsafe_allow_html=True)
st.markdown("### 🔊 Speak Last Answer")

if st.button("🎙️ Speak Again"):
    if not openai_key.strip():
        st.warning("Add OpenAI key first.")
    elif not st.session_state.last_answer.strip():
        st.info("No answer yet. Ask a question first.")
    else:
        try:
            audio = openai_tts(openai_key.strip(), st.session_state.last_answer[:900], voice=voice)
            st.audio(audio, format="audio/mp3")
        except Exception as e:
            st.error(f"TTS error: {e}")
st.markdown("</div>", unsafe_allow_html=True)