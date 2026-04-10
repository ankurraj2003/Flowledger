
import streamlit as st
import pandas as pd
import time
import base64
import os
from datetime import datetime

# ─── Module Imports ──────────────────────────────────────────
from config import APP_TITLE, APP_VERSION, APP_DESCRIPTION, get_api_key, logger
from extractor import extract_text_from_pdf, PDFExtractionError
from ai_engine import analyze_purchase_order, AIAnalysisError
from mapper import enrich_items_with_sku
from exporter import create_batch_excel_export

# =============================================================
#                      PAGE CONFIGURATION
# =============================================================
st.set_page_config(
    page_title=f"{APP_TITLE} V{APP_VERSION}",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================
#                   LOGO HELPER
# =============================================================
LOGO_PATH = os.path.join(os.path.dirname(__file__), "assets", "logo.png")


def get_logo_base64():
    """Return base64-encoded logo string for embedding in HTML."""
    try:
        with open(LOGO_PATH, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except FileNotFoundError:
        return None

def get_image_base64(filename):
    """Return base64-encoded string for embedding any asset image in HTML."""
    filepath = os.path.join(os.path.dirname(__file__), "assets", filename)
    try:
        with open(filepath, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception as e:
        logger.error(f"Error loading image {filename}: {e}")
        return ""

LOGO_B64 = get_logo_base64()
UPLOAD_B64 = get_image_base64("upload.png")
EXTRACT_B64 = get_image_base64("extract.png")
AI_ANALYSIS_B64 = get_image_base64("ai_analysis.png")
SKU_B64 = get_image_base64("sku.png")
TALLY_B64 = get_image_base64("tally.webp")
ZOHO_B64 = get_image_base64("zoho.png")
ERP_B64 = get_image_base64("erp.png")

# =============================================================
#                  INDUSTRIAL DARK THEME CSS
# =============================================================
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;500;600;700&family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
<style>
    /* ══════════════════════════════════════════════════════════
       GLOBAL / ROOT
       ══════════════════════════════════════════════════════════ */
    :root {
        --bg-primary:    #0d0d0d;
        --bg-secondary:  #1a1a1a;
        --bg-tertiary:   #252525;
        --bg-card:       #1e1e1e;
        --accent:        #FF6B00;
        --accent-light:  #FFA500;
        --accent-dim:    #cc5500;
        --text-primary:  #FFFFFF;
        --text-secondary:#B0B0B0;
        --text-muted:    #6a6a6a;
        --border:        #333333;
        --border-light:  #444444;
        --success:       #00C853;
        --warning:       #FFB300;
        --danger:        #FF1744;
        --info:          #00B0FF;
    }

    /* ── Main app background ─────────────────────────────── */
    .stApp, .main, [data-testid="stAppViewContainer"] {
        background-color: var(--bg-primary) !important;
        color: var(--text-primary) !important;
        font-family: 'Inter', sans-serif !important;
    }
    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1300px;
    }

    /* ── Headings ─────────────────────────────────────────── */
    h1, h2, h3, h4, h5, h6,
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        font-family: 'Rajdhani', sans-serif !important;
        font-weight: 700 !important;
        color: var(--text-primary) !important;
        text-transform: uppercase;
        letter-spacing: 1.5px;
    }
    p, span, label, .stMarkdown p {
        font-family: 'Inter', sans-serif !important;
        color: var(--text-secondary) !important;
    }

    /* ══════════════════════════════════════════════════════════
       SIDEBAR — Carbon-Fiber Dark
       ══════════════════════════════════════════════════════════ */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #111111 0%, #0a0a0a 40%, #111111 100%) !important;
        border-right: 2px solid var(--accent) !important;
    }
    [data-testid="stSidebar"]::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        background-image:
            radial-gradient(circle at 1px 1px, rgba(255,107,0,0.03) 1px, transparent 0);
        background-size: 20px 20px;
        pointer-events: none;
    }
    [data-testid="stSidebar"] * {
        color: #d0d0d0 !important;
    }
    [data-testid="stSidebar"] .stMarkdown h1,
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3 {
        color: var(--accent-light) !important;
        text-shadow: 0 0 12px rgba(255,107,0,0.25);
    }
    [data-testid="stSidebar"] hr {
        border-color: var(--border) !important;
        opacity: 0.5;
    }
    /* Sidebar text inputs */
    [data-testid="stSidebar"] .stTextInput input {
        background-color: #1a1a1a !important;
        border: 1px solid var(--border) !important;
        color: var(--text-primary) !important;
        border-radius: 6px;
        font-family: 'JetBrains Mono', monospace !important;
    }
    [data-testid="stSidebar"] .stTextInput input:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 8px rgba(255,107,0,0.3) !important;
    }

    /* ══════════════════════════════════════════════════════════
       STATUS BADGES
       ══════════════════════════════════════════════════════════ */
    .status-badge {
        display: inline-block;
        padding: 5px 16px;
        border-radius: 4px;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 1.2px;
        text-transform: uppercase;
        font-family: 'Rajdhani', sans-serif;
        border: 1px solid;
    }
    .badge-success {
        background: rgba(0,200,83,0.12);
        color: #00C853 !important;
        border-color: rgba(0,200,83,0.4);
    }
    .badge-warning {
        background: rgba(255,179,0,0.12);
        color: #FFB300 !important;
        border-color: rgba(255,179,0,0.4);
    }
    .badge-info {
        background: rgba(0,176,255,0.12);
        color: #00B0FF !important;
        border-color: rgba(0,176,255,0.4);
    }
    .badge-danger {
        background: rgba(255,23,68,0.12);
        color: #FF1744 !important;
        border-color: rgba(255,23,68,0.4);
    }
    .badge-steel {
        background: rgba(255,107,0,0.08);
        color: var(--accent) !important;
        border-color: rgba(255,107,0,0.35);
    }

    /* ══════════════════════════════════════════════════════════
       METRIC CARDS — Steel Framed
       ══════════════════════════════════════════════════════════ */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #1a1a1a 0%, #222222 100%) !important;
        border: 1px solid var(--border) !important;
        border-left: 3px solid var(--accent) !important;
        border-radius: 8px !important;
        padding: 18px !important;
        box-shadow: 0 4px 16px rgba(0,0,0,0.4);
        transition: all 0.3s ease;
    }
    div[data-testid="stMetric"]:hover {
        border-color: var(--accent) !important;
        box-shadow: 0 4px 20px rgba(255,107,0,0.15);
        transform: translateY(-1px);
    }
    div[data-testid="stMetric"] label {
        color: var(--text-muted) !important;
        font-family: 'Rajdhani', sans-serif !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        font-size: 0.78rem !important;
    }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: var(--text-primary) !important;
        font-family: 'Rajdhani', sans-serif !important;
        font-weight: 700 !important;
    }

    /* ══════════════════════════════════════════════════════════
       TABS — Industrial
       ══════════════════════════════════════════════════════════ */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0px;
        background-color: var(--bg-secondary);
        border-radius: 8px 8px 0 0;
        border-bottom: 2px solid var(--accent);
        padding: 0;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 0;
        padding: 14px 28px;
        font-weight: 700;
        font-family: 'Rajdhani', sans-serif !important;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        font-size: 0.9rem;
        color: var(--text-muted) !important;
        background-color: transparent;
        border-bottom: 3px solid transparent;
        transition: all 0.3s ease;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: var(--accent-light) !important;
        background-color: rgba(255,107,0,0.06);
    }
    .stTabs [aria-selected="true"] {
        color: var(--accent) !important;
        border-bottom: 3px solid var(--accent) !important;
        background-color: rgba(255,107,0,0.08) !important;
    }
    .stTabs [data-baseweb="tab-highlight"] {
        background-color: var(--accent) !important;
    }
    .stTabs [data-baseweb="tab-panel"] {
        background-color: var(--bg-primary);
        padding-top: 1.5rem;
    }

    /* ══════════════════════════════════════════════════════════
       FILE UPLOADER — Amber Dashed
       ══════════════════════════════════════════════════════════ */
    [data-testid="stFileUploader"] {
        border: 2px dashed var(--accent) !important;
        border-radius: 10px;
        padding: 32px 24px;
        background: rgba(255,107,0,0.03) !important;
        transition: all 0.3s ease;
        min-height: 200px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }
    [data-testid="stFileUploader"]:hover {
        background: rgba(255,107,0,0.06) !important;
        box-shadow: 0 0 20px rgba(255,107,0,0.1);
    }
    [data-testid="stFileUploader"] * {
        color: var(--text-secondary) !important;
    }
    /* Fix overlapping upload icon text */
    [data-testid="stFileUploader"] section button span {
        display: none !important;
    }
    [data-testid="stFileUploader"] section button::before {
        content: 'upload';
        font-family: 'Material Icons';
        margin-right: 8px;
        font-size: 1.2rem;
        vertical-align: middle;
    }

    /* ══════════════════════════════════════════════════════════
       BUTTONS — Industrial Amber
       ══════════════════════════════════════════════════════════ */
    .stButton > button[kind="primary"],
    .stDownloadButton > button {
        background: linear-gradient(135deg, var(--accent) 0%, var(--accent-dim) 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 6px !important;
        font-family: 'Rajdhani', sans-serif !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 1.5px !important;
        font-size: 0.95rem !important;
        padding: 12px 28px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 14px rgba(255,107,0,0.3) !important;
    }
    .stButton > button[kind="primary"]:hover,
    .stDownloadButton > button:hover {
        background: linear-gradient(135deg, var(--accent-light) 0%, var(--accent) 100%) !important;
        box-shadow: 0 6px 22px rgba(255,107,0,0.45) !important;
        transform: translateY(-1px) !important;
    }

    /* ══════════════════════════════════════════════════════════
       HERO BANNER — Dark Steel
       ══════════════════════════════════════════════════════════ */
    .hero-banner {
        background: linear-gradient(135deg, #111111 0%, #1a1a1a 50%, #0d0d0d 100%);
        border: 1px solid var(--border);
        border-left: 4px solid var(--accent);
        padding: 28px 36px;
        border-radius: 10px;
        margin-bottom: 28px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.5);
        position: relative;
        overflow: hidden;
    }
    .hero-banner::after {
        content: '';
        position: absolute;
        top: 0; right: 0;
        width: 250px; height: 100%;
        background: linear-gradient(135deg, transparent 0%, rgba(255,107,0,0.04) 100%);
        pointer-events: none;
    }
    .hero-banner .hero-content {
        display: flex;
        align-items: center;
        gap: 24px;
    }
    .hero-banner .hero-logo img {
        height: 44px;
        mix-blend-mode: screen;
        filter: contrast(1.2);
    }
    .hero-banner .hero-text h1 {
        color: #FFFFFF !important;
        margin: 0 !important;
        font-size: 1.8rem !important;
        font-family: 'Rajdhani', sans-serif !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 3px !important;
        line-height: 1 !important;
    }
    .hero-banner .hero-text .hero-accent {
        color: var(--accent) !important;
    }
    .hero-banner .hero-text p {
        color: var(--text-muted) !important;
        margin: 6px 0 0 0 !important;
        font-size: 0.88rem !important;
        letter-spacing: 2px !important;
        text-transform: uppercase !important;
        font-family: 'Rajdhani', sans-serif !important;
    }

    /* ══════════════════════════════════════════════════════════
       PROCESS STEPS — Industrial Cards
       ══════════════════════════════════════════════════════════ */
    .process-step {
        background: linear-gradient(135deg, #1a1a1a 0%, #222 100%);
        border: 1px solid var(--border);
        border-top: 3px solid var(--accent);
        padding: 24px 16px;
        margin: 12px 0;
        border-radius: 0 0 8px 8px;
        text-align: center;
        transition: all 0.3s ease;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 8px;
    }
    .process-step:hover {
        border-top-color: var(--accent-light);
        box-shadow: 0 4px 16px rgba(255,107,0,0.12);
        transform: translateY(-2px);
    }
    .process-step .step-icon {
        font-size: 1.8rem;
        display: block;
        margin-bottom: 12px;
    }
    .process-step .step-icon img {
        height: 38px;
        width: auto;
        opacity: 0.9;
        transition: transform 0.3s ease;
    }
    .process-step:hover .step-icon img {
        transform: scale(1.1);
        opacity: 1;
    }
    .process-step .step-num {
        font-family: 'Rajdhani', sans-serif;
        font-weight: 700;
        font-size: 0.7rem;
        color: var(--accent) !important;
        text-transform: uppercase;
        letter-spacing: 2px;
        display: block;
        margin-bottom: 4px;
    }
    .process-step .step-label {
        font-family: 'Rajdhani', sans-serif;
        font-weight: 600;
        font-size: 0.95rem;
        color: var(--text-primary) !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* ══════════════════════════════════════════════════════════
       EXPANDERS
       ══════════════════════════════════════════════════════════ */
    details, .streamlit-expanderHeader, [data-testid="stExpander"] {
        background-color: var(--bg-secondary) !important;
        border: 1px solid var(--border) !important;
        border-radius: 6px !important;
        color: var(--text-primary) !important;
    }
    [data-testid="stExpander"] summary .stMarkdown {
        color: var(--text-primary) !important;
        font-family: 'Rajdhani', sans-serif !important;
        font-weight: 600 !important;
    }

    /* ══════════════════════════════════════════════════════════
       DATA FRAMES / TABLES
       ══════════════════════════════════════════════════════════ */
    [data-testid="stDataFrame"],
    .stDataFrame {
        border: 1px solid var(--border) !important;
        border-radius: 6px !important;
    }

    /* ══════════════════════════════════════════════════════════
       DIVIDERS
       ══════════════════════════════════════════════════════════ */
    hr {
        border-color: var(--border) !important;
        opacity: 0.4;
    }

    /* ══════════════════════════════════════════════════════════
       ERP COMPAT CARD
       ══════════════════════════════════════════════════════════ */
    .erp-card {
        background: linear-gradient(135deg, #1a1a1a 0%, #222 100%);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 20px;
        text-align: center;
        transition: all 0.3s ease;
    }
    .erp-card:hover {
        border-color: var(--accent);
        box-shadow: 0 4px 16px rgba(255,107,0,0.1);
    }
    .erp-card .erp-icon {
        font-size: 2rem;
        display: block;
        margin-bottom: 8px;
    }
    .erp-card .erp-icon img {
        height: 48px;
        width: auto;
        border-radius: 4px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
    }
    .erp-card .erp-name {
        font-family: 'Rajdhani', sans-serif;
        font-weight: 700;
        font-size: 1rem;
        color: var(--text-primary) !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .erp-card .erp-status {
        font-size: 0.75rem;
        margin-top: 6px;
        display: inline-block;
        padding: 3px 10px;
        border-radius: 3px;
    }

    /* ══════════════════════════════════════════════════════════
       FOOTER
       ══════════════════════════════════════════════════════════ */
    .industrial-footer {
        background: var(--bg-secondary);
        border-top: 2px solid var(--accent);
        padding: 16px 0;
        margin-top: 2rem;
        text-align: center;
    }
    .industrial-footer p {
        color: var(--text-muted) !important;
        font-family: 'Rajdhani', sans-serif !important;
        font-size: 0.8rem !important;
        letter-spacing: 2px !important;
        text-transform: uppercase !important;
        margin: 0 !important;
    }
    .industrial-footer .footer-accent {
        color: var(--accent) !important;
    }

    /* ══════════════════════════════════════════════════════════
       ALERTS — Override Streamlit defaults
       ══════════════════════════════════════════════════════════ */
    .stAlert, [data-testid="stAlert"] {
        background-color: var(--bg-secondary) !important;
        border: 1px solid var(--border) !important;
        border-radius: 6px !important;
    }
    /* success alerts */
    div[data-baseweb="notification"][kind="positive"],
    .element-container .stSuccess {
        border-left: 3px solid var(--success) !important;
    }
    /* info alerts */
    div[data-baseweb="notification"][kind="info"],
    .element-container .stInfo {
        border-left: 3px solid var(--info) !important;
    }
    /* warning alerts */
    div[data-baseweb="notification"][kind="warning"],
    .element-container .stWarning {
        border-left: 3px solid var(--warning) !important;
    }
    /* error alerts */
    div[data-baseweb="notification"][kind="negative"],
    .element-container .stError {
        border-left: 3px solid var(--danger) !important;
    }

    /* ══════════════════════════════════════════════════════════
       PROGRESS BAR
       ══════════════════════════════════════════════════════════ */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, var(--accent) 0%, var(--accent-light) 100%) !important;
    }

    /* ══════════════════════════════════════════════════════════
       SECTION HEADER
       ══════════════════════════════════════════════════════════ */
    .section-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 16px;
    }
    .section-header .section-icon {
        font-size: 1.4rem;
        width: 42px;
        height: 42px;
        background: rgba(255,107,0,0.1);
        border: 1px solid rgba(255,107,0,0.3);
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .section-header .section-title {
        font-family: 'Rajdhani', sans-serif !important;
        font-weight: 700;
        font-size: 1.3rem;
        color: var(--text-primary) !important;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin: 0 !important;
    }
    .section-header .section-subtitle {
        font-size: 0.82rem;
        color: var(--text-muted) !important;
        margin: 2px 0 0 0 !important;
        letter-spacing: 0.5px;
    }

    /* Architecture table in sidebar */
    [data-testid="stSidebar"] table {
        background-color: rgba(26,26,26,0.8) !important;
        border: 1px solid var(--border) !important;
        border-radius: 6px;
    }
    [data-testid="stSidebar"] th {
        background-color: rgba(255,107,0,0.12) !important;
        color: var(--accent-light) !important;
        font-family: 'Rajdhani', sans-serif !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
    }
    [data-testid="stSidebar"] td {
        border-color: var(--border) !important;
    }

    /* caption */
    .stCaption, [data-testid="stCaptionContainer"] {
        color: var(--text-muted) !important;
    }
</style>
""", unsafe_allow_html=True)


# =============================================================
#                     SESSION STATE INIT
# =============================================================
def init_session_state():
    """Initialize all session state variables."""
    defaults = {
        "processed_invoices": [],      # List of validated invoice dicts
        "processing_complete": False,
        "api_key_input": "",
        "failed_files": [],            # Files that failed processing
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_session_state()


from datetime import datetime
from config import BUSINESS_NAME, GST_NO, VIEWER_USERNAME

# =============================================================
#                       HERO BANNER
# =============================================================
current_date = datetime.now().strftime("%d %b %Y")

st.markdown(f"""
<div class="hero-banner" style="display: flex; justify-content: space-between; align-items: flex-end;">
    <div class="hero-text">
        <h1>FLOW<span class="hero-accent">LEDGER</span> <span style="font-size:0.5em; color:#6a6a6a; vertical-align: middle;">V{APP_VERSION}</span></h1>
        <p>AI-Driven Batch Invoice Scanner → Consolidated ERP Ledger</p>
    </div>
    <div class="hero-right" style="text-align: right; color: #a1a1aa; font-family: 'Rajdhani', sans-serif; letter-spacing: 1px; font-size: 0.9rem; text-transform: uppercase; line-height: 1.4;">
        <div>{BUSINESS_NAME}</div>
        <div>GSTIN: {GST_NO}</div>
        <div>{current_date}</div>
        <div style="color: var(--accent); margin-top: 4px;">👤 {VIEWER_USERNAME}</div>
    </div>
</div>
""", unsafe_allow_html=True)


# =============================================================
#                       MAIN TABS
# =============================================================
tab_upload, tab_review, tab_export = st.tabs([
    "⬆  UPLOAD",
    "📋  REVIEW & EDIT",
    "⬇  EXPORT & SYNC",
])

# ─────────────────────────────────────────────────────────────
#                     TAB 1: UPLOAD
# ─────────────────────────────────────────────────────────────
with tab_upload:
    api_key = get_api_key()


    st.markdown("""
    <div class="section-header" style="margin-top: 20px;">
        <div class="section-icon">📄</div>
        <div>
            <p class="section-title">Upload Invoice PDFs</p>
            <p class="section-subtitle">Batch upload — process multiple invoices simultaneously</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Process steps visualization
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""<div class="process-step">
            <span class="step-icon"><img src="data:image/png;base64,{UPLOAD_B64}" alt="Upload"></span>
            <span class="step-num">Step 01</span>
            <span class="step-label">Upload PDFs</span>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class="process-step">
            <span class="step-icon"><img src="data:image/png;base64,{EXTRACT_B64}" alt="Extract"></span>
            <span class="step-num">Step 02</span>
            <span class="step-label">Extract Text</span>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""<div class="process-step">
            <span class="step-icon"><img src="data:image/png;base64,{AI_ANALYSIS_B64}" alt="AI Analysis"></span>
            <span class="step-num">Step 03</span>
            <span class="step-label">AI Analysis</span>
        </div>""", unsafe_allow_html=True)
    with col4:
        st.markdown(f"""<div class="process-step">
            <span class="step-icon"><img src="data:image/png;base64,{SKU_B64}" alt="SKU Mapping"></span>
            <span class="step-num">Step 04</span>
            <span class="step-label">SKU Mapping</span>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    uploaded_files = st.file_uploader(
        "Choose PDF file(s)",
        type=["pdf"],
        accept_multiple_files=True,
        help="Upload one or more text-based (digital) PDF invoices.",
        key="pdf_uploader",
    )

    if uploaded_files:
        st.info(f"📎 **{len(uploaded_files)} file(s)** selected for processing.", icon="📎")
        for f in uploaded_files:
            st.caption(f"  ▸ {f.name} — {len(f.getvalue()) / 1024:.1f} KB")

        if st.button("⚡ PROCESS ALL INVOICES", type="primary", use_container_width=True):
            if not api_key:
                st.error("❌ Please enter your Groq API Key in the sidebar.", icon="🔑")
            else:
                # Reset state for new batch
                st.session_state.processed_invoices = []
                st.session_state.failed_files = []

                total = len(uploaded_files)
                progress = st.progress(0, text=f"Processing 0/{total} invoices...")

                for idx, pdf_file in enumerate(uploaded_files):
                    file_name = pdf_file.name
                    st.markdown(f"---")

                    with st.status(f"⚙️ [{idx+1}/{total}] Processing **{file_name}**...", expanded=True) as status:
                        try:
                            # Step 1: Extract text
                            st.write(f"🔍 Extracting text from `{file_name}`...")
                            pdf_bytes = pdf_file.getvalue()
                            extracted_text = extract_text_from_pdf(pdf_bytes)
                            st.write(f"✅ Extracted **{len(extracted_text)}** characters.")

                            # Step 2: AI Analysis
                            st.write(f"🤖 Analyzing with Groq...")
                            po_data = analyze_purchase_order(extracted_text, api_key)
                            st.write(f"✅ Vendor: **{po_data.get('vendor_name', 'N/A')}** | Invoice#: **{po_data.get('invoice_no', 'N/A')}**")

                            # Step 3: SKU Mapping
                            st.write(f"🏷️ Mapping SKUs...")
                            items = po_data.get("items", [])
                            enriched = enrich_items_with_sku(items)
                            po_data["items"] = enriched
                            matched = sum(1 for i in enriched if i.get("internal_sku") != "MANUAL REVIEW")
                            st.write(f"✅ **{matched}/{len(enriched)}** items matched.")

                            # Tag with source file name
                            po_data["file_name"] = file_name

                            st.session_state.processed_invoices.append(po_data)
                            status.update(label=f"✅ [{idx+1}/{total}] {file_name} — Complete", state="complete")

                        except (PDFExtractionError, AIAnalysisError) as e:
                            st.session_state.failed_files.append({"file": file_name, "error": str(e)})
                            status.update(label=f"❌ [{idx+1}/{total}] {file_name} — Failed", state="error")
                            st.error(f"{file_name}: {str(e)}", icon="❌")

                        except Exception as e:
                            st.session_state.failed_files.append({"file": file_name, "error": str(e)})
                            status.update(label=f"❌ [{idx+1}/{total}] {file_name} — Failed", state="error")
                            st.error(f"{file_name}: Unexpected error — {str(e)}", icon="❌")

                    progress.progress(
                        (idx + 1) / total,
                        text=f"Processed {idx + 1}/{total} invoices..."
                    )

                st.session_state.processing_complete = True
                success = len(st.session_state.processed_invoices)
                failed = len(st.session_state.failed_files)
                st.success(
                    f"🎉 **Batch complete!** {success} succeeded, {failed} failed. "
                    f"Switch to the **Review & Edit** tab.",
                    icon="✅",
                )
                if success > 0:
                    st.balloons()

    elif st.session_state.processing_complete:
        count = len(st.session_state.processed_invoices)
        st.info(f"✅ **{count} invoice(s)** already processed. Check the **Review & Edit** tab.", icon="📋")


# ─────────────────────────────────────────────────────────────
#                  TAB 2: REVIEW & EDIT
# ─────────────────────────────────────────────────────────────
with tab_review:
    st.markdown("""
    <div class="section-header">
        <div class="section-icon">📊</div>
        <div>
            <p class="section-title">Review Extracted Invoices</p>
            <p class="section-subtitle">Inspect, verify, and edit AI-extracted data before export</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    invoices = st.session_state.processed_invoices

    if not st.session_state.processing_complete or not invoices:
        st.info("⬅️ Please upload and process PDF(s) in the **Upload** tab first.", icon="📤")
    else:
        # ── Batch Summary Metrics ──
        st.markdown("""
        <div class="section-header">
            <div class="section-icon">📈</div>
            <div><p class="section-title">Batch Summary</p></div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Invoices Processed", len(invoices))
        with col2:
            total_items = sum(len(inv.get("items", [])) for inv in invoices)
            st.metric("Total Line Items", total_items)
        with col3:
            grand_sum = sum(inv.get("grand_total", 0) for inv in invoices)
            st.metric("Total Value", f"$ {grand_sum:,.2f}")
        with col4:
            failed = len(st.session_state.failed_files)
            st.metric("Failed", failed)

        st.divider()

        # ── Invoice Ledger Table (one row per invoice) ──
        st.markdown("""
        <div class="section-header">
            <div class="section-icon">📋</div>
            <div>
                <p class="section-title">Invoice Ledger</p>
                <p class="section-subtitle">One row per invoice — exported format</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        ledger_data = []
        for inv in invoices:
            items = inv.get("items", [])
            item_summary = "; ".join(
                f"{it.get('desc', '')} (x{it.get('qty', 0)})"
                for it in items
            )
            ledger_data.append({
                "Source File": inv.get("file_name", ""),
                "Invoice No.": inv.get("invoice_no", "N/A"),
                "Vendor": inv.get("vendor_name", "N/A"),
                "Date": inv.get("date", "N/A"),
                "Due Date": inv.get("due_date", "N/A"),
                "Bill To": inv.get("bill_to", "N/A"),
                "Terms": inv.get("terms", "N/A"),
                "Items": len(items),
                "Items Summary": item_summary,
                "Sub Total ($)": inv.get("sub_total", 0),
                "Tax Rate (%)": inv.get("tax_rate", 0),
                "Tax ($)": inv.get("tax_amount", 0),
                "Grand Total ($)": inv.get("grand_total", 0),
            })

        df_ledger = pd.DataFrame(ledger_data)

        column_config = {
            "Sub Total ($)": st.column_config.NumberColumn(format="%.2f"),
            "Tax Rate (%)": st.column_config.NumberColumn(format="%.2f"),
            "Tax ($)": st.column_config.NumberColumn(format="%.2f"),
            "Grand Total ($)": st.column_config.NumberColumn(format="%.2f"),
            "Items": st.column_config.NumberColumn(format="%d"),
        }

        st.dataframe(
            df_ledger,
            column_config=column_config,
            use_container_width=True,
            hide_index=True,
        )

        st.divider()

        # ── Detailed view per invoice (expandable) ──
        st.markdown("""
        <div class="section-header">
            <div class="section-icon">🔎</div>
            <div><p class="section-title">Invoice Details</p></div>
        </div>
        """, unsafe_allow_html=True)

        for i, inv in enumerate(invoices):
            with st.expander(
                f"📄 {inv.get('file_name', '')} — {inv.get('vendor_name', 'N/A')} | "
                f"Invoice# {inv.get('invoice_no', 'N/A')} | "
                f"Total: $ {inv.get('grand_total', 0):,.2f}",
                expanded=False,
            ):
                # Header info
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.metric("Vendor", inv.get("vendor_name", "N/A"))
                with c2:
                    st.metric("Invoice #", inv.get("invoice_no", "N/A"))
                with c3:
                    st.metric("Date", inv.get("date", "N/A"))
                with c4:
                    st.metric("Grand Total", f"$ {inv.get('grand_total', 0):,.2f}")

                # Line items table
                items = inv.get("items", [])
                if items:
                    df_items = pd.DataFrame(items)
                    display_cols = ["desc", "details", "internal_sku", "qty", "unit", "price", "total"]
                    existing_cols = [c for c in display_cols if c in df_items.columns]
                    st.dataframe(df_items[existing_cols], use_container_width=True, hide_index=True)

                # Raw JSON
                with st.expander("🧬 Raw JSON", expanded=False):
                    st.json(inv)

        # ── Failed files (if any) ──
        if st.session_state.failed_files:
            st.divider()
            st.markdown("""
            <div class="section-header">
                <div class="section-icon">❌</div>
                <div><p class="section-title">Failed Files</p></div>
            </div>
            """, unsafe_allow_html=True)
            for fail in st.session_state.failed_files:
                st.error(f"**{fail['file']}**: {fail['error']}", icon="❌")


# ─────────────────────────────────────────────────────────────
#                   TAB 3: EXPORT & SYNC
# ─────────────────────────────────────────────────────────────
with tab_export:
    st.markdown("""
    <div class="section-header">
        <div class="section-icon">📥</div>
        <div>
            <p class="section-title">Export & Sync to ERP</p>
            <p class="section-subtitle">Download consolidated Excel or sync directly with your ERP</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    invoices = st.session_state.processed_invoices

    if not st.session_state.processing_complete or not invoices:
        st.info("⬅️ Please upload and process PDF(s) first.", icon="📤")
    else:
        st.markdown(
            f"Download **{len(invoices)} invoice(s)** as a consolidated Excel ledger "
            f"formatted for **Tally** and **Zoho Books** import."
        )

        st.divider()

        # ── ERP Compatibility Cards ──
        st.markdown("""
        <div class="section-header">
            <div class="section-icon">🔗</div>
            <div><p class="section-title">ERP Compatibility</p></div>
        </div>
        """, unsafe_allow_html=True)

        badge_col1, badge_col2, badge_col3 = st.columns(3)
        with badge_col1:
            st.markdown(f"""<div class="erp-card">
                <span class="erp-icon"><img src="data:image/webp;base64,{TALLY_B64}" alt="Tally Prime"></span>
                <span class="erp-name">Tally Prime</span><br>
                <span class="erp-status badge-success">● Compatible</span>
            </div>""", unsafe_allow_html=True)
        with badge_col2:
            st.markdown(f"""<div class="erp-card">
                <span class="erp-icon"><img src="data:image/png;base64,{ZOHO_B64}" alt="Zoho Books"></span>
                <span class="erp-name">Zoho Books</span><br>
                <span class="erp-status badge-success">● Compatible</span>
            </div>""", unsafe_allow_html=True)
        with badge_col3:
            st.markdown(f"""<div class="erp-card">
                <span class="erp-icon"><img src="data:image/png;base64,{ERP_B64}" alt="Custom ERP"></span>
                <span class="erp-name">Custom ERP</span><br>
                <span class="erp-status badge-info">● Configurable</span>
            </div>""", unsafe_allow_html=True)

        st.divider()

        # ── Excel Format Preview ──
        st.markdown("""
        <div class="section-header">
            <div class="section-icon">📋</div>
            <div>
                <p class="section-title">Excel Structure</p>
                <p class="section-subtitle">Two-sheet workbook format</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        | Sheet | Content |
        |-------|---------|
        | **Invoice Ledger** | One row per invoice — all header fields + totals |
        | **All Line Items** | Every line item across all invoices — with source tracking |
        """)

        st.divider()

        # ── Pre-Export Validation ──
        st.markdown("""
        <div class="section-header">
            <div class="section-icon">🔍</div>
            <div><p class="section-title">Pre-Export Validation</p></div>
        </div>
        """, unsafe_allow_html=True)

        issues = []
        for inv in invoices:
            fname = inv.get("file_name", "?")
            for j, item in enumerate(inv.get("items", []), start=1):
                if not isinstance(item.get("qty"), (int, float)):
                    issues.append(f"{fname} → Row {j}: Quantity is not a valid number.")
                if not isinstance(item.get("price"), (int, float)):
                    issues.append(f"{fname} → Row {j}: Price is not a valid number.")
                if item.get("internal_sku") == "MANUAL REVIEW":
                    issues.append(f"{fname} → Row {j}: SKU review needed — '{item.get('desc', '')}'")

        if issues:
            with st.expander(f"⚠️ {len(issues)} validation note(s)", expanded=False):
                for issue in issues:
                    st.warning(issue, icon="⚠️")
        else:
            st.success("✅ All validations passed — data is ready for export!", icon="✅")

        st.divider()

        # ── Generate & Download ──
        st.markdown("""
        <div class="section-header">
            <div class="section-icon">💾</div>
            <div><p class="section-title">Download Excel</p></div>
        </div>
        """, unsafe_allow_html=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Flowledger_Batch_{len(invoices)}inv_{timestamp}.xlsx"

        try:
            excel_buffer = create_batch_excel_export(invoices)

            st.download_button(
                label="⬇️  DOWNLOAD CONSOLIDATED EXCEL",
                data=excel_buffer,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.document",
                type="primary",
                use_container_width=True,
            )
            st.caption(f"📁 File name: `{filename}`")

        except Exception as e:
            st.error(f"❌ Failed to generate Excel file: {str(e)}", icon="❌")
            logger.error(f"Export failed: {e}")

        st.divider()

        # ── Final Summary ──
        st.markdown("""
        <div class="section-header">
            <div class="section-icon">📊</div>
            <div><p class="section-title">Export Summary</p></div>
        </div>
        """, unsafe_allow_html=True)

        s1, s2, s3, s4 = st.columns(4)
        with s1:
            st.metric("Invoices", len(invoices))
        with s2:
            total_items = sum(len(inv.get("items", [])) for inv in invoices)
            st.metric("Line Items", total_items)
        with s3:
            grand = sum(inv.get("grand_total", 0) for inv in invoices)
            st.metric("Total Value", f"$ {grand:,.2f}")
        with s4:
            st.metric("Format", "XLSX (2 sheets)")


# =============================================================
#                         FOOTER
# =============================================================
st.markdown(f"""
<div class="industrial-footer">
    <p>
        <span class="footer-accent">■</span> &nbsp;
        {APP_TITLE} V{APP_VERSION} &mdash; AI-Driven Batch Invoice Scanner
        &nbsp;|&nbsp; Built with Streamlit + Groq
        &nbsp;|&nbsp; &copy; {datetime.now().year}
        &nbsp; <span class="footer-accent">■</span>
    </p>
</div>
""", unsafe_allow_html=True)
# triggering reload
