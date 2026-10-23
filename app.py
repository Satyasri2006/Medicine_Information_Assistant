import streamlit as st
from pathlib import Path
import base64
import html
from PIL import Image

from model import process_query, generate_response


# ============================================================
# ASSET PATHS
# ============================================================

ASSISTANT_IMAGE = Path("assets/image.jpeg")
BACKGROUND_IMAGE = Path("assets/background.png")

page_icon = Image.open(ASSISTANT_IMAGE) if ASSISTANT_IMAGE.exists() else "💊"


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="MIA - Medicine Information Assistant",
    page_icon=page_icon,
    layout="centered",
    initial_sidebar_state="collapsed"
)


# ============================================================
# SESSION STATE
# ============================================================

if "chat_open" not in st.session_state:
    st.session_state.chat_open = False

if "messages" not in st.session_state:
    st.session_state.messages = []


# ============================================================
# BASE64 ENCODING
# ============================================================


def get_base64_image(image_path: Path):
    if not image_path.exists():
        return None
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()


background_base64 = get_base64_image(BACKGROUND_IMAGE)
assistant_base64 = get_base64_image(ASSISTANT_IMAGE)

avatar_src = f"data:image/jpeg;base64,{assistant_base64}" if assistant_base64 else None


# ============================================================
# BACKGROUND CSS STYLES
# ============================================================

if background_base64:
    bg_rule = f"""
    background-image: url("data:image/png;base64,{background_base64}") !important;
    background-size: cover !important;
    background-position: center !important;
    background-repeat: no-repeat !important;
    background-attachment: fixed !important;
    """
