# utils/cleaning.py
import pandas as pd
import numpy as np
import re


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Enhanced cleaning for v2.0:
    - strip whitespace from column names
    - drop fully empty columns/rows
    - simple numeric coercion for likely numeric cols
    - drop exact duplicate rows
    - normalize string fields
    """
    df = df.copy()
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
                df[col] = df[col].astype(str).str.replace(",", "").str.replace(" ", "")
                df[col] = pd.to_numeric(df[col], errors='coerce')

    # Drop duplicate rows — track count for reporting
    before = len(df)
    df = df.drop_duplicates()
    after = len(df)
    df.attrs["duplicates_removed"] = before - after

    return df


def data_quality_score(df: pd.DataFrame) -> dict:
    """
    Compute a comprehensive Data Quality Score (0-100).
    Returns dict with overall score, component scores, and details.
    """
    if df is None or df.empty:
        return {"overall": 0, "components": {}, "grade": "F"}

    total_cells = df.shape[0] * df.shape[1]
    missing_cells = int(df.isna().sum().sum())
    completeness = max(0, 1 - missing_cells / total_cells) if total_cells > 0 else 0

    # Uniqueness: duplicate rows as fraction of total
    dup_count = int(df.duplicated().sum())
    uniqueness = max(0, 1 - dup_count / len(df)) if len(df) > 0 else 0

    # Consistency: numeric columns with plausible ranges (no extreme negatives on sales-like cols)
    numeric_cols = df.select_dtypes(include='number').columns
    consistency = 1.0
    if len(numeric_cols) > 0:
        bad = 0
        for col in numeric_cols:
            q1 = df[col].quantile(0.01)
            q99 = df[col].quantile(0.99)
            iqr = q99 - q1
            outliers = ((df[col] < q1 - 3 * iqr) | (df[col] > q99 + 3 * iqr)).sum()
            bad += outliers
        total_numeric_cells = len(df) * len(numeric_cols)
        consistency = max(0, 1 - bad / total_numeric_cells) if total_numeric_cells > 0 else 1.0

    # Validity: % of object columns where top value != 'nan'
    obj_cols = df.select_dtypes(include='object').columns
    validity = 1.0
    if len(obj_cols) > 0:
        nan_like = sum(1 for c in obj_cols if df[c].astype(str).str.lower().eq('nan').sum() > len(df) * 0.1)
        validity = max(0, 1 - nan_like / len(obj_cols))

    # Weighted overall
    weights = {"completeness": 0.4, "uniqueness": 0.2, "consistency": 0.2, "validity": 0.2}
    overall = (
        completeness * weights["completeness"] +
        uniqueness * weights["uniqueness"] +
        consistency * weights["consistency"] +
        validity * weights["validity"]
    ) * 100

    overall = round(overall, 1)

    grade = "A" if overall >= 90 else "B" if overall >= 75 else "C" if overall >= 60 else "D" if overall >= 50 else "F"

    return {
        "overall": overall,
        "grade": grade,
        "components": {
            "Completeness": round(completeness * 100, 1),
            "Uniqueness": round(uniqueness * 100, 1),
            "Consistency": round(consistency * 100, 1),
            "Validity": round(validity * 100, 1)
        },
        "details": {
            "missing_cells": missing_cells,
            "total_cells": total_cells,
            "duplicate_rows": dup_count,
        }
    }


def explain_column_detection(df: pd.DataFrame):
    """
    Attempt to detect sales/profit/category/date/geo columns and give
    a confidence score and a short reason.
    Returns a dict:
      { "Sales Column": (col_name or None, score (0-1), reason str), ... }
    """
    mapping = {}

    def detect(keywords, prefer_contains=True):
        for kw in keywords:
            for c in df.columns:
                cn = str(c).lower()
                if prefer_contains and kw in cn:
                    reason = f"Matched keyword '{kw}' inside column name '{c}'."
                    return c, 0.95, reason
                if not prefer_contains and cn.startswith(kw):
                    reason = f"Column name '{c}' starts with '{kw}'."
                    return c, 0.9, reason
        return None, 0.0, ""

    sales_candidates = ["sales", "revenue", "amount", "total", "price", "orderamount"]
    profit_candidates = ["profit", "margin", "gain"]
    category_candidates = ["category", "product", "segment", "type", "item"]
    date_candidates = ["date", "time", "orderdate", "timestamp"]
    geo_candidates = ["country", "region", "state", "city", "location", "territory"]

    sales_col, sales_score, sales_reason = detect(sales_candidates)
    profit_col, profit_score, profit_reason = detect(profit_candidates)
    category_col, category_score, category_reason = detect(category_candidates)
    date_col, date_score, date_reason = detect(date_candidates)
    geo_col, geo_score, geo_reason = detect(geo_candidates)

    # Fallback: numeric column with highest sum for sales
    if not sales_col:
        numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        if numeric_cols:
            sums = {c: df[c].abs().sum(skipna=True) for c in numeric_cols}
            if sums:
                best = max(sums, key=sums.get)
                if sums[best] > 0:
                    sales_col = best
                    sales_score = 0.6
                    sales_reason = "No obvious 'sales' name; selected numeric column with highest total."

    # Fallback: date-like object column
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
    mapping["Geo Column"] = (geo_col, geo_score, geo_reason)
    return mapping
