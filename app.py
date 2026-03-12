"""
=============================================================
Professional Streamlit interface with sidebar for project info
and configuration, plus 3 main tabs:
  1. Upload (multi-PDF batch)
  2. Review & Edit Table (consolidated ledger)
  3. Export & Sync (one-row-per-invoice Excel)
=============================================================
"""

import streamlit as st
import pandas as pd
import time
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
    page_icon="🔄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================
#                      CUSTOM CSS STYLING
# =============================================================
st.markdown("""
<style>
    /* ── Main container ───────────────────────────────── */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }

    /* ── Sidebar ──────────────────────────────────────── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    }
    [data-testid="stSidebar"] * {
        color: #e0e0e0 !important;
    }
    [data-testid="stSidebar"] .stMarkdown h1,
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3 {
        color: #ffffff !important;
    }

    /* ── Status badges ────────────────────────────────── */
    .status-badge {
        display: inline-block;
        padding: 4px 14px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    .badge-success {
        background: linear-gradient(135deg, #00b894, #00cec9);
        color: white;
    }
    .badge-warning {
        background: linear-gradient(135deg, #fdcb6e, #e17055);
        color: white;
    }
    .badge-info {
        background: linear-gradient(135deg, #74b9ff, #0984e3);
        color: white;
    }

    /* ── Metric cards ─────────────────────────────────── */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #f8f9fa, #e9ecef);
        border: 1px solid #dee2e6;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }

    /* ── Tab styling ──────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 10px 24px;
        font-weight: 600;
    }

    /* ── Upload zone ──────────────────────────────────── */
    [data-testid="stFileUploader"] {
        border: 2px dashed #74b9ff;
        border-radius: 12px;
        padding: 20px;
        background: #f0f7ff;
    }

    /* ── Header banner ────────────────────────────────── */
    .hero-banner {
        background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
        padding: 24px 32px;
        border-radius: 16px;
        margin-bottom: 24px;
        box-shadow: 0 4px 20px rgba(44,62,80,0.3);
    }
    .hero-banner h1 {
        color: white !important;
        margin: 0 !important;
        font-size: 2rem !important;
    }
    .hero-banner p {
        color: #bdc3c7 !important;
        margin: 4px 0 0 0 !important;
    }

    /* ── Process steps ────────────────────────────────── */
    .process-step {
        background: #f8f9fa;
        border-left: 4px solid #3498db;
        padding: 12px 16px;
        margin: 8px 0;
        border-radius: 0 8px 8px 0;
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


# =============================================================
#                         SIDEBAR
# =============================================================
with st.sidebar:
    # ── Project Info ──
    st.markdown("## 🔄 Flowledger")
    st.markdown(f"**Version** `{APP_VERSION}`")
    st.markdown(f"_{APP_DESCRIPTION}_")
    st.divider()

    # ── Configuration ──
    st.markdown("### ⚙️ Configuration")
    api_key_input = st.text_input(
        "Google Gemini API Key",
        type="password",
        placeholder="Enter your API key...",
        help="Get your key from https://aistudio.google.com/app/apikey",
        key="api_key_widget",
    )

    api_key = get_api_key(override=api_key_input)
    if api_key:
        st.success("✅ API Key configured", icon="🔑")
    else:
        st.warning("⚠️ API Key required", icon="🔑")

    st.divider()

    # ── Architecture Info ──
    st.markdown("### 🏗️ Architecture")
    st.markdown("""
    | Module | Purpose |
    |--------|---------|
    | `config` | API keys & env vars |
    | `extractor` | PDF → text |
    | `ai_engine` | Text → JSON (Gemini) |
    | `mapper` | SKU matching |
    | `exporter` | JSON → Excel |
    | `app` | Streamlit UI |
    """)

    st.divider()

    # ── Pipeline Status ──
    st.markdown("### 📊 Pipeline Status")
    inv_count = len(st.session_state.processed_invoices)
    if st.session_state.processing_complete and inv_count > 0:
        st.markdown(
            f'<span class="status-badge badge-success">✅ {inv_count} invoice(s)</span>',
            unsafe_allow_html=True,
        )
    elif inv_count > 0:
        st.markdown('<span class="status-badge badge-warning">⏳ In Progress</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-badge badge-info">💤 Idle</span>', unsafe_allow_html=True)


# =============================================================
#                       HERO BANNER
# =============================================================
st.markdown("""
<div class="hero-banner">
    <h1>🔄 Flowledger V1.0</h1>
    <p>AI-Driven Batch Invoice Scanner → Consolidated ERP Ledger</p>
</div>
""", unsafe_allow_html=True)


# =============================================================
#                       MAIN TABS
# =============================================================
tab_upload, tab_review, tab_export = st.tabs([
    "📤  1. Upload",
    "📝  2. Review & Edit Table",
    "📥  3. Export & Sync",
])

# ─────────────────────────────────────────────────────────────
#                     TAB 1: UPLOAD
# ─────────────────────────────────────────────────────────────
with tab_upload:
    st.markdown("### 📄 Upload Invoice PDFs (Batch)")
    st.markdown(
        "Upload **one or multiple** Invoice/PO PDFs. Flowledger will process each one and "
        "create a **consolidated ledger** — one row per invoice in the exported Excel."
    )

    # Process steps visualization
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown('<div class="process-step">📄 <b>Step 1</b><br>Upload PDFs</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="process-step">🔍 <b>Step 2</b><br>Extract Text</div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="process-step">🤖 <b>Step 3</b><br>AI Analysis</div>', unsafe_allow_html=True)
    with col4:
        st.markdown('<div class="process-step">✅ <b>Step 4</b><br>SKU Mapping</div>', unsafe_allow_html=True)

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
            st.caption(f"  • {f.name} — {len(f.getvalue()) / 1024:.1f} KB")

        if st.button("🚀 Process All Invoices", type="primary", use_container_width=True):
            if not api_key:
                st.error("❌ Please enter your Google Gemini API Key in the sidebar.", icon="🔑")
            else:
                # Reset state for new batch
                st.session_state.processed_invoices = []
                st.session_state.failed_files = []

                total = len(uploaded_files)
                progress = st.progress(0, text=f"Processing 0/{total} invoices...")

                for idx, pdf_file in enumerate(uploaded_files):
                    file_name = pdf_file.name
                    st.markdown(f"---")

                    with st.status(f"📄 [{idx+1}/{total}] Processing **{file_name}**...", expanded=True) as status:
                        try:
                            # Step 1: Extract text
                            st.write(f"🔍 Extracting text from `{file_name}`...")
                            pdf_bytes = pdf_file.getvalue()
                            extracted_text = extract_text_from_pdf(pdf_bytes)
                            st.write(f"✅ Extracted **{len(extracted_text)}** characters.")

                            # Step 2: AI Analysis
                            st.write(f"🤖 Analyzing with Gemini...")
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
                            status.update(label=f"✅ [{idx+1}/{total}] {file_name} — done!", state="complete")

                        except (PDFExtractionError, AIAnalysisError) as e:
                            st.session_state.failed_files.append({"file": file_name, "error": str(e)})
                            status.update(label=f"❌ [{idx+1}/{total}] {file_name} — failed", state="error")
                            st.error(f"{file_name}: {str(e)}", icon="❌")

                        except Exception as e:
                            st.session_state.failed_files.append({"file": file_name, "error": str(e)})
                            status.update(label=f"❌ [{idx+1}/{total}] {file_name} — failed", state="error")
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
    st.markdown("### 📊 Review Extracted Invoices")

    invoices = st.session_state.processed_invoices

    if not st.session_state.processing_complete or not invoices:
        st.info("📤 Please upload and process PDF(s) in the **Upload** tab first.", icon="⬅️")
    else:
        # ── Batch Summary Metrics ──
        st.markdown("#### 📈 Batch Summary")
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
        st.markdown("#### 📋 Invoice Ledger (one row per invoice)")
        st.caption("This is the format that will be exported to Excel.")

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
        st.markdown("#### 🔎 Invoice Details (expandable)")
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
            st.markdown("#### ❌ Failed Files")
            for fail in st.session_state.failed_files:
                st.error(f"**{fail['file']}**: {fail['error']}", icon="❌")


# ─────────────────────────────────────────────────────────────
#                   TAB 3: EXPORT & SYNC
# ─────────────────────────────────────────────────────────────
with tab_export:
    st.markdown("### 📥 Export & Sync to ERP")

    invoices = st.session_state.processed_invoices

    if not st.session_state.processing_complete or not invoices:
        st.info("📤 Please upload and process PDF(s) first.", icon="⬅️")
    else:
        st.markdown(
            f"Download **{len(invoices)} invoice(s)** as a consolidated Excel ledger "
            f"formatted for **Tally** and **Zoho Books** import."
        )

        st.divider()

        # ── ERP Compatibility Badges ──
        st.markdown("#### 🔗 ERP Compatibility")
        badge_col1, badge_col2, badge_col3 = st.columns(3)
        with badge_col1:
            st.markdown('<span class="status-badge badge-success">✅ Tally Prime</span>', unsafe_allow_html=True)
        with badge_col2:
            st.markdown('<span class="status-badge badge-success">✅ Zoho Books</span>', unsafe_allow_html=True)
        with badge_col3:
            st.markdown('<span class="status-badge badge-info">ℹ️ Custom ERP</span>', unsafe_allow_html=True)

        st.divider()

        # ── Excel Format Preview ──
        st.markdown("#### 📋 Excel Structure")
        st.markdown("""
        The exported Excel contains **2 sheets**:

        | Sheet | Content |
        |-------|---------|
        | **Invoice Ledger** | One row per invoice — all header fields + totals |
        | **All Line Items** | Every line item across all invoices — with source tracking |
        """)

        st.divider()

        # ── Pre-Export Validation ──
        st.markdown("#### 🔍 Pre-Export Validation")
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
        st.markdown("#### 💾 Download Excel")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Flowledger_Batch_{len(invoices)}inv_{timestamp}.xlsx"

        try:
            excel_buffer = create_batch_excel_export(invoices)

            st.download_button(
                label="⬇️  Download Consolidated Excel",
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
        st.markdown("#### 📊 Export Summary")
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
st.divider()
st.markdown(
    f"""
    <div style="text-align: center; color: #7f8c8d; font-size: 0.85rem; padding: 8px 0;">
        <b>{APP_TITLE} V{APP_VERSION}</b> — AI-Driven Batch Invoice Scanner
        &nbsp;|&nbsp; Built with Streamlit + Google Gemini
        &nbsp;|&nbsp; © {datetime.now().year}
    </div>
    """,
    unsafe_allow_html=True,
)
