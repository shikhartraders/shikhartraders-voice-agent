import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(
    page_title="Shikhar Traders Voice Agent (V4 Animated)",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------
# V4 ANIMATED PREMIUM CSS
# -----------------------------
st.markdown("""
<style>
/* MAIN BACKGROUND */
.stApp{
    background: #05060b;
    color: white;
    overflow-x: hidden;
}

/* Animated gradient layer */
.bg-anim {
    position: fixed;
    inset: 0;
    z-index: -3;
    background:
        radial-gradient(circle at 20% 15%, rgba(0,255,255,0.20), transparent 45%),
        radial-gradient(circle at 85% 20%, rgba(168,85,247,0.22), transparent 45%),
        radial-gradient(circle at 50% 95%, rgba(0,255,120,0.18), transparent 50%),
        linear-gradient(120deg, #05060b, #070a14, #05060b);
    animation: bgMove 12s ease-in-out infinite;
}
@keyframes bgMove {
    0% { filter: hue-rotate(0deg) brightness(1); transform: scale(1); }
    50% { filter: hue-rotate(30deg) brightness(1.15); transform: scale(1.02); }
    100% { filter: hue-rotate(0deg) brightness(1); transform: scale(1); }
}

/* Floating blobs */
.blob {
    position: fixed;
    width: 340px;
    height: 340px;
    border-radius: 999px;
    filter: blur(40px);
    opacity: 0.35;
    z-index: -2;
    animation: floaty 10s ease-in-out infinite;
}
.blob.b1 { left: -120px; top: 90px; background: rgba(0,245,255,0.8); }
.blob.b2 { right: -140px; top: 140px; background: rgba(168,85,247,0.85); animation-delay: 2s; }
.blob.b3 { left: 30%; bottom: -160px; background: rgba(0,255,120,0.75); animation-delay: 4s; }

@keyframes floaty {
    0% { transform: translateY(0px) translateX(0px) scale(1); }
    50% { transform: translateY(-30px) translateX(15px) scale(1.05); }
    100% { transform: translateY(0px) translateX(0px) scale(1); }
}

/* Tiny particle shimmer */
.particles {
    position: fixed;
    inset: 0;
    z-index: -1;
    background-image:
        radial-gradient(rgba(255,255,255,0.10) 1px, transparent 1px);
    background-size: 55px 55px;
    opacity: 0.18;
    animation: drift 18s linear infinite;
}
@keyframes drift {
    0% { transform: translateY(0px); }
    100% { transform: translateY(-120px); }
}

/* Sidebar */
section[data-testid="stSidebar"]{
    background: linear-gradient(180deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02));
    border-right: 1px solid rgba(255,255,255,0.10);
    backdrop-filter: blur(18px);
}

/* Title */
.glow-title{
    font-size: 46px;
    font-weight: 950;
    letter-spacing: 0.6px;
    background: linear-gradient(90deg, #00f5ff, #a855f7, #ff4fd8, #00ff88);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-shadow: 0px 0px 35px rgba(168,85,247,0.25);
}

/* Typing effect */
.typing {
    font-size: 14px;
    opacity: 0.85;
    border-right: 2px solid rgba(255,255,255,0.7);
    white-space: nowrap;
    overflow: hidden;
    width: 0;
    animation: typing 4s steps(50, end) infinite alternate;
}
@keyframes typing {
    from { width: 0; }
    to { width: 520px; }
}

/* Glass cards */
.glass{
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.12);
    box-shadow: 0 18px 55px rgba(0,0,0,0.42);
    border-radius: 20px;
    padding: 18px;
    backdrop-filter: blur(16px);
}

/* Chat bubble */
.chatbox{
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 18px;
    padding: 14px 16px;
    margin: 10px 0px;
    backdrop-filter: blur(14px);
}

/* Badge */
.badge{
    display:inline-block;
    padding: 6px 10px;
    border-radius: 999px;
    font-weight: 900;
    font-size: 12px;
    border: 1px solid rgba(255,255,255,0.10);
    background: rgba(255,255,255,0.06);
}

/* Buttons */
.stButton>button{
    border-radius: 14px !important;
    padding: 10px 16px !important;
    font-weight: 900 !important;
    border: 1px solid rgba(255,255,255,0.14) !important;
    background: linear-gradient(135deg, rgba(0,245,255,0.18), rgba(168,85,247,0.18), rgba(255,79,216,0.12)) !important;
    color: #fff !important;
    box-shadow: 0 14px 35px rgba(0,0,0,0.35) !important;
    transition: 0.25s ease !important;
}
.stButton>button:hover{
    transform: translateY(-2px) scale(1.02);
    box-shadow: 0 20px 45px rgba(0,0,0,0.50) !important;
}
hr{
    border: none;
    height: 1px;
    background: rgba(255,255,255,0.10);
    margin: 14px 0;
}
</style>

<div class="bg-anim"></div>
<div class="blob b1"></div>
<div class="blob b2"></div>
<div class="blob b3"></div>
<div class="particles"></div>
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
# LANGUAGE PACK
# -----------------------------
def lang_pack(lang):
    if lang == "English":
        return {
            "welcome": "Hi! I’m Shikhar Traders Voice Agent 👋 How can I help you today?",
            "hint": "Ask about UltraTech products / order booking / delivery / payment…",
            "missing_key": "⚠️ OpenAI API Key missing. Please add it in sidebar.",
            "cooldown": "⏳ Please wait 3 seconds before next message (anti rate-limit)."
        }
    if lang == "Hinglish":
        return {
            "welcome": "Hi! Main Shikhar Traders Voice Agent हूँ 👋 Aapko kis cheez mein help chahiye?",
            "hint": "UltraTech products / order / delivery / payment ke baare mein poochho…",
            "missing_key": "⚠️ OpenAI API Key nahi dala. Sidebar mein add karo.",
            "cooldown": "⏳ 3 seconds ruk jao, phir message bhejo (rate-limit avoid)."
        }
    return {
        "welcome": "नमस्ते! मैं Shikhar Traders Voice Agent हूँ 👋 आप किस चीज़ में मदद चाहते हैं?",
        "hint": "UltraTech products / order / delivery / payment के बारे में पूछिए…",
        "missing_key": "⚠️ OpenAI API Key नहीं डाला गया। Sidebar में डालिए।",
        "cooldown": "⏳ अगला message भेजने से पहले 3 सेकंड रुकिए (rate-limit avoid)."
    }

# -----------------------------
# OPENAI CHAT
# -----------------------------
def openai_chat(api_key, question, kb, lang="English"):
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
            {"role": "user", "content": f"KNOWLEDGE:\n{kb}\n\nQUESTION:\n{question}"}
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

# -----------------------------
# OPENAI TTS
# -----------------------------
def openai_tts(api_key, text, voice="coral"):
    url = "https://api.openai.com/v1/audio/speech"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": "gpt-4o-mini-tts", "voice": voice, "input": text}
    r = requests.post(url, headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    return r.content

# -----------------------------
# WHATSAPP LINK
# -----------------------------
def make_whatsapp_link(phone, message):
    phone_clean = phone.replace(" ", "")
    if phone_clean.startswith("0"):
        phone_clean = phone_clean[1:]
    if not phone_clean.startswith("91"):
        phone_clean = "91" + phone_clean
    msg = requests.utils.quote(message)
    return f"https://wa.me/{phone_clean}?text={msg}"

# -----------------------------
# SESSION STATE
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "orders" not in st.session_state:
    st.session_state.orders = []
if "last_msg_time" not in st.session_state:
    st.session_state.last_msg_time = 0

# -----------------------------
# SIDEBAR
# -----------------------------
st.sidebar.markdown("## ⚙️ Settings")
openai_key = st.sidebar.text_input("OpenAI API Key", value="", type="password")
lang = st.sidebar.selectbox("🌍 Language", ["English", "Hinglish", "Hindi"])
voice = st.sidebar.selectbox("🎙️ Voice", ["coral", "alloy", "verse", "sage"])
enable_voice = st.sidebar.toggle("🔊 Voice Replies", value=True)

st.sidebar.markdown("---")
if st.sidebar.button("🧹 Clear Chat"):
    st.session_state.messages = []
    st.experimental_rerun()

# -----------------------------
# HEADER
# -----------------------------
c1, c2 = st.columns([1.7, 1.0])

with c1:
    st.markdown(f"<div class='glow-title'>{BUSINESS['name']} Voice Agent</div>", unsafe_allow_html=True)
    st.markdown("<div class='typing'>UltraTech Only • Voice Replies • WhatsApp Orders • Premium Animated UI</div>", unsafe_allow_html=True)

with c2:
    st.markdown("<div class='glass'>", unsafe_allow_html=True)
    st.markdown(f"📞 **{BUSINESS['phones'][0]}** | **{BUSINESS['phones'][1]}**")
    st.markdown(f"✉️ **{BUSINESS['email']}**")
    st.markdown(f"📍 [Store Location]({BUSINESS['maps']})")
    st.markdown(f"🌐 [Website]({BUSINESS['website']})")
    st.markdown("</div>", unsafe_allow_html=True)

st.write("")

# -----------------------------
# QUICK ACTIONS
# -----------------------------
st.markdown("<div class='glass'>", unsafe_allow_html=True)
st.markdown("### ⚡ Quick Actions (Tap)")

qa1, qa2, qa3, qa4, qa5, qa6 = st.columns(6)

if qa1.button("🧱 Cement Price"):
    st.session_state.messages.append({"role": "user", "content": "Tell me UltraTech cement prices."})
if qa2.button("🛡️ Waterproofing"):
    st.session_state.messages.append({"role": "user", "content": "Tell me Weather Pro waterproofing prices and uses."})
if qa3.button("🔩 Iron Ring"):
    st.session_state.messages.append({"role": "user", "content": "Iron ring price and bulk order rules?"})
if qa4.button("📦 Order Booking"):
    st.session_state.messages.append({"role": "user", "content": "I want to book an order. What details do you need?"})
if qa5.button("🚚 Delivery"):
    st.session_state.messages.append({"role": "user", "content": "Do you provide delivery? How much delivery charge?"})
if qa6.button("💳 Payment"):
    st.session_state.messages.append({"role": "user", "content": "How can I pay? Confirm payment options."})

st.markdown("</div>", unsafe_allow_html=True)

st.write("")

# -----------------------------
# ORDER BOOKING FORM
# -----------------------------
st.markdown("<div class='glass'>", unsafe_allow_html=True)
st.markdown("### 📦 Order Booking Form (Animated V4)")

o1, o2, o3 = st.columns(3)
with o1:
    customer_name = st.text_input("Customer Name")
with o2:
    customer_mobile = st.text_input("Mobile Number")
with o3:
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
    quantity = st.text_input("Quantity (bags/litres/pieces)")
with q2:
    delivery_city = st.text_input("City / Area")

address = st.text_area("Full Address (optional)")
note = st.text_area("Extra Note (optional)")

submit = st.button("✅ Save Order + WhatsApp Link")

if submit:
    order_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    order_data = {
        "time": order_time,
        "name": customer_name,
        "mobile": customer_mobile,
        "product": product,
        "quantity": quantity,
        "city": delivery_city,
        "address": address,
        "note": note
    }
    st.session_state.orders.append(order_data)

    whatsapp_msg = f"""Hello Shikhar Traders,
I want to place an order (UltraTech Only).

Name: {customer_name}
Mobile: {customer_mobile}
Product: {product}
Quantity: {quantity}
City/Area: {delivery_city}
Address: {address}
Note: {note}

Please confirm final price, stock, delivery charges and payment details.
"""

    wa_link = make_whatsapp_link(BUSINESS["phones"][0], whatsapp_msg)

    st.success("✅ Order saved successfully!")
    st.markdown(f"📲 **WhatsApp Order Link:** [Click Here to Send]({wa_link})")
    st.info(BUSINESS["note"])

st.markdown("</div>", unsafe_allow_html=True)

st.write("")

# -----------------------------
# ORDERS DASHBOARD
# -----------------------------
st.markdown("<div class='glass'>", unsafe_allow_html=True)
st.markdown("### 📊 Orders Dashboard (Open)")

if len(st.session_state.orders) == 0:
    st.warning("No orders saved yet.")
else:
    df = pd.DataFrame(st.session_state.orders)
    st.dataframe(df, use_container_width=True)

    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download Orders CSV",
        data=csv_bytes,
        file_name="shikhartraders_orders.csv",
        mime="text/csv"
    )

st.markdown("</div>", unsafe_allow_html=True)

st.write("")

# -----------------------------
# CHAT SECTION
# -----------------------------
pack = lang_pack(lang)

if len(st.session_state.messages) == 0:
    st.session_state.messages.append({"role": "assistant", "content": pack["welcome"]})

for m in st.session_state.messages:
    if m["role"] == "user":
        st.markdown(f"<div class='chatbox'><span class='badge'>You</span><br>{m['content']}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='chatbox'><span class='badge'>Agent</span><br>{m['content']}</div>", unsafe_allow_html=True)

user_q = st.chat_input(pack["hint"])

def add_assistant_reply(reply_text):
    st.session_state.messages.append({"role": "assistant", "content": reply_text})

    if enable_voice and openai_key.strip():
        try:
            audio = openai_tts(openai_key.strip(), reply_text[:900], voice=voice)
            st.audio(audio, format="audio/mp3")
        except Exception:
            pass

def handle_question(q):
    now = time.time()
    if now - st.session_state.last_msg_time < 3:
        add_assistant_reply(pack["cooldown"])
        return
    st.session_state.last_msg_time = now

    st.session_state.messages.append({"role": "user", "content": q})

    if not openai_key.strip():
        add_assistant_reply(pack["missing_key"])
        return

    try:
        with st.spinner("Thinking..."):
            reply = openai_chat(openai_key.strip(), q, LOCAL_KB, lang=lang)

        if any(k in q.lower() for k in ["price", "stock", "payment", "discount", "delivery"]):
            reply += f"\n\n📞 Call/WhatsApp: {BUSINESS['phones'][0]}, {BUSINESS['phones'][1]}\n✉️ Email: {BUSINESS['email']}"

        add_assistant_reply(reply)

    except Exception as e:
        add_assistant_reply(f"⚠️ Error: {str(e)}\n\nTry again after 10 seconds.")

if user_q:
    handle_question(user_q)
    st.experimental_rerun()