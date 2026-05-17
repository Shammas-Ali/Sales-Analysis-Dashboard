import streamlit as st
import pandas as pd
import numpy as np
import os
from datetime import datetime

from utils.cleaning import clean_data, explain_column_detection, data_quality_score
from utils.eda import (get_summary, total_missing, missing_values_chart,
                       correlation_heatmap, sales_trend_with_growth, profit_margin_trend)
from utils import charts
from utils.insights import generate_insights, generate_executive_summary
from utils.report import export_report
from utils.forecasting import run_forecast
from utils.chatbot import build_dataset_context, query_chatbot

# ------------------ CONFIG ------------------
# ⚡ MUST be first Streamlit call
st.set_page_config(
    page_title="Sales Intelligence Dashboard v2.0",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)
os.makedirs("reports", exist_ok=True)

# ------------------ CUSTOM CSS ------------------
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1e3a5f 0%, #2C5F8A 100%);
        padding: 1.2rem 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 1rem;
    }
    .main-header h1 { margin: 0; font-size: 1.8rem; }
    .main-header p { margin: 0; opacity: 0.85; font-size: 0.9rem; }
    .kpi-card {
        background: white;
        border: 1px solid #e0e7ef;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }
    .quality-badge {
        display: inline-block;
        padding: 4px 14px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 1.1rem;
    }
    .chat-msg-user {
        color: #000000 !important;
        background: #e8f0fe;
        padding: 8px 14px;
        border-radius: 12px 12px 2px 12px;
        margin: 4px 0;
        max-width: 80%;
        margin-left: auto;
        text-align: right;
    }
    .chat-msg-bot {
        color: #000000 !important;
        background: #f0f4f8;
        padding: 8px 14px;
        border-radius: 12px 12px 12px 2px;
        margin: 4px 0;
        max-width: 85%;
    }
    div[data-testid="stMetricValue"] { font-size: 1.4rem !important; }
</style>
""", unsafe_allow_html=True)

# ------------------ HEADER ------------------
st.markdown("""
<div class="main-header">
    <h1>📊 SALES INTELLIGENCE DASHBOARD</h1>
</div>
""", unsafe_allow_html=True)

# ==========================================
# ⚡ CACHED FUNCTIONS — run once per file
# ==========================================

@st.cache_data(show_spinner=False)
def load_and_clean(file_bytes: bytes, filename: str) -> pd.DataFrame:
    """Load and clean data. Cached by file content — only reruns when file changes."""
    import io
    if filename.endswith(".csv"):
        df_raw = pd.read_csv(io.BytesIO(file_bytes), encoding="latin1")
    else:
        df_raw = pd.read_excel(io.BytesIO(file_bytes))
    df = clean_data(df_raw)
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace("[^a-z0-9_]", "", regex=True)
    )
    return df


@st.cache_data(show_spinner=False)
def cached_column_detection(df: pd.DataFrame):
    return explain_column_detection(df)


@st.cache_data(show_spinner=False)
def cached_quality_score(df: pd.DataFrame):
    return data_quality_score(df)


@st.cache_data(show_spinner=False)
def cached_summary(df: pd.DataFrame):
    return get_summary(df)


@st.cache_data(show_spinner=False)
def cached_insights(df: pd.DataFrame, sales_col, profit_col, category_col):
    return generate_insights(df, sales_col, profit_col, category_col)


@st.cache_data(show_spinner=False)
def cached_exec_summary(df: pd.DataFrame, sales_col, profit_col, category_col, date_col):
    return generate_executive_summary(df, sales_col, profit_col, category_col, date_col)


@st.cache_data(show_spinner=False)
def cached_dataset_context(df: pd.DataFrame, sales_col, profit_col, category_col, date_col):
    return build_dataset_context(df, sales_col, profit_col, category_col, date_col)


@st.cache_data(show_spinner=False)
def cached_correlation_heatmap(df: pd.DataFrame):
    return correlation_heatmap(df)


# ------------------ SIDEBAR ------------------
with st.sidebar:
    st.image("https://img.icons8.com/fluency/48/combo-chart.png", width=40)
    st.markdown("### 📁 Data Upload")
    uploaded_file = st.file_uploader(
        "Upload CSV or Excel file",
        type=["csv", "xlsx"],
        help="Auto-detects sales, profit, date, category, and geo columns."
    )
    st.info("💡 Best results with columns: sales, profit, date, category, country/region.")

# ------------------ MAIN LOGIC ------------------
if not uploaded_file:
    st.markdown("""
    ### Welcome to Sales Intelligence Dashboard v2.0

    **What's New in v2.0:**
    - 🤖 **AI Chatbot** — Ask questions about your dataset in plain English
    - 📈 **ML Forecasting** — Prophet/ARIMA sales predictions with confidence intervals
    - 🏆 **Advanced KPIs** — Profit margin, growth indicators, best/worst category
    - 🚨 **Anomaly Detection** — Outlier and risk alerts
    - 📋 **Executive Summary** — Auto-generated business narrative
    - 🔬 **Enhanced EDA** — Correlation heatmap, growth trends, margin trends
    - 🎯 **Data Quality Score** — Completeness, uniqueness, consistency, validity

    **Upload a CSV or Excel file in the sidebar to get started.**
    """)
    st.stop()

# ---------- LOAD DATA (cached) ----------
try:
    file_bytes = uploaded_file.read()
    with st.spinner("🔄 Loading and cleaning data..."):
        df = load_and_clean(file_bytes, uploaded_file.name)
except Exception as e:
    st.error(f"❌ File loading error: {e}")
    st.stop()

# ---------- COLUMN DETECTION & QUALITY (cached) ----------
col_info = cached_column_detection(df)
dq = cached_quality_score(df)

with st.sidebar:
    st.markdown("---")
    st.markdown("### 📌 Column Detection")
    for label, (col, score, reason) in col_info.items():
        if col:
            st.success(f"**{label}:** `{col}` ({int(score*100)}%)")
        else:
            st.warning(f"**{label}:** Not detected")

    st.markdown("---")
    grade = dq.get("grade", "?")
    score_val = dq.get("overall", 0)
    color = "#27ae60" if score_val >= 75 else "#f39c12" if score_val >= 50 else "#e74c3c"
    st.markdown(f"""
    ### 🎯 Data Quality
    <span class="quality-badge" style="background:{color};color:white;">{score_val}/100 · Grade {grade}</span>
    """, unsafe_allow_html=True)
    for comp, val in dq.get("components", {}).items():
        st.progress(int(val), text=f"{comp}: {val}%")

sales_col     = col_info.get("Sales Column",    (None,))[0]
profit_col    = col_info.get("Profit Column",   (None,))[0]
category_col  = col_info.get("Category Column", (None,))[0]
date_col      = col_info.get("Date Column",     (None,))[0]
geo_col_detected = col_info.get("Geo Column",   (None,))[0]

# ---------- DATE HANDLING ----------
# ⚡ Only parse dates if not already datetime
if date_col and date_col in df.columns:
    if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col])
    df = df.sort_values(date_col)

df_filtered = df.copy()

# ---------- SIDEBAR FILTERS ----------
with st.sidebar:
    st.markdown("### 🔍 Filters")
    if date_col and date_col in df.columns:
        min_d, max_d = df[date_col].min(), df[date_col].max()
        date_range = st.date_input("Date Range", [min_d.date(), max_d.date()])
        if len(date_range) == 2:
            df_filtered = df_filtered[
                (df_filtered[date_col] >= pd.to_datetime(date_range[0])) &
                (df_filtered[date_col] <= pd.to_datetime(date_range[1]))
            ]

    if category_col and category_col in df.columns:
        categories = sorted(df[category_col].astype(str).unique().tolist())
        selected = st.multiselect("Categories", categories, default=categories)
        if selected:
            df_filtered = df_filtered[df_filtered[category_col].astype(str).isin(selected)]

    if sales_col and sales_col in df.columns:
        smin = float(df[sales_col].min())
        smax = float(df[sales_col].max())
        if smin < smax:
            selected_range = st.slider("Sales Amount Range", smin, smax, (smin, smax))
            df_filtered = df_filtered[
                (df_filtered[sales_col] >= selected_range[0]) &
                (df_filtered[sales_col] <= selected_range[1])
            ]

    st.markdown(f"**Rows after filter:** {len(df_filtered):,}")

# ⚡ Pre-compute commonly used cached values for the filtered dataframe
# These are cheap string/scalar results cached by df hash
insights       = cached_insights(df_filtered, sales_col, profit_col, category_col)
exec_summary   = cached_exec_summary(df_filtered, sales_col, profit_col, category_col, date_col)
summary_df     = cached_summary(df_filtered)
dataset_ctx    = cached_dataset_context(df_filtered, sales_col, profit_col, category_col, date_col)

# ------------------ TABS ------------------
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📊 KPIs & Charts",
    "📈 Forecasting",
    "💡 Insights",
    "🔬 EDA",
    "🤖 AI Chatbot",
    "📄 Data Preview",
    "⬇️ Report"
])

# ===========================
# TAB 1: KPIs & CHARTS
# ===========================
with tab1:
    st.header("KPIs")

    kpis = {}
    c1, c2, c3, c4, c5, c6 = st.columns(6)

    if sales_col and sales_col in df_filtered.columns:
        total_sales = df_filtered[sales_col].sum()
        c1.metric("💰 Total Sales", f"${total_sales:,.0f}")
        kpis["Total Sales"] = f"${total_sales:,.0f}"
    else:
        c1.warning("Sales N/A")
        total_sales = 0
        kpis["Total Sales"] = "Not detected"

    if profit_col and profit_col in df_filtered.columns:
        total_profit = df_filtered[profit_col].sum()
        c2.metric("📈 Total Profit", f"${total_profit:,.0f}",
                  delta="▲ Positive" if total_profit > 0 else "▼ Negative")
        kpis["Total Profit"] = f"${total_profit:,.0f}"
    else:
        c2.warning("Profit N/A")
        total_profit = 0
        kpis["Total Profit"] = "Not detected"

    if sales_col and profit_col and total_sales > 0:
        margin = (total_profit / total_sales) * 100
        c3.metric("🎯 Profit Margin", f"{margin:.1f}%")
        kpis["Profit Margin"] = f"{margin:.1f}%"
    else:
        c3.metric("🎯 Profit Margin", "N/A")
        kpis["Profit Margin"] = "N/A"

    if sales_col and sales_col in df_filtered.columns:
        avg_sales = df_filtered[sales_col].mean()
        c4.metric("📊 Avg Sales", f"${avg_sales:,.2f}")
        kpis["Average Sales"] = f"${avg_sales:,.2f}"

    c5.metric("📋 Total Records", f"{len(df_filtered):,}")
    kpis["Total Records"] = f"{len(df_filtered):,}"

    c6.metric("🎯 Data Quality", f"{dq['overall']}/100", delta=f"Grade {dq['grade']}")
    kpis["Data Quality Score"] = f"{dq['overall']}/100 ({dq['grade']})"
    kpis["Missing Cells"] = total_missing(df_filtered)

    if category_col and sales_col and category_col in df_filtered.columns:
        st.markdown("---")
        st.markdown("#### 🏆 Category Performance")
        cat_sales = df_filtered.groupby(category_col)[sales_col].sum().sort_values(ascending=False)
        cols_adv = st.columns(min(len(cat_sales), 5))
        for i, (cat, val) in enumerate(cat_sales.head(5).items()):
            rank = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][i]
            cols_adv[i].metric(f"{rank} {cat}", f"${val:,.0f}")
        kpis["Best Category"] = cat_sales.idxmax()
        kpis["Worst Category"] = cat_sales.idxmin()

    st.markdown("---")
    st.header("📊 Visual Analysis")

    # ⚡ chart_paths dict — images only saved on report generation, not every render
    chart_paths = {}

    colA, colB = st.columns(2)
    with colA:
        if sales_col and date_col and date_col in df_filtered.columns:
            fig_trend = sales_trend_with_growth(df_filtered, date_col, sales_col)
            if fig_trend:
                st.plotly_chart(fig_trend, use_container_width=True)
            else:
                fig = charts.sales_over_time(df_filtered, date_col, sales_col)
                st.plotly_chart(fig, use_container_width=True)
    with colB:
        if sales_col and sales_col in df_filtered.columns:
            fig_hist = charts.sales_distribution_histogram(df_filtered, sales_col)
            st.plotly_chart(fig_hist, use_container_width=True)

    colA, colB = st.columns(2)
    with colA:
        if category_col and sales_col and category_col in df_filtered.columns:
            fig_bar = charts.category_sales_bar(df_filtered, category_col, sales_col)
            st.plotly_chart(fig_bar, use_container_width=True)
    with colB:
        if category_col and sales_col and category_col in df_filtered.columns:
            fig_donut = charts.sales_pie_donut_chart(df_filtered, category_col, sales_col)
            st.plotly_chart(fig_donut, use_container_width=True)

    if sales_col and profit_col and date_col and date_col in df_filtered.columns:
        fig_margin = profit_margin_trend(df_filtered, date_col, sales_col, profit_col)
        if fig_margin:
            st.plotly_chart(fig_margin, use_container_width=True)

    if sales_col and profit_col and category_col and category_col in df_filtered.columns:
        fig3d = charts.sales_3d_scatter(df_filtered, sales_col, profit_col, category_col)
        st.plotly_chart(fig3d, use_container_width=True)

    # Drill-Down
    if category_col and category_col in df_filtered.columns:
        st.markdown("---")
        st.markdown("### 🔎 Drill-Down Analysis")
        clicked_category = st.selectbox("Select a Category to Drill Down",
                                         sorted(df_filtered[category_col].astype(str).unique()))
        df_drill = df_filtered[df_filtered[category_col].astype(str) == str(clicked_category)]

        col_d1, col_d2, col_d3 = st.columns(3)
        col_d1.metric("Records", f"{len(df_drill):,}")
        if sales_col:
            col_d2.metric("Sales", f"${df_drill[sales_col].sum():,.0f}")
        if profit_col:
            col_d3.metric("Profit", f"${df_drill[profit_col].sum():,.0f}")

        product_col_candidates = [c for c in df_drill.columns
                                   if any(x in c for x in ["product", "item", "sku", "productname", "name"])]
        product_col = product_col_candidates[0] if product_col_candidates else None

        if sales_col and date_col and date_col in df_drill.columns:
            st.plotly_chart(charts.sales_over_time(df_drill, date_col, sales_col), use_container_width=True)

        if product_col and sales_col:
            top_products = df_drill.groupby(product_col)[sales_col].sum().reset_index()
            top_products = top_products.sort_values(sales_col, ascending=False).head(10)
            top_products.columns = ["Product", "Sales"]
            st.markdown(f"**Top 10 Products in {clicked_category}:**")
            st.dataframe(top_products, use_container_width=True)

    # Geo Map
    geo_candidates = [c for c in df_filtered.columns
                      if any(k in c for k in ["country", "region", "location", "state", "city"])]
    if geo_candidates and sales_col:
        geo_col = geo_candidates[0]
        st.markdown("---")
        st.markdown("### 🌍 Geographic Sales Map")
        fig_geo = charts.sales_geo_map(df_filtered, geo_col, sales_col)
        if fig_geo:
            st.plotly_chart(fig_geo, use_container_width=True)
        else:
            st.info("Geographic column found but couldn't render map (check country name format).")
    else:
        st.info("ℹ️ No geographic column detected for geo map.")

# ===========================
# TAB 2: FORECASTING
# ===========================
with tab2:
    st.header("📈 Sales Forecasting")
    st.markdown("Predict future sales using machine learning (Prophet / ARIMA fallback).")

    if not date_col or not sales_col:
        st.warning("⚠️ Forecasting requires both a Date column and a Sales column to be detected.")
    else:
        col_f1, col_f2 = st.columns([1, 3])
        with col_f1:
            periods = st.slider("Forecast Periods (months)", min_value=1, max_value=24, value=6)
            freq_map = {"Monthly": "ME", "Quarterly": "QE", "Weekly": "W"}
            freq_label = st.selectbox("Aggregation Frequency", list(freq_map.keys()))
            freq = freq_map[freq_label]
            run_btn = st.button("🚀 Run Forecast", use_container_width=True)

        if run_btn or "forecast_result" in st.session_state:
            if run_btn:
                with st.spinner(f"Running {periods}-period forecast..."):
                    result = run_forecast(df_filtered, date_col, sales_col, periods=periods, freq=freq)
                    st.session_state["forecast_result"] = result

            result = st.session_state.get("forecast_result", {})

            if "error" in result:
                st.error(f"❌ {result['error']}")
            else:
                with col_f2:
                    st.plotly_chart(result["figure"], use_container_width=True)

                st.markdown(f"**Model Used:** `{result.get('model', 'Unknown')}`")
                st.markdown("**Forecast Table:**")
                fc_df = result["forecast"].copy()
                fc_df.columns = ["Date", "Predicted Sales", "Lower Bound", "Upper Bound"]
                fc_df["Date"] = pd.to_datetime(fc_df["Date"]).dt.strftime("%b %Y")
                for col in ["Predicted Sales", "Lower Bound", "Upper Bound"]:
                    fc_df[col] = fc_df[col].apply(lambda x: f"${x:,.0f}")
                st.dataframe(fc_df, use_container_width=True)

# ===========================
# TAB 3: INSIGHTS
# ===========================
with tab3:
    st.header("💡 Actionable Business Insights")

    with st.expander("📋 Executive Summary", expanded=True):
        st.markdown(exec_summary)

    st.markdown("---")
    st.markdown("### 🔍 Insights")
    for i in insights:
        if any(w in i for w in ["🚨", "Risk", "Negative", "NEGATIVE", "Loss", "low margin"]):
            st.error(i)
        elif any(w in i for w in ["⚠️", "Anomaly", "concentration", "missing"]):
            st.warning(i)
        else:
            st.success(i)

# ===========================
# TAB 4: EDA
# ===========================
with tab4:
    st.header("🔬 Exploratory Data Analysis")

    col_eda1, col_eda2 = st.columns(2)
    with col_eda1:
        st.markdown("#### 📊 Data Quality Breakdown")
        for comp, val in dq.get("components", {}).items():
            color = "🟢" if val >= 80 else "🟡" if val >= 60 else "🔴"
            st.markdown(f"{color} **{comp}:** {val}%")
            st.progress(int(val))
        det = dq.get("details", {})
        st.markdown(f"- Missing cells: `{det.get('missing_cells', 0):,}`")
        st.markdown(f"- Duplicate rows removed: `{df.attrs.get('duplicates_removed', 0):,}`")

    with col_eda2:
        st.markdown("#### 📋 Dataset Info")
        st.markdown(f"- **Rows:** {len(df_filtered):,}")
        st.markdown(f"- **Columns:** {df_filtered.shape[1]}")
        st.markdown(f"- **Numeric columns:** {len(df_filtered.select_dtypes(include='number').columns)}")
        st.markdown(f"- **Text columns:** {len(df_filtered.select_dtypes(include='object').columns)}")

    st.markdown("---")
    st.subheader("Summary Statistics")
    st.dataframe(summary_df, use_container_width=True)

    st.subheader("Missing Values")
    miss_fig = missing_values_chart(df_filtered)
    st.plotly_chart(miss_fig, use_container_width=True)

    st.subheader("Correlation Heatmap")
    corr_fig = cached_correlation_heatmap(df_filtered)
    if corr_fig:
        st.plotly_chart(corr_fig, use_container_width=True)
    else:
        st.info("Need at least 2 numeric columns for correlation heatmap.")

# ===========================
# TAB 5: AI CHATBOT
# ===========================
with tab5:
    st.header("🤖 AI Sales Assistant")
    st.markdown("Ask questions about your dataset in plain English.")

    import os as _os
    _api_key = ""
    try:
        _api_key = st.secrets.get("OPENROUTER_API_KEY", "")
    except Exception:
        pass
    if not _api_key:
        _api_key = _os.environ.get("OPENROUTER_API_KEY", "")
    if not _api_key:
        st.warning("⚠️ **OpenRouter API key not configured.** The AI chatbot requires an OpenRouter API key.")
        with st.expander("🔧 Setup Instructions (click to expand)", expanded=True):
            st.markdown("""
**Step 1:** Get your free API key at [openrouter.ai/keys](https://openrouter.ai/keys) → API Keys → Create Key

**Step 2 (Recommended) — Streamlit Secrets:**
Create `.streamlit/secrets.toml` in your project folder:
```toml
OPENROUTER_API_KEY = "sk-or-v1-..."
```
Then restart: `streamlit run app.py`

**Step 2 (Alternative) — Environment variable:**
```bash
set OPENROUTER_API_KEY=sk-or-v1-...
streamlit run app.py
```
""")
        st.stop()

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # ⚡ dataset_ctx is already computed above (cached) — no re-computation here

    st.markdown("**💬 Try asking:**")
    suggested = [
        "What are the top performing categories?",
        "Is the profit margin healthy?",
        "Which customers contribute most to revenue?",
        "What data quality issues should I worry about?",
        "Give me a 3-point executive summary."
    ]
    col_s = st.columns(len(suggested))
    for i, q in enumerate(suggested):
        if col_s[i].button(q, key=f"sugg_{i}", use_container_width=True):
            st.session_state["chat_input_prefill"] = q

    st.markdown("---")

    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f'<div class="chat-msg-user">🧑 {msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-msg-bot">🤖 {msg["content"]}</div>', unsafe_allow_html=True)

    prefill = st.session_state.pop("chat_input_prefill", "")
    user_input = st.text_input(
        "Ask a question about your sales data...",
        value=prefill,
        placeholder="e.g., Which category has the highest profit margin?",
        key="chat_user_input"
    )

    col_btn1, col_btn2 = st.columns([1, 5])
    send_btn = col_btn1.button("Send", use_container_width=True)
    col_btn2.button("Clear", on_click=lambda: st.session_state.update({"chat_history": []}),
                    use_container_width=False)

    if send_btn and user_input.strip():
        with st.spinner("Thinking..."):
            response = query_chatbot(user_input, dataset_ctx, st.session_state.chat_history)
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            st.session_state.chat_history.append({"role": "assistant", "content": response})
        st.rerun()

# ===========================
# TAB 6: DATA PREVIEW
# ===========================
with tab6:
    st.header("📄 Data Preview")
    search_term = st.text_input("🔍 Search in data", "")
    if search_term:
        mask = df_filtered.astype(str).apply(lambda col: col.str.contains(search_term, case=False)).any(axis=1)
        st.dataframe(df_filtered[mask], use_container_width=True)
        st.caption(f"Showing {mask.sum():,} matching rows")
    else:
        # ⚡ Show only first 500 rows for instant load; full data on demand
        max_rows = 500
        st.dataframe(df_filtered.head(max_rows), use_container_width=True)
        if len(df_filtered) > max_rows:
            st.caption(f"Showing first {max_rows:,} of {len(df_filtered):,} rows for performance. Use filters to narrow data.")
        else:
            st.caption(f"Showing all {len(df_filtered):,} rows")

# ===========================
# TAB 7: REPORT EXPORT
# ===========================
with tab7:
    st.header("⬇️ Generate Full PDF Report")
    st.markdown("Export a comprehensive PDF with KPIs, charts, insights, executive summary, and data quality score.")

    col_r1, col_r2 = st.columns(2)
    with col_r1:
        st.markdown("**Report will include:**")
        st.markdown("- ✅ Executive Summary\n- ✅ Data Quality Score\n- ✅ KPIs\n- ✅ Visual Charts\n- ✅ EDA Summary\n- ✅ Business Insights\n- ✅ Conclusions")
        if st.button("📥 Generate PDF Report", use_container_width=True, type="primary"):
            with st.spinner("Saving charts and generating report..."):
                # ⚡ Only save chart images when user explicitly requests a report
                chart_paths = {}
                try:
                    if sales_col and date_col and date_col in df_filtered.columns:
                        fig_trend = sales_trend_with_growth(df_filtered, date_col, sales_col)
                        if fig_trend:
                            fig_trend.write_image("reports/sales_trend_growth.png")
                            chart_paths["Sales Trend with Growth"] = "reports/sales_trend_growth.png"

                    if sales_col and sales_col in df_filtered.columns:
                        fig_hist = charts.sales_distribution_histogram(df_filtered, sales_col)
                        fig_hist.write_image("reports/sales_distribution.png")
                        chart_paths["Sales Distribution"] = "reports/sales_distribution.png"

                    if category_col and sales_col and category_col in df_filtered.columns:
                        fig_bar = charts.category_sales_bar(df_filtered, category_col, sales_col)
                        fig_bar.write_image("reports/category_sales.png")
                        chart_paths["Category Sales"] = "reports/category_sales.png"

                        fig_donut = charts.sales_pie_donut_chart(df_filtered, category_col, sales_col)
                        fig_donut.write_image("reports/category_donut.png")
                        chart_paths["Category Donut"] = "reports/category_donut.png"

                    miss_fig = missing_values_chart(df_filtered)
                    miss_fig.write_image("reports/missing_values.png")
                    chart_paths["Missing Values"] = "reports/missing_values.png"

                except Exception as chart_err:
                    st.warning(f"Some charts could not be saved: {chart_err}")

                kpis_export = {
                    "Total Sales":    f"${df_filtered[sales_col].sum():,.0f}"   if sales_col   else "N/A",
                    "Total Profit":   f"${df_filtered[profit_col].sum():,.0f}"  if profit_col  else "N/A",
                    "Profit Margin":  (f"{(df_filtered[profit_col].sum()/df_filtered[sales_col].sum()*100):.1f}%"
                                      if sales_col and profit_col and df_filtered[sales_col].sum() > 0 else "N/A"),
                    "Average Sales":  f"${df_filtered[sales_col].mean():,.2f}"  if sales_col   else "N/A",
                    "Total Records":  f"{len(df_filtered):,}",
                    "Missing Cells":  f"{total_missing(df_filtered):,}",
                    "Data Quality Score": f"{dq['overall']}/100 (Grade {dq['grade']})"
                }

                try:
                    filename = export_report(
                        kpis=kpis_export,
                        insights=insights,
                        chart_paths=chart_paths,
                        summary_df=summary_df.head(20),
                        executive_summary=exec_summary,
                        quality_score=dq
                    )
                    st.success(f"✅ Report generated: `{filename}`")
                    with open(filename, "rb") as f:
                        st.download_button(
                            label="⬇️ Download PDF Report",
                            data=f.read(),
                            file_name=os.path.basename(filename),
                            mime="application/pdf",
                            use_container_width=True
                        )
                except Exception as e:
                    st.error(f"Report generation failed: {e}")