else:
    bg_rule = """
    background: linear-gradient(135deg, #dcf0f5 0%, #eef7f9 100%) !important;
    """


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    f"""
    <style>

    /* Front/App Background Image */
    html, body, [data-testid="stAppViewContainer"] {{
        {bg_rule}
    }}

    [data-testid="stHeader"] {{
        background: transparent !important;
        height: 0 !important;
    }}

    #MainMenu {{
        visibility: hidden;
    }}

    footer {{
        visibility: hidden;
    }}

    /* Main Centered Card Container */
    .main {{
        background: transparent !important;
    }}

    .main .block-container {{
        max-width: 740px !important;
        width: 92% !important;
        margin: 1.5rem auto 2rem auto !important;
        padding: 2.4rem 2.6rem 2.2rem 2.6rem !important;
        background: rgba(255, 255, 255, 0.94) !important;
        backdrop-filter: blur(14px) !important;
        -webkit-backdrop-filter: blur(14px) !important;
        border-radius: 28px !important;
        box-shadow: 0px 16px 45px rgba(24, 60, 75, 0.16) !important;
        border: 1px solid rgba(255, 255, 255, 0.85) !important;
    }}

    /* ======================================================
       LANDING PAGE
       ====================================================== */

    .landing-hero {{
        text-align: center;
        padding-top: 0.5rem;
        padding-bottom: 1.2rem;
    }}

    .hero-image {{
        width: 360px;
        height: 360px;
        border-radius: 50%;
        object-fit: cover;
        border: 5px solid #ffffff;
        box-shadow: 0px 10px 30px rgba(44, 113, 136, 0.25);
        margin: 0 auto 22px auto;
        display: block;
    }}

    .hero-emoji {{
        font-size: 110px;
        margin-bottom: 16px;
        text-align: center;
    }}

    h1.hero-title, .hero-title, [data-testid="stMarkdownContainer"] h1.hero-title, [data-testid="stMarkdownContainer"] .hero-title {{
        font-size: 92px !important;
        line-height: 1.05 !important;
        font-weight: 900 !important;
        letter-spacing: 2px !important;
        color: #002b49 !important;
        margin: 0 0 14px 0 !important;
        text-align: center !important;
    }}

    .hero-subtitle, [data-testid="stMarkdownContainer"] .hero-subtitle {{
        font-size: 26px !important;
        font-weight: 600 !important;
        color: #356477 !important;
        margin: 0 0 28px 0 !important;
        text-align: center !important;
    }}

    /* Primary Button ("Ask away →") */
    button[kind="primary"], [data-testid="stBaseButton-primary"] {{
        background: #2c7188 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 16px !important;
        padding: 14px 28px !important;
        font-size: 17px !important;
        font-weight: 700 !important;
        box-shadow: 0px 6px 18px rgba(44, 113, 136, 0.28) !important;
        transition: all 0.2s ease !important;
    }}

    button[kind="primary"]:hover, [data-testid="stBaseButton-primary"]:hover {{
        background: #225a6c !important;
        color: #ffffff !important;
        transform: translateY(-2px) !important;
        box-shadow: 0px 8px 22px rgba(44, 113, 136, 0.35) !important;
    }}

    /* Secondary Buttons ("Back to MIA", "Clear conversation") */
    button[kind="secondary"], [data-testid="stBaseButton-secondary"] {{
        background: #eef4f6 !important;
        color: #3b5f70 !important;
        border: 1px solid #d3e2e8 !important;
        border-radius: 12px !important;
        padding: 9px 18px !important;
        font-size: 13px !important;
        font-weight: 600 !important;
        box-shadow: none !important;
        transition: all 0.15s ease !important;
    }}

    button[kind="secondary"]:hover, [data-testid="stBaseButton-secondary"]:hover {{
        background: #e2eef2 !important;
        color: #2c7188 !important;
        border-color: #b8d4de !important;
        transform: none !important;
    }}

    .landing-footer {{
        text-align: center;
        margin-top: 36px;
        font-size: 12px;
        color: #7b94a1;
    }}

    /* ======================================================
       CHAT HEADER
       ====================================================== */

    .chat-header {{
        text-align: center;
        margin-bottom: 20px;
        padding-bottom: 12px;
        border-bottom: 1px solid #e2edf2;
    }}

    .chat-header-icon {{
        width: 56px;
        height: 56px;
        border-radius: 50%;
        object-fit: cover;
        border: 3px solid #ffffff;
        box-shadow: 0px 4px 12px rgba(44, 113, 136, 0.22);
        margin: 0 auto 8px auto;
        display: block;
    }}

    .chat-title {{
        font-size: 28px !important;
        font-weight: 800 !important;
        color: #123b52 !important;
        margin: 0 !important;
        text-align: center !important;
    }}

    .chat-subtitle {{
        font-size: 14px !important;
        color: #5c7e8e !important;
        margin-top: 4px !important;
        text-align: center !important;
    }}

    /* ======================================================
       CONVERSATION BUBBLES
       ====================================================== */

    .msg-row {{
        display: flex;
        width: 100%;
        margin: 12px 0;
    }}

    .msg-row.user {{
        justify-content: flex-end;
    }}

    .msg-row.mia {{
        justify-content: flex-start;
        align-items: flex-end;
    }}

    .avatar {{
        width: 36px;
        height: 36px;
        border-radius: 50%;
        object-fit: cover;
        flex: 0 0 auto;
        margin-right: 10px;
        box-shadow: 0px 2px 6px rgba(48, 86, 100, 0.20);
        border: 2px solid #ffffff;
    }}

    .bubble {{
        max-width: 80%;
        padding: 12px 18px;
        font-size: 15px;
        line-height: 1.55;
        word-wrap: break-word;
    }}

    .bubble.user {{
        background: #ffffff !important;
        color: #123b52 !important;
        border: 2px solid #2c7188 !important;
        border-radius: 20px 20px 6px 20px !important;
        box-shadow: 0px 4px 12px rgba(44, 113, 136, 0.15) !important;
    }}

    .bubble.mia {{
        background: #ffffff;
        color: #1d3c4d;
        border-radius: 20px 20px 20px 6px;
        box-shadow: 0px 3px 12px rgba(50, 80, 100, 0.12);
        border: 1px solid #e7f0f4;
    }}

    .intent-badge {{
        display: inline-block;
        background: #e1f1f4;
        color: #2c7188;
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.6px;
        text-transform: uppercase;
        padding: 3px 10px;
        border-radius: 20px;
        margin-bottom: 7px;
    }}

    /* ======================================================
       CHAT INPUT & DISCLAIMER
       ====================================================== */

    [data-testid="stBottom"] {{
        background: transparent !important;
    }}

    [data-testid="stBottom"] > div {{
        max-width: 740px !important;
        margin: 0 auto !important;
        padding-bottom: 1rem !important;
    }}

    [data-testid="stChatInput"] {{
        border-radius: 18px !important;
        box-shadow: 0 4px 16px rgba(44, 113, 136, 0.16) !important;
        background: #ffffff !important;
        background-color: #ffffff !important;
        border: 2px solid #2c7188 !important;
    }}

    [data-testid="stChatInput"] > div,
    [data-testid="stChatInput"] textarea,
    [data-testid="stChatInputTextArea"] {{
        background: #ffffff !important;
        background-color: #ffffff !important;
        color: #123b52 !important;
        border-radius: 16px !important;
    }}

    [data-testid="stChatInput"] textarea {{
        color: #123b52 !important;
        font-size: 15px !important;
        background: #ffffff !important;
        background-color: #ffffff !important;
    }}

    [data-testid="stChatInput"] textarea::placeholder {{
        color: #648392 !important;
    }}

    [data-testid="stChatInput"] button {{
        color: #2c7188 !important;
        background: transparent !important;
    }}

    [data-testid="stChatInput"] button:hover {{
        color: #123b52 !important;
    }}

    .chat-disclaimer {{
        background: rgba(255, 248, 225, 0.9);
        border-left: 4px solid #e5ad32;
        border-radius: 10px;
        padding: 10px 14px;
        margin-top: 18px;
        margin-bottom: 10px;
        color: #765d19;
        font-size: 12px;
        line-height: 1.5;
    }}

    /* ======================================================
       RESPONSIVE MOBILE
       ====================================================== */

    @media (max-width: 768px) {{
        .main .block-container {{
            width: 95% !important;
            margin: 0.8rem auto !important;
            padding: 1.6rem 1.2rem !important;
            border-radius: 20px !important;
        }}

        .hero-image {{
            width: 200px;
            height: 200px;
        }}

        .hero-title {{
            font-size: 58px;
        }}

        .hero-subtitle {{
            font-size: 17px;
        }}

        .bubble {{
            max-width: 88%;
        }}
    }}

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# LANDING PAGE
# ============================================================

if not st.session_state.chat_open:

    if avatar_src:
        avatar_tag = f'<img class="hero-image" src="{avatar_src}" alt="MIA">'
    else:
        avatar_tag = '<div class="hero-emoji">🤖</div>'

    hero_html = f"""<div class="landing-hero">
        {avatar_tag}
        <h1 class="hero-title" style="color: #002b49 !important; font-size: 92px !important; font-weight: 900 !important; letter-spacing: 2px !important; line-height: 1.05 !important; margin: 0 0 14px 0 !important; text-align: center !important;">I am MIA</h1>
        <p class="hero-subtitle" style="color: #356477 !important; font-size: 26px !important; font-weight: 600 !important; margin: 0 0 28px 0 !important; text-align: center !important;">Your personal medicine information assistant</p>
    </div>"""

    st.markdown(hero_html, unsafe_allow_html=True)

    _, col_btn, _ = st.columns([1, 2, 1])
    with col_btn:
        if st.button("Ask away →", key="open_chat", type="primary", use_container_width=True):
            st.session_state.chat_open = True
            if not st.session_state.messages:
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": (
                            "Hi! I'm MIA\n"
                            "Ask me about any medicine — its uses, "
                            "dosage, side effects or warnings."
                        ),
                        "intent": None
                    }
                )
            st.rerun()

    st.markdown(
        '<div class="landing-footer">'
        'For general awareness only • Not a substitute for professional medical advice'
        '</div>',
        unsafe_allow_html=True
    )

    st.stop()


# ============================================================
# CHAT PAGE
# ============================================================

if avatar_src:
    header_icon_html = f'<img class="chat-header-icon" src="{avatar_src}" alt="MIA">'
else:
    header_icon_html = '<div style="font-size: 38px; margin-bottom: 6px; text-align: center;">🤖</div>'

st.markdown(
    f"""<div class="chat-header">
        {header_icon_html}
        <div class="chat-title">MIA</div>
        <div class="chat-subtitle">Your personal medicine information assistant</div>
    </div>""",
    unsafe_allow_html=True
)


# ============================================================
# CHAT HISTORY
# ============================================================

for message in st.session_state.messages:
    # Escape special characters and convert newlines to <br> so markdown
    # parser doesn't break out of the HTML block
    content_escaped = html.escape(message["content"]).replace("\n", "<br>")

    if message["role"] == "user":
        msg_html = (
            '<div class="msg-row user">'
            f'<div class="bubble user">{content_escaped}</div>'
            '</div>'
        )
        st.markdown(msg_html, unsafe_allow_html=True)
    else:
        intent = message.get("intent")
        intent_html = ""
        if intent:
            intent_escaped = html.escape(intent.replace("_", " "))
            intent_html = f'<span class="intent-badge">{intent_escaped}</span><br>'

        avatar_tag = f'<img class="avatar" src="{avatar_src}" alt="MIA">' if avatar_src else ""
        msg_html = (
            '<div class="msg-row mia">'
            f'{avatar_tag}'
            f'<div class="bubble mia">{intent_html}{content_escaped}</div>'
            '</div>'
        )
        st.markdown(msg_html, unsafe_allow_html=True)


# ============================================================
# CHAT INPUT
# ============================================================

query = st.chat_input("Type your message about a medicine...")

if query:
    st.session_state.messages.append(
        {
            "role": "user",
            "content": query
        }
    )

    with st.spinner("MIA is thinking..."):
        try:
            result = process_query(query)
            if result["status"] == "success":
                response = generate_response(result)
                intent = result["intent"]
            else:
                response = result["message"]
                intent = None
        except Exception:
            response = (
                "Sorry, I couldn't process that question right now. "
                "Please check the medicine name and try again."
            )
            intent = None

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": response,
            "intent": intent
        }
    )
    st.rerun()


# ============================================================
# CHAT CONTROLS
# ============================================================

col1, col2 = st.columns(2)

with col1:
    if st.button("← Back to MIA", key="back_home", type="secondary", use_container_width=True):
        st.session_state.chat_open = False
        st.rerun()

with col2:
    if st.button("Clear conversation", key="clear_chat", type="secondary", use_container_width=True):
        st.session_state.messages = []
        st.rerun()


# ============================================================
# DISCLAIMER
# ============================================================

st.markdown(
    """<div class="chat-disclaimer">
        ⚠️ <strong>Important:</strong> MIA provides information for general
        awareness and educational purposes only. It does not replace
        advice, diagnosis or treatment from a qualified healthcare
        professional.
    </div>""",
    unsafe_allow_html=True
)
