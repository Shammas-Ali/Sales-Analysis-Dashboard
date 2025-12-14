# utils/cleaning.py
import pandas as pd
import numpy as np
import re

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Basic cleaning:
    - strip whitespace from column names
    - drop fully empty columns
    - simple numeric coercion for likely numeric cols
    - drop exact duplicate rows
    """
    df = df.copy()
    # normalize column names temporarily (but app will re-standardize)
    df.columns = [str(c).strip() for c in df.columns]

    # Drop columns that are completely empty
    df.dropna(axis=1, how='all', inplace=True)

    # Remove rows that are all NaN
    df.dropna(axis=0, how='all', inplace=True)

    # Trim string fields
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].astype(str).str.strip()

    # Try convert numeric-looking columns to numeric
    for col in df.columns:
        if df[col].dtype == object:
            sample = df[col].dropna().astype(str).head(50)
            numeric_like = sample.apply(lambda s: bool(re.match(r'^[\d\-\+\.,\s]+$', s)))
            if len(sample) > 0 and numeric_like.sum() >= len(sample) * 0.6:
                # remove thousand separators and try convert
                df[col] = df[col].astype(str).str.replace(",", "").str.replace(" ", "")
                df[col] = pd.to_numeric(df[col], errors='coerce')

    # Drop duplicate rows
    df = df.drop_duplicates()

    return df

def explain_column_detection(df: pd.DataFrame):
    """
    Attempt to detect sales/profit/category/date columns and give
    a confidence score and a short reason.
    Returns a dict:
      { "Sales Column": (col_name or None, score (0-1), reason str), ... }
    """
    cols = [c.lower() for c in df.columns]
    mapping = {}

    def detect(keywords, prefer_contains=True):
        # keywords list in priority order
        for kw in keywords:
            for c in df.columns:
                cn = str(c).lower()
                if prefer_contains and kw in cn:
                    reason = f"Matched keyword '{kw}' inside column name '{c}'."
                    return c, 0.95, reason
                if not prefer_contains and cn.startswith(kw):
                    reason = f"Column name '{c}' starts with '{kw}'."
                    return c, 0.9, reason
        # fallback: check dtype or values
        return None, 0.0, ""

    sales_candidates = ["sales", "revenue", "amount", "total", "price", "orderamount"]
    profit_candidates = ["profit", "margin", "gain"]
    category_candidates = ["category", "product", "segment", "type", "item"]
    date_candidates = ["date", "time", "orderdate", "timestamp"]

    sales_col, sales_score, sales_reason = detect(sales_candidates)
    profit_col, profit_score, profit_reason = detect(profit_candidates)
    category_col, category_score, category_reason = detect(category_candidates)
    date_col, date_score, date_reason = detect(date_candidates)

    # If sales not found, try numeric columns with large values
    if not sales_col:
        numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        if numeric_cols:
            # pick the numeric column with highest sum
            sums = {c: df[c].abs().sum(skipna=True) for c in numeric_cols}
            if sums:
                best = max(sums, key=sums.get)
                if sums[best] > 0:
                    sales_col = best
                    sales_score = 0.6
                    sales_reason = "No obvious 'sales' name; selected numeric column with highest total."
    # If date not found, check for object columns that look like dates
    if not date_col:
        for c in df.columns:
            try:
                parsed = pd.to_datetime(df[c], errors='coerce')
                if parsed.notna().sum() >= max(5, len(parsed) * 0.4):
                    date_col = c
                    date_score = 0.7
                    date_reason = f"Column '{c}' parsed mostly as datetimes."
                    break
            except Exception:
                continue

    mapping["Sales Column"] = (sales_col, sales_score, sales_reason)
    mapping["Profit Column"] = (profit_col, profit_score, profit_reason)
    mapping["Category Column"] = (category_col, category_score, category_reason)
    mapping["Date Column"] = (date_col, date_score, date_reason)
    return mapping