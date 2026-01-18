import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import time

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="Shikhar Traders Voice Agent (V7 Premium)",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# PREMIUM CSS (CLEAN + ANIMATED)
# =========================
st.markdown("""
<style>
/* App background */
.stApp{
    background:#05060b;
    color:#ffffff;
}

/* Animated gradient blobs */
.bg{
    position:fixed; inset:0; z-index:-10;
    background:
        radial-gradient(circle at 15% 15%, rgba(0,255,255,0.20), transparent 45%),
        radial-gradient(circle at 85% 20%, rgba(168,85,247,0.20), transparent 42%),
        radial-gradient(circle at 50% 95%, rgba(0,255,120,0.16), transparent 50%),
        linear-gradient(120deg, #05060b, #070a14, #05060b);
    animation:bgFlow 12s ease-in-out infinite;
}
@keyframes bgFlow{
    0%{filter:hue-rotate(0deg) brightness(1); transform:scale(1);}
    50%{filter:hue-rotate(22deg) brightness(1.15); transform:scale(1.02);}
    100%{filter:hue-rotate(0deg) brightness(1); transform:scale(1);}
}

/* Fade-in animation */
.fadein{
    animation:fadeInUp 0.6s ease both;
}
@keyframes fadeInUp{
    from{opacity:0; transform:translateY(12px);}
    to{opacity:1; transform:translateY(0px);}
}

/* Glass card */
.card{
    border-radius:22px;
    padding:18px 18px;
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.12);
    box-shadow: 0 22px 70px rgba(0,0,0,0.50);
    backdrop-filter: blur(16px);
}

/* Premium title */
.title{
    font-size:44px;
    font-weight:950;
    line-height:1.05;
    background: linear-gradient(90deg, #00f5ff, #a855f7, #ff4fd8, #00ff88);
    -webkit-background-clip:text;
    -webkit-text-fill-color:transparent;
    animation: shimmer 4s linear infinite;
    background-size: 200% 200%;
}
@keyframes shimmer{
    0%{background-position:0% 50%;}
    100%{background-position:100% 50%;}
}

.sub{
    color:rgba(255,255,255,0.70);
    font-size:14px;
    margin-top:6px;
}

/* Small badge */
.badge{
    display:inline-block;
    padding: 6px 10px;
    border-radius: 999px;
    font-weight: 900;
    font-size: 12px;
    border: 1px solid rgba(255,255,255,0.10);
    background: rgba(255,255,255,0.06);
}

/* Chat bubbles */
.bubble{
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 18px;
    padding: 14px 16px;
    margin: 10px 0px;
    backdrop-filter: blur(14px);
}

/* Buttons glow */
.stButton>button{
    border-radius: 14px !important;
    padding: 10px 14px !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    background: rgba(255,255,255,0.06) !important;
    color: white !important;
    font-weight: 800 !important;
    transition: all .25s ease !important;
}
.stButton>button:hover{
    transform: translateY(-2px) scale(1.02);
    box-shadow: 0 18px 40px rgba(0,0,0,0.55);
    border: 1px solid rgba(0,245,255,0.35) !important;
}

/* Sidebar cleanup */
section[data-testid="stSidebar"]{
    background: rgba(10,12,18,0.85);
    border-right: 1px solid rgba(255,255,255,0.08);
}
</style>
<div class="bg"></div>
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

# =========================
# HELPERS
# =========================
def load_docs(raw_url: str) -> str:
    if not raw_url or "raw.githubusercontent.com" not in raw_url:
        return ""
    try:
        r = requests.get(raw_url, timeout=20)
        if r.status_code == 200 and len(r.text.strip()) > 30:
            return r.text
        return ""
    except:
        return ""

def openai_chat(api_key, question, kb_text, lang="English"):
    url = "https://api.openai.com/v1/responses"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    system_prompt = f"""
You are a premium customer support agent for {BUSINESS['name']} (UltraTech only).
Answer in {lang}.
Be fast, short, clear, friendly, and professional.
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

# =========================
# SESSION
# =========================
if "messages" not in st.session_state:
    st.session_state.messages = []
if "orders" not in st.session_state:
    st.session_state.orders = []
if "last_answer" not in st.session_state:
    st.session_state.last_answer = ""
if "docs_text" not in st.session_state:
    st.session_state.docs_text = ""
if "tts_last_time" not in st.session_state:
    st.session_state.tts_last_time = 0

# =========================
# SIDEBAR
# =========================
st.sidebar.markdown("## ⚙️ Configuration")
openai_key = st.sidebar.text_input("OpenAI API Key", value="", type="password")

docs_url = st.sidebar.text_input(
    "Documentation RAW URL",
    value="https://raw.githubusercontent.com/shikhartraders/shikhartraders-voice-agent/main/shikhartraders_support_docs_all_in_one.md"
)

lang = st.sidebar.selectbox("🌍 Language", ["English", "Hinglish", "Hindi"])
voice = st.sidebar.selectbox("🎙️ Voice", ["coral", "alloy", "verse", "sage"])
auto_voice = st.sidebar.toggle("🔊 Auto Voice Reply", value=False)

c1, c2 = st.sidebar.columns(2)
with c1:
    if st.button("📥 Load Docs"):
        st.session_state.docs_text = load_docs(docs_url)
        if st.session_state.docs_text:
            st.sidebar.success("✅ Docs loaded")
        else:
            st.sidebar.error("❌ Docs not loaded (RAW link wrong or file private)")
with c2:
    if st.button("🧹 Clear"):
        st.session_state.messages = []
        st.session_state.last_answer = ""

# =========================
# HEADER
# =========================
st.markdown("<div class='fadein card'>", unsafe_allow_html=True)
st.markdown(f"<div class='title'>{BUSINESS['name']} Voice Agent</div>", unsafe_allow_html=True)
st.markdown("<div class='sub'>UltraTech Only • Clean UI • Premium Animations • Voice Replies</div>", unsafe_allow_html=True)

st.markdown(
    f"""
    <br>
    <span class='badge'>📞 {BUSINESS['phones'][0]}</span>
    <span class='badge'>📞 {BUSINESS['phones'][1]}</span>
    <span class='badge'>✉️ {BUSINESS['email']}</span>
    <span class='badge'>📍 Store Location</span>
    """,
    unsafe_allow_html=True
)
st.markdown(f"🔗 Store Location: {BUSINESS['maps']}")
st.markdown(f"🌐 Website: {BUSINESS['website']}")
st.markdown("</div>", unsafe_allow_html=True)

st.write("")

# =========================
# QUICK ACTIONS
# =========================
st.markdown("<div class='fadein card'>", unsafe_allow_html=True)
st.markdown("### ⚡ Quick Actions (Tap)")
qa1, qa2, qa3, qa4, qa5 = st.columns(5)

if qa1.button("🧱 Cement Price"):
    st.session_state.messages.append({"role": "user", "content": "Tell me UltraTech cement prices."})
if qa2.button("🛡️ Waterproofing"):
    st.session_state.messages.append({"role": "user", "content": "Tell me Weather Pro waterproofing prices and uses."})
if qa3.button("🔩 Iron Ring"):
    st.session_state.messages.append({"role": "user", "content": "Iron ring price and bulk order rules?"})
if qa4.button("📦 Book Order"):
    st.session_state.messages.append({"role": "user", "content": "I want to book an order. What details do you need?"})
if qa5.button("💳 Payment"):
    st.session_state.messages.append({"role": "user", "content": "How can I pay? Confirm payment options."})

st.markdown("</div>", unsafe_allow_html=True)

st.write("")

# =========================
# ORDER FORM (CLEAN)
# =========================
st.markdown("<div class='fadein card'>", unsafe_allow_html=True)
st.markdown("### 📦 Quick Order Form")

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

note = st.text_area("Extra Note (optional)")

if st.button("✅ Save Order + WhatsApp"):
    order_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    order = {
        "time": order_time,
        "name": name,
        "mobile": mobile,
        "product": product,
        "quantity": qty,
        "city": city,
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
Note: {note}

Please confirm final price, stock, delivery charges and payment details.
"""
    wa = make_whatsapp_link(BUSINESS["phones"][0], msg)
    st.success("✅ Order saved!")
    st.markdown(f"📲 WhatsApp Link: [Send Order]({wa})")
    st.info(BUSINESS["note"])

st.markdown("</div>", unsafe_allow_html=True)

st.write("")

# =========================
# ORDERS DASHBOARD
# =========================
st.markdown("<div class='fadein card'>", unsafe_allow_html=True)
st.markdown("### 📊 Orders Dashboard")

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

# =========================
# CHAT
# =========================
st.markdown("<div class='fadein card'>", unsafe_allow_html=True)
st.markdown("### 💬 Chat")

if len(st.session_state.messages) == 0:
    st.session_state.messages.append({
        "role": "assistant",
        "content": "Hi! I’m Shikhar Traders Voice Agent 👋 Ask me about UltraTech cement / waterproofing / orders."
    })

for m in st.session_state.messages:
    if m["role"] == "user":
        st.markdown(f"<div class='bubble'><span class='badge'>You</span><br>{m['content']}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='bubble'><span class='badge'>Agent</span><br>{m['content']}</div>", unsafe_allow_html=True)

question = st.chat_input("Ask about UltraTech products / delivery / payment…")

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

            # Auto voice reply (with cooldown)
            if auto_voice:
                now = time.time()
                if now - st.session_state.tts_last_time < 10:
                    st.warning("⏳ Voice cooldown: wait 10 seconds to avoid 429 error.")
                else:
                    try:
                        audio = openai_tts(openai_key.strip(), reply[:800], voice=voice)
                        st.audio(audio, format="audio/mp3")
                        st.session_state.tts_last_time = now
                    except Exception as e:
                        st.error("🔊 TTS failed (rate limit). Please wait 10 seconds and try again.")

        except Exception as e:
            st.session_state.messages.append({"role": "assistant", "content": f"⚠️ Error: {e}"})

st.markdown("</div>", unsafe_allow_html=True)

st.write("")

# =========================
# SPEAK LAST ANSWER
# =========================
st.markdown("<div class='fadein card'>", unsafe_allow_html=True)
st.markdown("### 🔊 Speak Last Answer")

if st.button("🎙️ Speak Again"):
    if not openai_key.strip():
        st.warning("Add OpenAI key first.")
    elif not st.session_state.last_answer.strip():
        st.info("No answer yet. Ask a question first.")
    else:
        now = time.time()
        if now - st.session_state.tts_last_time < 10:
            st.warning("⏳ Wait 10 seconds to avoid 429 Too Many Requests.")
        else:
            try:
                audio = openai_tts(openai_key.strip(), st.session_state.last_answer[:800], voice=voice)
                st.audio(audio, format="audio/mp3")
                st.session_state.tts_last_time = now
            except:
                st.error("TTS rate limit hit. Please wait and try again.")

st.markdown("</div>", unsafe_allow_html=True)

# =========================
# DOCS PREVIEW
# =========================
st.markdown("<div class='fadein card'>", unsafe_allow_html=True)
st.markdown("### 📄 Documentation Preview")

if st.session_state.docs_text.strip():
    st.success("✅ Documentation is loaded.")
    st.text_area("Docs (preview)", st.session_state.docs_text[:2500], height=220)
else:
    st.info("Docs not loaded. App will still work using built-in products + FAQs.")

st.markdown("</div>", unsafe_allow_html=True)