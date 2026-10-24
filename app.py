import streamlit as st
from pathlib import Path
import base64
import html
import uuid
from PIL import Image

from model import process_query, generate_response
import database


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
# SESSION STATE INITIALIZATION
# ============================================================

if "user" not in st.session_state:
    st.session_state.user = None

if "chat_open" not in st.session_state:
    st.session_state.chat_open = False

if "viewing_history" not in st.session_state:
    st.session_state.viewing_history = False

if "messages" not in st.session_state:
    st.session_state.messages = []

if "current_session_id" not in st.session_state or not st.session_state.current_session_id:
    st.session_state.current_session_id = uuid.uuid4().hex[:10]


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
       LANDING PAGE & HERO
       ====================================================== */

    .landing-hero {{
        text-align: center;
        padding-top: 0.5rem;
        padding-bottom: 1.2rem;
    }}

    .hero-image {{
        width: 320px;
        height: 320px;
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

    /* User Greeting Pill */
    .user-greeting-pill {{
        background: #eef7fa;
        border: 1.5px solid #c8e1ea;
        border-radius: 14px;
        padding: 10px 18px;
        margin: 0 auto 24px auto;
        max-width: 520px;
        text-align: center;
        color: #123b52;
        font-size: 15px;
        font-weight: 600;
        box-shadow: 0 2px 8px rgba(44, 113, 136, 0.08);
    }}

    /* Form Fields Styling */
    [data-testid="stTextInput"] {{
        margin-bottom: 12px !important;
    }}

    [data-testid="stTextInput"] label p {{
        color: #123b52 !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        margin-bottom: 4px !important;
    }}

    [data-testid="stTextInput"] input {{
        background-color: #ffffff !important;
        color: #123b52 !important;
        border: 1.5px solid #c2dbe4 !important;
        border-radius: 10px !important;
        padding: 10px 14px !important;
        font-size: 15px !important;
        box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.03) !important;
    }}

    [data-testid="stTextInput"] input::placeholder {{
        color: #8fa3ad !important;
        font-size: 14px !important;
    }}

    [data-testid="stTextInput"] input:focus {{
        border-color: #2c7188 !important;
        box-shadow: 0 0 0 2px rgba(44, 113, 136, 0.2) !important;
    }}

    /* ======================================================
       SEGMENTED TABS BAR (matches reference picture)
       ====================================================== */
    [data-testid="stTabs"] [role="tablist"],
    .stTabs [role="tablist"],
    [data-baseweb="tab-list"],
    .stTabs [data-baseweb="tab-list"] {{
        display: flex !important;
        width: 100% !important;
        background: #ffffff !important;
        border: 1.5px solid #2c7188 !important;
        border-radius: 14px !important;
        padding: 0 !important;
        margin: 0 0 16px 0 !important;
        overflow: hidden !important;
        gap: 0 !important;
        box-shadow: 0 2px 8px rgba(44, 113, 136, 0.08) !important;
    }}

    [data-testid="stTabs"] [role="tab"],
    [data-testid="stTab"],
    button[role="tab"],
    [data-baseweb="tab"],
    .stTabs [data-baseweb="tab"] {{
        flex: 1 1 50% !important;
        width: 50% !important;
        min-width: 0 !important;
        height: 48px !important;
        min-height: 48px !important;
        text-align: center !important;
        justify-content: center !important;
        align-items: center !important;
        display: inline-flex !important;
        font-size: 16px !important;
        font-weight: 700 !important;
        padding: 10px 16px !important;
        margin: 0 !important;
        border: none !important;
        border-radius: 0 !important;
        background: #ffffff !important;
        color: #123b52 !important;
        cursor: pointer !important;
        transition: all 0.2s ease !important;
    }}

    /* Dividing line between left and right tab */
    [data-testid="stTabs"] [role="tab"]:first-child,
    [data-testid="stTab"]:first-child,
    [data-baseweb="tab"]:first-child,
    .stTabs [data-baseweb="tab"]:first-child {{
        border-right: 1.5px solid #2c7188 !important;
    }}

    /* Active Selected Tab (solid teal with white text) */
    [data-testid="stTabs"] [role="tab"][aria-selected="true"],
    [data-testid="stTab"][aria-selected="true"],
    [data-testid="stTabs"] [role="tab"][data-selected="true"],
    [data-baseweb="tab"][aria-selected="true"],
    .stTabs [data-baseweb="tab"][aria-selected="true"] {{
        background: #2c7188 !important;
        color: #ffffff !important;
    }}

    [data-testid="stTabs"] [role="tab"][aria-selected="true"] *,
    [data-testid="stTab"][aria-selected="true"] *,
    [data-testid="stTabs"] [role="tab"][data-selected="true"] *,
    [data-baseweb="tab"][aria-selected="true"] *,
    .stTabs [data-baseweb="tab"][aria-selected="true"] * {{
        color: #ffffff !important;
        font-weight: 700 !important;
    }}

    /* Inactive Tab (white with dark teal text) */
    [data-testid="stTabs"] [role="tab"][aria-selected="false"],
    [data-testid="stTab"][aria-selected="false"],
    [data-baseweb="tab"][aria-selected="false"],
    .stTabs [data-baseweb="tab"][aria-selected="false"] {{
        background: #ffffff !important;
        color: #123b52 !important;
    }}

    [data-testid="stTabs"] [role="tab"][aria-selected="false"]:hover,
    [data-testid="stTab"][aria-selected="false"]:hover,
    [data-baseweb="tab"][aria-selected="false"]:hover,
    .stTabs [data-baseweb="tab"][aria-selected="false"]:hover {{
        background: #f2f8fa !important;
    }}

    [data-testid="stTabs"] [role="tab"][aria-selected="false"] *,
    [data-testid="stTab"][aria-selected="false"] *,
    [data-baseweb="tab"][aria-selected="false"] *,
    .stTabs [data-baseweb="tab"][aria-selected="false"] * {{
        color: #123b52 !important;
        font-weight: 700 !important;
    }}

    /* Remove default Streamlit tab borders, bottom line & indicators */
    [data-testid="stTabs"] [role="tablist"]::after,
    .stTabs [role="tablist"]::after,
    .react-aria-SelectionIndicator,
    [data-testid="stTabs"] .react-aria-SelectionIndicator,
    [data-baseweb="tab-border"],
    [data-baseweb="tab-highlight"],
    [data-testid="stTabs"] hr {{
        display: none !important;
        content: none !important;
        opacity: 0 !important;
        height: 0 !important;
        width: 0 !important;
    }}

    [data-testid="stTabs"] [role="tab"] p,
    [data-testid="stTab"] p {{
        font-size: 16px !important;
        font-weight: 700 !important;
        margin: 0 !important;
        padding: 0 !important;
    }}

    /* Auth Card Form */
    [data-testid="stForm"] {{
        border: 1.5px solid #b8d4de !important;
        border-radius: 18px !important;
        padding: 28px 24px 22px 24px !important;
        background: rgba(255, 255, 255, 0.8) !important;
        box-shadow: 0 4px 16px rgba(44, 113, 136, 0.08) !important;
    }}

    .auth-card-title {{
        font-size: 32px !important;
        font-weight: 800 !important;
        color: #002b49 !important;
        text-align: center !important;
        margin: 0 0 6px 0 !important;
    }}

    .auth-card-subtitle {{
        font-size: 15px !important;
        font-weight: 500 !important;
        color: #123b52 !important;
        text-align: center !important;
        margin: 0 0 24px 0 !important;
    }}

    /* Primary Buttons */
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

    /* Secondary Buttons */
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

    /* History Session Container */
    .history-card {{
        background: #fbfdfe;
        border: 1px solid #d8e8ee;
        border-radius: 16px;
        padding: 16px 20px;
        margin-bottom: 18px;
        box-shadow: 0 3px 10px rgba(44, 113, 136, 0.06);
    }}

    .history-card-header {{
        color: #123b52;
        font-size: 16px;
        font-weight: 700;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid #eef5f8;
        padding-bottom: 8px;
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
# HELPER: ARCHIVE ACTIVE SESSION BEFORE CLEARING
# ============================================================

def flush_current_session_to_db():
    if st.session_state.user and st.session_state.messages and st.session_state.current_session_id:
        user_id = st.session_state.user["id"]
        # Only archive conversation turns (skip initial welcome message if alone)
        meaningful_messages = [
            m for m in st.session_state.messages
            if m.get("role") == "user" or (m.get("role") == "assistant" and m.get("intent") is not None)
        ]
        if meaningful_messages:
            database.archive_session(user_id, st.session_state.current_session_id, meaningful_messages)


# ============================================================
# SCREEN 1: UNAUTHENTICATED (LOGIN & REGISTER)
# ============================================================

if st.session_state.user is None:

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

    tab_login, tab_register = st.tabs(["Log In", "Register"])

    with tab_login:
        with st.form("form_login"):
            st.markdown(
                """
                <h2 class="auth-card-title">Log In</h2>
                <p class="auth-card-subtitle">Log in to your account to start chatting with MIA</p>
                """,
                unsafe_allow_html=True
            )
            login_email = st.text_input("Email Address", placeholder="name@example.com", key="login_email").strip()
            login_password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_password")
            login_submitted = st.form_submit_button("Log In", type="primary", use_container_width=True)

            if login_submitted:
                success, msg, user = database.login_user(login_email, login_password)
                if success:
                    st.session_state.user = user
                    st.session_state.chat_open = False
                    st.session_state.viewing_history = False
                    st.rerun()
                else:
                    st.error(msg)

    with tab_register:
        with st.form("form_register"):
            st.markdown(
                """
                <h2 class="auth-card-title">Register</h2>
                <p class="auth-card-subtitle">Create an account to start chatting with MIA</p>
                """,
                unsafe_allow_html=True
            )
            reg_name = st.text_input("Full Name (how MIA should call you)", placeholder="e.g. Alex", key="reg_name").strip()
            reg_email = st.text_input("Email Address", placeholder="name@example.com", key="reg_email").strip()
            reg_password = st.text_input("Password", type="password", placeholder="Minimum 6 characters", key="reg_password")
            reg_confirm = st.text_input("Confirm Password", type="password", placeholder="Re-enter password", key="reg_confirm")
            reg_submitted = st.form_submit_button("Register & Get Started", type="primary", use_container_width=True)

            if reg_submitted:
                success, msg, user = database.register_user(reg_name, reg_email, reg_password, reg_confirm)
                if success:
                    st.session_state.user = user
                    st.session_state.chat_open = False
                    st.session_state.viewing_history = False
                    st.success("Account created successfully! Welcome to MIA.")
                    st.rerun()
                else:
                    st.error(msg)

    st.markdown(
        '<div class="landing-footer">'
        'For general awareness only • Not a substitute for professional medical advice'
        '</div>',
        unsafe_allow_html=True
    )
    st.stop()


# ============================================================
# SCREEN 2: CONVERSATION HISTORY VIEW
# ============================================================

if st.session_state.viewing_history:

    if avatar_src:
        header_icon_html = f'<img class="chat-header-icon" src="{avatar_src}" alt="MIA">'
    else:
        header_icon_html = '<div style="font-size: 38px; margin-bottom: 6px; text-align: center;">🤖</div>'

    user_name = st.session_state.user.get("name", "there")

    st.markdown(
        f"""<div class="chat-header">
            {header_icon_html}
            <div class="chat-title">Conversation History</div>
            <div class="chat-subtitle">All saved discussions between {html.escape(user_name)} and MIA</div>
        </div>""",
        unsafe_allow_html=True
    )

    # Navigation buttons
    col_nav1, col_nav2 = st.columns(2)
    with col_nav1:
        if st.button("← Back to Chat", key="hist_back_chat", type="primary", use_container_width=True):
            st.session_state.viewing_history = False
            st.session_state.chat_open = True
            st.rerun()
    with col_nav2:
        if st.button("🏠 Back to Home", key="hist_back_home", type="secondary", use_container_width=True):
            st.session_state.viewing_history = False
            st.session_state.chat_open = False
            st.rerun()

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    past_sessions = database.get_user_history(st.session_state.user["id"])

    if not past_sessions:
        st.markdown(
            """
            <div style="text-align: center; padding: 40px 20px; color: #5c7e8e; background: #f8fbfa; border: 1.5px dashed #cde2eb; border-radius: 18px;">
                <div style="font-size: 40px; margin-bottom: 10px;">📜</div>
                <h4 style="color: #123b52; margin: 0 0 6px 0;">No conversation history yet</h4>
                <p style="font-size: 14px; margin: 0;">Start chatting with MIA, and all your past questions and answers will be safely saved here.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        for idx, sess in enumerate(past_sessions):
            msg_count = len(sess["messages"])
            session_time = sess.get("started_at", "Previous Session")
            expander_title = f"💬 Session {len(past_sessions) - idx} • {session_time} ({msg_count} messages)"

            with st.expander(expander_title, expanded=(idx == 0)):
                for msg in sess["messages"]:
                    content_escaped = html.escape(msg["content"]).replace("\n", "<br>")
                    if msg["role"] == "user":
                        st.markdown(
                            f'<div class="msg-row user"><div class="bubble user">{content_escaped}</div></div>',
                            unsafe_allow_html=True
                        )
                    else:
                        intent = msg.get("intent")
                        intent_html = ""
                        if intent:
                            intent_escaped = html.escape(intent.replace("_", " "))
                            intent_html = f'<span class="intent-badge">{intent_escaped}</span><br>'
                        avatar_tag = f'<img class="avatar" src="{avatar_src}" alt="MIA">' if avatar_src else ""
                        st.markdown(
                            f'<div class="msg-row mia">{avatar_tag}<div class="bubble mia">{intent_html}{content_escaped}</div></div>',
                            unsafe_allow_html=True
                        )

    st.markdown(
        '<div class="landing-footer">'
        'For general awareness only • Not a substitute for professional medical advice'
        '</div>',
        unsafe_allow_html=True
    )
    st.stop()


# ============================================================
# SCREEN 3: AUTHENTICATED LANDING PAGE
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

    user_name = st.session_state.user.get("name", "there")
    user_email = st.session_state.user.get("email", "")

    st.markdown(
        f"""
        <div class="user-greeting-pill">
            👋 Welcome, <b>{html.escape(user_name)}</b> <span style="font-size: 13px; color: #5c7e8e; font-weight: 400;">({html.escape(user_email)})</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    _, col_btn, _ = st.columns([1, 2, 1])
    with col_btn:
        if st.button("Ask away →", key="open_chat", type="primary", use_container_width=True):
            st.session_state.chat_open = True
            st.session_state.viewing_history = False
            # Generate a new session id if none exists
            if not st.session_state.current_session_id:
                st.session_state.current_session_id = uuid.uuid4().hex[:10]
            # Initialize personalized welcome message
            if not st.session_state.messages:
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": (
                            f"Hi {user_name}! I'm MIA 💊\n"
                            "Ask me about any medicine — its uses, "
                            "dosage, side effects or warnings."
                        ),
                        "intent": None
                    }
                )
            st.rerun()

    # See history and Logout buttons
    col_opt1, col_opt2 = st.columns(2)
    with col_opt1:
        if st.button("📜 See history", key="home_see_history", type="secondary", use_container_width=True):
            st.session_state.viewing_history = True
            st.rerun()
    with col_opt2:
        if st.button("🚪 Log out", key="home_logout", type="secondary", use_container_width=True):
            flush_current_session_to_db()
            st.session_state.user = None
            st.session_state.chat_open = False
            st.session_state.messages = []
            st.session_state.current_session_id = None
            st.session_state.viewing_history = False
            st.rerun()

    st.markdown(
        '<div class="landing-footer">'
        'For general awareness only • Not a substitute for professional medical advice'
        '</div>',
        unsafe_allow_html=True
    )

    st.stop()


# ============================================================
# SCREEN 4: CHAT PAGE
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
# ENSURE INITIALIZED WELCOME MESSAGE WITH USER NAME
# ============================================================

user_name = st.session_state.user.get("name", "there")
if not st.session_state.messages:
    if not st.session_state.current_session_id:
        st.session_state.current_session_id = uuid.uuid4().hex[:10]
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": (
                f"Hi {user_name}! I'm MIA 💊\n"
                "Ask me about any medicine — its uses, "
                "dosage, side effects or warnings."
            ),
            "intent": None
        }
    )


