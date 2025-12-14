# utils/charts.py
import plotly.express as px
import pandas as pd


def sales_over_time(df, date_col, sales_col):
    fig = px.line(df, x=date_col, y=sales_col, title="Sales Over Time")
    return fig


def sales_distribution_histogram(df, sales_col):
    fig = px.histogram(df, x=sales_col, nbins=30, title="Sales Distribution")
    return fig


def category_sales_bar(df, category_col, sales_col):
    df_cat = df.groupby(category_col)[sales_col].sum().reset_index()
    fig = px.bar(df_cat, x=category_col, y=sales_col, title="Sales by Category")
    return fig


def sales_pie_donut_chart(df, category_col, sales_col):
    df_cat = df.groupby(category_col)[sales_col].sum().reset_index()
    fig = px.pie(df_cat, names=category_col, values=sales_col, hole=0.4, title="Sales Share by Category")
    return fig


def sales_3d_scatter(df, sales_col, profit_col, category_col):
    fig = px.scatter_3d(df, x=sales_col, y=profit_col, z=category_col, color=category_col,
                        size=sales_col, title="3D Sales vs Profit vs Category")
    return fig


def sales_geo_map(df: pd.DataFrame, geo_col: str, sales_col: str):
    """
    Modern Geo Map: Choropleth showing sales per country/region.
    """
    if geo_col not in df.columns or sales_col not in df.columns:
        return None

    # Aggregate sales by geo
    df_geo = df.groupby(geo_col)[sales_col].sum().reset_index()

    # Try to plot
    try:
        fig = px.choropleth(
            df_geo,
            locations=geo_col,
            locationmode='country names',  # use 'ISO-3' if country codes
            color=sales_col,
            hover_name=geo_col,
            hover_data={sales_col: ':,.0f'},
            color_continuous_scale=px.colors.sequential.Plasma,
            title="Sales by Region/Country"
        )
        fig.update_layout(
            geo=dict(showframe=False, showcoastlines=True, projection_type='equirectangular'),
            template="plotly_white"
        )
        return fig
    except Exception:
        return None
