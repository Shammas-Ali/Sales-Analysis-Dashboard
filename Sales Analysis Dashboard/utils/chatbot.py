# utils/chatbot.py
import pandas as pd
import os
import requests

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

# ⚡ Use a fast, cheap model instead of "openrouter/auto" (which is slow due to routing overhead)
# Options ranked by speed: gemini-flash > gpt-4o-mini > claude-haiku
OPENROUTER_MODEL = "google/gemini-2.0-flash-001"

# Reuse HTTP session for connection pooling (avoids TCP handshake on every request)
_session = requests.Session()


def _get_api_key() -> str:
    try:
        import streamlit as st
        key = st.secrets.get("OPENROUTER_API_KEY", "")
        if key:
            return key
    except Exception:
        pass
    return os.environ.get("OPENROUTER_API_KEY", "")


def build_dataset_context(df: pd.DataFrame, sales_col: str, profit_col: str,
                           category_col: str, date_col: str) -> str:
    """Build a concise dataset summary string for the chatbot system prompt."""
    lines = []
    lines.append(f"Dataset shape: {df.shape[0]} rows x {df.shape[1]} columns")
    lines.append(f"Columns: {', '.join(df.columns.tolist())}")

    if date_col and date_col in df.columns:
        # Column is already datetime after app.py processing
        dmin = df[date_col].min()
        dmax = df[date_col].max()
        if pd.notna(dmin) and pd.notna(dmax):
            lines.append(f"Date range: {dmin.strftime('%b %Y')} to {dmax.strftime('%b %Y')}")

    total_sales = 0
    if sales_col and sales_col in df.columns:
        total_sales = df[sales_col].sum()
        lines.append(f"Total sales: ${total_sales:,.2f}")
        lines.append(f"Average sales per record: ${df[sales_col].mean():,.2f}")
        lines.append(f"Max single-record sales: ${df[sales_col].max():,.2f}")

    if profit_col and profit_col in df.columns:
        total_profit = df[profit_col].sum()
        lines.append(f"Total profit: ${total_profit:,.2f}")
        if total_sales > 0:
            lines.append(f"Profit margin: {(total_profit / total_sales * 100):.2f}%")

    if category_col and category_col in df.columns:
        lines.append(f"Number of categories: {df[category_col].nunique()}")
        if sales_col and sales_col in df.columns:
            top_cats = df.groupby(category_col)[sales_col].sum().sort_values(ascending=False).head(5)
            lines.append("Top 5 categories by sales: " +
                         "; ".join([f"{k}: ${v:,.0f}" for k, v in top_cats.items()]))

    missing = int(df.isna().sum().sum())
    lines.append(f"Missing values: {missing} cells")

    for col in df.select_dtypes(include="object").columns[:4]:
        top_vals = df[col].value_counts().head(3).index.tolist()
        lines.append(f"Sample values in '{col}': {', '.join(str(v) for v in top_vals)}")

    return "\n".join(lines)


def query_chatbot(user_message: str, dataset_context: str, chat_history: list) -> str:
    api_key = _get_api_key()

    if not api_key:
        return (
            "**OpenRouter API key not configured.**\n\n"
            "Add this to `.streamlit/secrets.toml`:\n"
            "```toml\n"
            'OPENROUTER_API_KEY = "sk-or-v1-..."\n'
            "```\n"
            "Get your free key at: https://openrouter.ai/keys"
        )

    system_prompt = (
        "You are a Sales Intelligence Assistant embedded in a sales analytics dashboard. "
        "Help users understand their uploaded sales dataset.\n\n"
        f"Dataset summary:\n---\n{dataset_context}\n---\n\n"
        "Rules: Answer ONLY from the data above. Be concise and business-focused. "
        "Use bullet points and $ for currency. Give actionable recommendations."
    )

    messages = [{"role": "system", "content": system_prompt}]
    # Limit history to last 6 turns (3 exchanges) to reduce token count and latency
    for h in chat_history[-6:]:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": user_message})

    try:
        response = _session.post(
            OPENROUTER_BASE_URL,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "http://localhost:8501",
                "X-Title": "Sales Intelligence Dashboard",
            },
            json={
                "model": OPENROUTER_MODEL,
                "messages": messages,
                "max_tokens": 500,       # Reduced from 800 — enough for concise answers
                "temperature": 0.2,      # Slightly lower = faster, more deterministic
            },
            timeout=20,                  # Reduced from 30s
        )
        data = response.json()

        if "choices" in data and data["choices"]:
            return data["choices"][0]["message"]["content"]

        if "error" in data:
            err  = data["error"]
            code = str(err.get("code", ""))
            msg  = err.get("message", "Unknown error")
            if code == "401" or "auth" in msg.lower() or "key" in msg.lower():
                return "Invalid or expired OpenRouter API key. Check https://openrouter.ai/keys and update secrets.toml."
            if code == "429":
                return "Rate limit reached. Please wait a moment and try again."
            if code == "402":
                return "OpenRouter credit limit reached. Add credits at https://openrouter.ai/credits"
            return f"OpenRouter error ({code}): {msg}"

        return "Could not generate a response. Please try again."

    except requests.exceptions.Timeout:
        return "Request timed out (20s). Try a shorter question or check your connection."
    except requests.exceptions.ConnectionError:
        return "Cannot reach OpenRouter. Check your internet connection."
    except Exception as e:
        return f"Unexpected error: {str(e)}"