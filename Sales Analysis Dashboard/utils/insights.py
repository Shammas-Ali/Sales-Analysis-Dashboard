# utils/insights.py
import pandas as pd
import numpy as np


def generate_insights(df: pd.DataFrame, sales_col: str, profit_col: str, category_col: str) -> list:
    """Generate enhanced business insights with anomaly detection."""
    insights = []
    if df is None or df.empty:
        return insights

    if sales_col and sales_col in df.columns:
        total_sales = df[sales_col].sum()
        avg_sales = df[sales_col].mean()
        insights.append(f"💰 Total sales (filtered): ${total_sales:,.0f}")

        # Outlier detection using IQR
        q1 = df[sales_col].quantile(0.25)
        q3 = df[sales_col].quantile(0.75)
        iqr = q3 - q1
        outliers = df[(df[sales_col] < q1 - 1.5 * iqr) | (df[sales_col] > q3 + 1.5 * iqr)]
        if len(outliers) > 0:
            insights.append(f"⚠️ Anomaly: {len(outliers)} outlier transactions detected (IQR method). Review for data entry errors or exceptional deals.")

        if category_col and category_col in df.columns:
            cat_sales = df.groupby(category_col)[sales_col].sum().sort_values(ascending=False)
            top = cat_sales.head(3)
            top_items = ", ".join([f"{idx} (${v:,.0f})" for idx, v in top.items()])
            insights.append(f"📊 Top 3 categories by sales: {top_items}")

            # Best & worst performing category
            best_cat = cat_sales.idxmax()
            worst_cat = cat_sales.idxmin()
            insights.append(f"🏆 Best performing category: {best_cat} (${cat_sales[best_cat]:,.0f})")
            insights.append(f"📉 Lowest performing category: {worst_cat} (${cat_sales[worst_cat]:,.0f})")

            # Category performance ranking
            insights.append(f"📋 Category Performance Ranking: " +
                            " > ".join([f"{k}" for k in cat_sales.index.tolist()[:5]]))
    else:
        insights.append("❌ Cannot generate sales insights: Sales column missing.")

    if profit_col and profit_col in df.columns:
        total_profit = df[profit_col].sum()
        insights.append(f"📈 Total profit (filtered): ${total_profit:,.0f}")

        if total_profit < 0:
            insights.append("🚨 Risk Alert: Total profit is NEGATIVE. Investigate high-cost or low-margin items immediately.")

        if sales_col and sales_col in df.columns:
            total_sales = df[sales_col].sum()
            if total_sales > 0:
                margin = (total_profit / total_sales) * 100
                if margin < 5:
                    insights.append(f"⚠️ Low margin alert: Profit margin is only {margin:.1f}%. Industry benchmark is typically >15%.")
                elif margin > 30:
                    insights.append(f"✅ Strong margin: {margin:.1f}% profit margin — excellent performance.")
                else:
                    insights.append(f"✅ Profit margin: {margin:.1f}%")

        # Negative profit categories
        if category_col and category_col in df.columns:
            neg_cats = df.groupby(category_col)[profit_col].sum()
            neg_cats = neg_cats[neg_cats < 0]
            if len(neg_cats) > 0:
                names = ", ".join(neg_cats.index.tolist())
                insights.append(f"🚨 Loss Alert: Categories with negative profit: {names}. Consider discontinuing or repricing.")
    else:
        insights.append("ℹ️ Profit column not found — profitability insights limited.")

    # Customer intelligence
    if sales_col and sales_col in df.columns:
        cust_cols = [c for c in df.columns if 'customer' in c.lower() and 'id' not in c.lower()]
        if not cust_cols:
            cust_cols = [c for c in df.columns if 'customer' in c.lower()]
        if cust_cols:
            cust = cust_cols[0]
            cust_sum = df.groupby(cust)[sales_col].sum().sort_values(ascending=False)
            top_customers = cust_sum.head(5)
            insights.append("👥 Top 5 customers: " + ", ".join([f"{c} (${v:,.0f})" for c, v in top_customers.items()]))

            # Revenue concentration
            total = cust_sum.sum()
            top5_share = top_customers.sum() / total * 100 if total > 0 else 0
            if top5_share > 50:
                insights.append(f"⚠️ Revenue concentration risk: Top 5 customers account for {top5_share:.1f}% of total sales.")

    # Data quality note
    missing_cells = int(df.isna().sum().sum())
    total_cells = df.shape[0] * df.shape[1]
    missing_pct = missing_cells / total_cells * 100 if total_cells > 0 else 0
    if missing_cells > 0:
        if missing_pct > 20:
            insights.append(f"🚨 Data quality risk: {missing_pct:.1f}% cells missing ({missing_cells:,} cells). Reliability of insights may be impacted.")
        else:
            insights.append(f"⚠️ Data quality: {missing_cells:,} missing cells ({missing_pct:.1f}%). Consider imputation.")
    else:
        insights.append("✅ Data quality: No missing values detected in the filtered dataset.")

    return insights


def generate_executive_summary(df: pd.DataFrame, sales_col: str, profit_col: str,
                                category_col: str, date_col: str) -> str:
    """
    Auto-generate a professional executive summary paragraph.
    """
    if df is None or df.empty:
        return "No data available for executive summary."

    parts = []

    # Period
    if date_col and date_col in df.columns:
        dmin = pd.to_datetime(df[date_col], errors='coerce').min()
        dmax = pd.to_datetime(df[date_col], errors='coerce').max()
        if pd.notna(dmin) and pd.notna(dmax):
            parts.append(f"This report covers the period from {dmin.strftime('%B %Y')} to {dmax.strftime('%B %Y')}.")

    # Sales
    if sales_col and sales_col in df.columns:
        total = df[sales_col].sum()
        avg = df[sales_col].mean()
        parts.append(f"Total sales achieved: **${total:,.0f}** across {len(df):,} transactions (avg ${avg:,.2f}/transaction).")

    # Profit
    if profit_col and profit_col in df.columns and sales_col and sales_col in df.columns:
        profit = df[profit_col].sum()
        sales = df[sales_col].sum()
        margin = (profit / sales * 100) if sales > 0 else 0
        sentiment = "strong" if margin > 20 else "moderate" if margin > 10 else "low"
        parts.append(f"Total profit stands at **${profit:,.0f}** with a {sentiment} profit margin of **{margin:.1f}%**.")

    # Best category
    if category_col and category_col in df.columns and sales_col and sales_col in df.columns:
        best = df.groupby(category_col)[sales_col].sum().idxmax()
        best_val = df.groupby(category_col)[sales_col].sum().max()
        parts.append(f"The highest-revenue category is **{best}** contributing ${best_val:,.0f}.")

    # Risk / recommendation
    if profit_col and profit_col in df.columns:
        if df[profit_col].sum() < 0:
            parts.append("⚠️ Critical: Overall profitability is negative. Immediate cost review is recommended.")
        else:
            parts.append("Business performance is within acceptable parameters. Focus should be on scaling high-margin categories and customer retention.")

    return " ".join(parts) if parts else "Upload data to generate executive summary."
