# utils/eda.py
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go


def get_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Return a combined numeric + object summary dataframe."""
    if df is None or df.empty:
        return pd.DataFrame()

    numeric = df.select_dtypes(include=['number']).describe().T
    numeric = numeric[['count', 'mean', 'std', 'min', '25%', '50%', '75%', 'max']].fillna(0)
    numeric = numeric.reset_index().rename(columns={'index': 'column'})

    objs = []
    for col in df.select_dtypes(include=['object']).columns:
        objs.append({
            "column": col,
            "count": df[col].notna().sum(),
            "unique": df[col].nunique(),
            "top": df[col].mode().iloc[0] if not df[col].mode().empty else None
        })
    objs_df = pd.DataFrame(objs)
    if not objs_df.empty:
        objs_df = objs_df[['column', 'count', 'unique', 'top']]

    if not objs_df.empty:
        return pd.concat([numeric, objs_df], ignore_index=True, sort=False).fillna("")
    else:
        return numeric


def total_missing(df):
    if df is None or df.empty:
        return 0
    return int(df.isna().sum().sum())


def get_missing_values_table(df):
    if df is None or df.empty:
        return pd.DataFrame()
    mv = df.isna().sum().reset_index()
    mv.columns = ['column', 'missing_count']
    mv['missing_pct'] = (mv['missing_count'] / len(df) * 100).round(2)
    return mv.sort_values('missing_count', ascending=False)


def missing_values_chart(df):
    mv = get_missing_values_table(df)
    if mv is None or mv.empty or mv['missing_count'].sum() == 0:
        fig = px.bar(title="No Missing Values in Dataset")
        fig.update_layout(
            xaxis=dict(visible=False), yaxis=dict(visible=False),
            annotations=[dict(text="✅ No missing values detected", x=0.5, y=0.5,
                              showarrow=False, font=dict(size=20))]
        )
        return fig
    mv = mv[mv['missing_count'] > 0]
    fig = px.bar(mv, x='column', y='missing_pct',
                 title="Missing Values (%) by Column",
                 labels={'missing_pct': '% Missing', 'column': 'Column'},
                 text='missing_pct', color='missing_pct',
                 color_continuous_scale='Reds')
    fig.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
    fig.update_layout(yaxis_range=[0, 110], template="plotly_white")
    return fig


def correlation_heatmap(df: pd.DataFrame):
    """Generate a Plotly correlation heatmap for numeric columns."""
    numeric_df = df.select_dtypes(include='number')
    if numeric_df.shape[1] < 2:
        return None

    corr = numeric_df.corr()
    fig = go.Figure(data=go.Heatmap(
        z=corr.values,
        x=corr.columns.tolist(),
        y=corr.index.tolist(),
        colorscale="RdBu",
        zmid=0,
        text=[[f"{v:.2f}" for v in row] for row in corr.values],
        texttemplate="%{text}",
        colorbar=dict(title="Correlation")
    ))
    fig.update_layout(
        title="Correlation Heatmap (Numeric Columns)",
        template="plotly_white",
        height=450
    )
    return fig


def sales_trend_with_growth(df: pd.DataFrame, date_col: str, sales_col: str, freq: str = "ME"):
    """Monthly/period sales trend with MoM growth rate overlay."""
    if not date_col or not sales_col:
        return None
    ts = df[[date_col, sales_col]].copy()
    ts[date_col] = pd.to_datetime(ts[date_col], errors='coerce')
    ts = ts.dropna(subset=[date_col])
    ts = ts.set_index(date_col).resample(freq)[sales_col].sum().reset_index()
    ts.columns = ["period", "sales"]
    ts["growth_pct"] = ts["sales"].pct_change() * 100

    fig = go.Figure()
    fig.add_bar(x=ts["period"], y=ts["sales"], name="Sales", marker_color="#4C72B0", opacity=0.7)
    fig.add_scatter(x=ts["period"], y=ts["growth_pct"], name="MoM Growth %",
                    mode="lines+markers", yaxis="y2",
                    line=dict(color="#DD8452", width=2))
    fig.update_layout(
        title="Sales Trend with Month-over-Month Growth",
        xaxis_title="Period",
        yaxis=dict(title="Sales ($)"),
        yaxis2=dict(title="Growth (%)", overlaying="y", side="right", showgrid=False),
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        hovermode="x unified"
    )
    return fig


def profit_margin_trend(df: pd.DataFrame, date_col: str, sales_col: str, profit_col: str, freq: str = "ME"):
    """Profit margin trend over time."""
    if not date_col or not sales_col or not profit_col:
        return None
    ts = df[[date_col, sales_col, profit_col]].copy()
    ts[date_col] = pd.to_datetime(ts[date_col], errors='coerce')
    ts = ts.dropna(subset=[date_col])
    ts = ts.set_index(date_col)
    agg = ts.resample(freq).sum().reset_index()
    agg.columns = ["period", "sales", "profit"]
    agg["margin"] = np.where(agg["sales"] > 0, agg["profit"] / agg["sales"] * 100, 0)

    fig = go.Figure()
    fig.add_scatter(x=agg["period"], y=agg["margin"],
                    mode="lines+markers", name="Profit Margin %",
                    line=dict(color="#55A868", width=2),
                    fill="tozeroy", fillcolor="rgba(85,168,104,0.1)")
    fig.add_hline(y=0, line_dash="dash", line_color="red", annotation_text="Break-even")
    fig.update_layout(
        title="Profit Margin Trend Over Time",
        xaxis_title="Period", yaxis_title="Profit Margin (%)",
        template="plotly_white", hovermode="x unified"
    )
    return fig
