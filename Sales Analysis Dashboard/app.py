# app.py
import streamlit as st
import pandas as pd
import datetime
from utils.cleaning import clean_data, explain_column_detection
from utils.eda import get_summary, total_missing, missing_values_chart
from utils import charts
from utils.report import export_report
from utils.insights import generate_insights

st.set_page_config(page_title="Sales Analysis Dashboard", layout="wide")

# ---------- UI ----------
st.title("📊 Sales Analysis Platform")
st.markdown("---")

uploaded_file = st.sidebar.file_uploader(
    "Upload your CSV or Excel file",
    type=["csv", "xlsx"],
    help="The platform automatically detects sales-related columns for analysis."
)

st.sidebar.markdown("### 🔧 Quick actions")
st.sidebar.info("Upload a CSV/XLSX with sales, date, category, profit columns (best if column names contain those words).")

# ---------- Main ----------
if uploaded_file:
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file, encoding='latin1')
        else:
            df = pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"Error loading file: {e}")
        st.stop()

    df_cleaned = clean_data(df.copy())
    df_cleaned.columns = df_cleaned.columns.str.strip().str.lower().str.replace('[^a-z0-9_]', '', regex=True)

    # Column detection
    col_info = explain_column_detection(df_cleaned)
    st.sidebar.subheader("📌 Column Detection Summary")
    for col_label, (col_name, score, reason) in col_info.items():
        if col_name:
            st.sidebar.success(f"{col_label}: {col_name} (Confidence: {score*100:.0f}%)")
            if reason:
                st.sidebar.caption(reason)
        else:
            st.sidebar.warning(f"{col_label}: Not detected")

    # Map columns
    sales_col = col_info.get("Sales Column", (None, 0, ""))[0]
    profit_col = col_info.get("Profit Column", (None, 0, ""))[0]
    category_col = col_info.get("Category Column", (None, 0, ""))[0]
    date_col = col_info.get("Date Column", (None, 0, ""))[0]

    if date_col:
        try:
            df_cleaned[date_col] = pd.to_datetime(df_cleaned[date_col], errors='coerce')
            df_cleaned = df_cleaned.dropna(subset=[date_col])
            df_cleaned = df_cleaned.sort_values(date_col)
        except Exception:
            st.sidebar.warning(f"Could not convert '{date_col}' to datetime.")

    df_filtered = df_cleaned.copy()

    # Filters
    if date_col:
        min_date = df_filtered[date_col].min().date()
        max_date = df_filtered[date_col].max().date()
        date_range = st.sidebar.date_input("Select Date Range", [min_date, max_date])
        if isinstance(date_range, list) and len(date_range) == 2:
            start, end = date_range
            df_filtered = df_filtered[(df_filtered[date_col] >= pd.to_datetime(start)) &
                                      (df_filtered[date_col] <= pd.to_datetime(end))]

    if category_col:
        cats = df_filtered[category_col].astype(str).unique().tolist()
        selected_cats = st.sidebar.multiselect("Select Categories", options=cats, default=cats)
        if selected_cats:
            df_filtered = df_filtered[df_filtered[category_col].astype(str).isin(selected_cats)]

    if sales_col:
        smin = float(df_filtered[sales_col].min())
        smax = float(df_filtered[sales_col].max())
        selected_range = st.sidebar.slider("Filter by Sales Amount", min_value=smin, max_value=smax, value=(smin, smax))
        df_filtered = df_filtered[(df_filtered[sales_col] >= selected_range[0]) &
                                  (df_filtered[sales_col] <= selected_range[1])]

    # Tabs
    tab1, tab_insights, tab2, tab3, tab4 = st.tabs(
        ["📊 KPIs & Charts", "💡 Insights", "🔬 EDA", "📄 Data Preview", "⬇️ Report Export"]
    )

    # ---------- TAB 1: KPIs & Charts ----------
    with tab1:
        st.header("Key Performance Indicators (KPIs)")
        kpi_cols = st.columns(4)
        kpis = {}

        # Total Sales
        if sales_col:
            total_sales = df_filtered[sales_col].sum()
            kpi_cols[0].metric("💰 Total Sales", f"${total_sales:,.0f}")
            kpis["Total Sales"] = f"${total_sales:,.0f}"
        else:
            kpi_cols[0].warning("No Sales column found")
            kpis["Total Sales"] = "Warning: Column not found"

        # Total Profit
        if profit_col:
            total_profit = df_filtered[profit_col].sum()
            kpi_cols[1].metric("📈 Total Profit", f"${total_profit:,.0f}")
            kpis["Total Profit"] = f"${total_profit:,.0f}"
        else:
            kpi_cols[1].warning("No Profit column found")
            kpis["Total Profit"] = "Warning: Column not found"

        # Avg Sales
        if sales_col and len(df_filtered) > 0:
            avg_sales = df_filtered[sales_col].mean()
            kpi_cols[2].metric("🛒 Avg. Sales per Record", f"${avg_sales:,.2f}")
            kpis["Average Sales"] = f"${avg_sales:,.2f}"
        else:
            kpi_cols[2].warning("No Sales column to calculate average")
            kpis["Average Sales"] = "Warning: Column not found"

        # Total Missing
        total_missing_count = total_missing(df_filtered)
        kpi_cols[3].metric("🗑️ Total Missing Cells", f"{total_missing_count:,}")
        kpis["Total Missing Cells"] = f"{total_missing_count:,}"

        st.markdown("---")
        st.header("Visualizations")

        # Sales Over Time & Distribution
        col_chart_1, col_chart_2 = st.columns(2)
        with col_chart_1:
            if date_col and sales_col:
                st.plotly_chart(charts.sales_over_time(df_filtered, date_col, sales_col), use_container_width=True)
            else:
                st.info("⏳ Skipping Sales Over Time: Requires Date & Sales columns.")
        with col_chart_2:
            if sales_col:
                st.plotly_chart(charts.sales_distribution_histogram(df_filtered, sales_col), use_container_width=True)
            else:
                st.info("📊 Skipping Sales Distribution.")

        # Category Sales & Donut
        col_chart_3, col_chart_4 = st.columns(2)
        with col_chart_3:
            if category_col and sales_col:
                st.plotly_chart(charts.category_sales_bar(df_filtered, category_col, sales_col), use_container_width=True)
        with col_chart_4:
            if category_col and sales_col:
                st.plotly_chart(charts.sales_pie_donut_chart(df_filtered, category_col, sales_col), use_container_width=True)

        # 3D scatter
        if sales_col and profit_col and category_col:
            st.plotly_chart(charts.sales_3d_scatter(df_filtered, sales_col, profit_col, category_col), use_container_width=True)

        # Drill-down
        st.markdown("### 🔎 Drill-Down Analysis")
        if category_col:
            clicked_category = st.selectbox("Select a Category to drill into",
                                            sorted(df_filtered[category_col].astype(str).unique()))
            df_drill = df_filtered[df_filtered[category_col].astype(str) == str(clicked_category)]

            product_col_candidates = [c for c in df_drill.columns if any(x in c for x in ["product", "item", "sku", "productname"])]
            product_col = product_col_candidates[0] if product_col_candidates else None

            st.subheader(f"Performance for: {clicked_category}")
            st.write(f"Records in selection: {len(df_drill):,}")

            if sales_col:
                st.plotly_chart(charts.sales_over_time(df_drill, date_col, sales_col) if date_col else charts.sales_distribution_histogram(df_drill, sales_col), use_container_width=True)

            if product_col:
                product_summary = df_drill.groupby(product_col)[sales_col].sum().reset_index().sort_values(by=sales_col, ascending=False).head(10)
                st.write("Top products in this category (by sales):")
                st.dataframe(product_summary)

        # ---------- Modern Geo Map ----------
        st.markdown("### 🌍 Geo Map")
        geo_candidates = [c for c in df_filtered.columns if any(k in c for k in ["country", "region", "location", "state", "city"])]
        if geo_candidates and sales_col:
            geo_col = geo_candidates[0]
            fig_geo = charts.sales_geo_map(df_filtered, geo_col, sales_col)
            if fig_geo:
                st.plotly_chart(fig_geo, use_container_width=True)
            else:
                st.info("🌍 Geo Map cannot be displayed.")
        else:
            st.info("🌍 No geographic column detected.")

    # ---------- TAB 2: Insights ----------
    with tab_insights:
        st.header("💡 Actionable Business Insights")
        insights_list = generate_insights(df_filtered, sales_col, profit_col, category_col)
        for insight in insights_list:
            if any(w in insight.lower() for w in ["drop", "loss", "urgent", "decline", "risk"]):
                st.warning(f"- {insight}")
            else:
                st.success(f"- {insight}")
        if not insights_list:
            st.info("No insights generated.")

    # ---------- TAB 3: EDA ----------
    with tab2:
        st.header("🔬 Exploratory Data Analysis (EDA)")
        st.subheader("Summary Statistics")
        st.dataframe(get_summary(df_filtered))

        st.subheader("Missing Values Analysis")
        missing_fig = missing_values_chart(df_filtered)
        if missing_fig:
            st.plotly_chart(missing_fig, use_container_width=True)
        else:
            st.info("No missing values to display.")

    # ---------- TAB 4: Data Preview ----------
    with tab3:
        st.header("📄 Data Preview")
        st.dataframe(df_filtered)

    # ---------- TAB 5: Report Export ----------
    with tab4:
        st.header("⬇️ Export Report")
        if st.button("Generate PDF Report"):
            filename = export_report(kpis)
            st.success(f"Report generated: {filename}")

else:
    st.info("📌 Please upload a CSV or Excel file to see the dashboard.")