# ============================================================
# CHAT HISTORY DISPLAY
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
# CHAT INPUT & MESSAGE PROCESSING
# ============================================================

query = st.chat_input("Type your message about a medicine...")

if query:
    user_id = st.session_state.user["id"]
    session_id = st.session_state.current_session_id

    # Add user message to UI state and persist to database history
    st.session_state.messages.append(
        {
            "role": "user",
            "content": query
        }
    )
    database.save_message(user_id, session_id, "user", query, None)

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

    # Add assistant response to UI state and persist to database history
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": response,
            "intent": intent
        }
    )
    database.save_message(user_id, session_id, "assistant", response, intent)
    st.rerun()


# ============================================================
# CHAT CONTROLS (Back to MIA, See history, Clear conversation)
# ============================================================

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("← Back to MIA", key="back_home", type="secondary", use_container_width=True):
        flush_current_session_to_db()
        st.session_state.chat_open = False
        st.session_state.viewing_history = False
        st.session_state.messages = []
        st.session_state.current_session_id = uuid.uuid4().hex[:10]
        st.rerun()

with col2:
    if st.button("📜 See history", key="chat_see_history", type="secondary", use_container_width=True):
        flush_current_session_to_db()
        st.session_state.viewing_history = True
        st.rerun()

with col3:
    if st.button("Clear conversation", key="clear_chat", type="secondary", use_container_width=True):
        flush_current_session_to_db()
        st.session_state.messages = []
        st.session_state.current_session_id = uuid.uuid4().hex[:10]
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": (
                    f"Hi {user_name}! I'm MIA 💊\n"
                    "Ask me about any medicine — its uses, "
                    "dosage, side effects or warnings."
                ),
                "intent": None
            }
        )
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
