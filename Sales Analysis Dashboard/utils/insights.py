# utils/insights.py
import pandas as pd

def generate_insights(df: pd.DataFrame, sales_col: str, profit_col: str, category_col: str):
    insights = []
    if df is None or df.empty:
        return insights

    # Basic checks
    if sales_col and sales_col in df.columns:
        total_sales = df[sales_col].sum()
        insights.append(f"Total sales (filtered): ${total_sales:,.0f}")
        # monthly trend if date present
        # Top categories
        if category_col and category_col in df.columns:
            top = df.groupby(category_col)[sales_col].sum().sort_values(ascending=False).head(3)
            top_items = ", ".join([f"{idx} (${v:,.0f})" for idx, v in top.items()])
            insights.append(f"Top categories by sales: {top_items}")
    else:
        insights.append("Cannot generate sales insights: Sales column missing.")

    if profit_col and profit_col in df.columns:
        total_profit = df[profit_col].sum()
        insights.append(f"Total profit (filtered): ${total_profit:,.0f}")
        if total_profit < 0:
            insights.append("Alert: Total profit is negative. Investigate high-cost or low-margin items.")
    else:
        insights.append("Profit column not found — profitability insights limited.")

    # Check high-impact customers/products
    if sales_col in df.columns:
        if 'customer' in " ".join(df.columns).lower():
            # try a customer column
            cust_cols = [c for c in df.columns if 'customer' in c.lower()]
            if cust_cols:
                cust = cust_cols[0]
                cust_sum = df.groupby(cust)[sales_col].sum().sort_values(ascending=False).head(5)
                insights.append("Top customers by sales: " + ", ".join([f"{c} (${v:,.0f})" for c, v in cust_sum.items()]))

    # Data quality note
    missing_cells = int(df.isna().sum().sum())
    if missing_cells > 0:
        insights.append(f"Data quality: {missing_cells} missing cells found. Consider imputation or cleaning.")
    else:
        insights.append("Data quality: No missing cells detected in the filtered dataset.")

    return insights
