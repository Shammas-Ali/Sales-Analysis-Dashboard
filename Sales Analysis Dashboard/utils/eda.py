# utils/eda.py
import pandas as pd
import plotly.express as px


def get_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Return a combined numeric + object summary dataframe for display"""
    if df is None or df.empty:
        return pd.DataFrame()

    # Numeric summary
    numeric = df.select_dtypes(include=['number']).describe().T
    numeric = numeric[['count', 'mean', 'std', 'min', '25%', '50%', '75%', 'max']].fillna(0)
    numeric = numeric.reset_index().rename(columns={'index': 'column'})

    # Text column summary
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

    # Combine numeric + object summary
    if not objs_df.empty:
        return pd.concat([numeric, objs_df], ignore_index=True, sort=False).fillna("")
    else:
        return numeric


def total_missing(df):
    """Return total number of missing cells in the dataframe"""
    if df is None or df.empty:
        return 0
    return int(df.isna().sum().sum())


def get_missing_values_table(df):
    """Return a table with missing count and percentage per column"""
    if df is None or df.empty:
        return pd.DataFrame()
    mv = df.isna().sum().reset_index()
    mv.columns = ['column', 'missing_count']
    mv['missing_pct'] = (mv['missing_count'] / len(df) * 100).round(2)
    return mv.sort_values('missing_count', ascending=False)


def missing_values_chart(df):
    """Return a Plotly bar chart showing missing % by column."""
    mv = get_missing_values_table(df)

    # If no data or no missing values, return a placeholder figure
    if mv is None or mv.empty or mv['missing_count'].sum() == 0:
        fig = px.bar(title="No Missing Values in Dataset")
        fig.update_layout(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            annotations=[dict(
                text="No missing values detected",
                x=0.5, y=0.5, showarrow=False, font=dict(size=20)
            )]
        )
        return fig

    # Filter columns with missing values
    mv = mv[mv['missing_count'] > 0]

    # Plot bar chart with % labels
    fig = px.bar(
        mv,
        x='column',
        y='missing_pct',
        title="Missing Values (%) by Column",
        labels={'missing_pct': '% Missing', 'column': 'Column'},
        text='missing_pct'
    )
    fig.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
    fig.update_layout(yaxis_range=[0, 100])
    return fig