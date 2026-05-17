# utils/forecasting.py
import pandas as pd
import numpy as np
import plotly.graph_objects as go

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except Exception:
    PROPHET_AVAILABLE = False

try:
    from statsmodels.tsa.arima.model import ARIMA
    ARIMA_AVAILABLE = True
except Exception:
    ARIMA_AVAILABLE = False


def prepare_time_series(df, date_col, sales_col, freq="ME"):
    ts = df[[date_col, sales_col]].copy()
    ts[date_col] = pd.to_datetime(ts[date_col], errors="coerce")
    ts = ts.dropna(subset=[date_col, sales_col])
    ts = ts.set_index(date_col)
    ts = ts.resample(freq)[sales_col].sum().reset_index()
    ts.columns = ["ds", "y"]
    return ts.sort_values("ds").reset_index(drop=True)


def _build_figure(ts, future_dates, mean_fc, lower, upper, model_name):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ts["ds"], y=ts["y"], mode="markers+lines",
                             name="Actual Sales", line=dict(color="#4C72B0", width=2), marker=dict(size=6)))
    fig.add_trace(go.Scatter(x=future_dates, y=mean_fc, mode="lines+markers",
                             name=f"{model_name} Forecast",
                             line=dict(color="#DD8452", width=2, dash="dash"), marker=dict(size=6)))
    fig.add_trace(go.Scatter(
        x=list(future_dates) + list(future_dates)[::-1],
        y=list(upper) + list(lower)[::-1],
        fill="toself", fillcolor="rgba(221,132,82,0.15)",
        line=dict(color="rgba(255,255,255,0)"), name="80% Confidence Interval"))
    fig.update_layout(title=f"Sales Forecast ({model_name})", xaxis_title="Date",
                      yaxis_title="Sales ($)", template="plotly_white",
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                      hovermode="x unified")
    return fig


def forecast_prophet(ts, periods, freq):
    if not PROPHET_AVAILABLE:
        return {"error": "Prophet not available"}
    if len(ts) < 6:
        return {"error": f"Need ≥6 points, got {len(ts)}"}
    try:
        model = Prophet(yearly_seasonality=True, weekly_seasonality=False,
                        daily_seasonality=False, interval_width=0.80)
        model.fit(ts)
        future = model.make_future_dataframe(periods=periods, freq=freq)
        fc = model.predict(future)
        fc_fut = fc[fc["ds"] > ts["ds"].max()].copy()
        fig = _build_figure(ts, fc_fut["ds"].values, fc_fut["yhat"].values,
                            fc_fut["yhat_lower"].values, fc_fut["yhat_upper"].values, "Prophet")
        out = fc_fut[["ds", "yhat", "yhat_lower", "yhat_upper"]].reset_index(drop=True)
        return {"forecast": out, "figure": fig, "model": "Prophet", "periods": periods}
    except Exception as e:
        return {"error": str(e)}


def forecast_arima(ts, periods, freq):
    if not ARIMA_AVAILABLE:
        return {"error": "statsmodels not available"}
    if len(ts) < 6:
        return {"error": f"Need ≥6 points, got {len(ts)}"}
    try:
        y = ts["y"].values.astype(float)
        fitted = ARIMA(y, order=(1, 1, 1)).fit()
        fc_result = fitted.get_forecast(steps=periods)
        mean_fc = fc_result.predicted_mean
        ci = fc_result.conf_int(alpha=0.20)
        freq_offset = pd.tseries.frequencies.to_offset(freq)
        future_dates = pd.date_range(start=ts["ds"].max() + freq_offset, periods=periods, freq=freq)
        fig = _build_figure(ts, future_dates, mean_fc, ci.iloc[:, 0].values, ci.iloc[:, 1].values, "ARIMA")
        out = pd.DataFrame({"ds": future_dates, "yhat": mean_fc,
                            "yhat_lower": ci.iloc[:, 0].values, "yhat_upper": ci.iloc[:, 1].values})
        return {"forecast": out, "figure": fig, "model": "ARIMA", "periods": periods}
    except Exception as e:
        return {"error": str(e)}


def forecast_linear(ts, periods, freq):
    """Pure numpy linear trend — zero dependencies, always works."""
    try:
        y = ts["y"].values.astype(float)
        x = np.arange(len(y))
        slope, intercept = np.polyfit(x, y, 1)
        future_x = np.arange(len(y), len(y) + periods)
        mean_fc = slope * future_x + intercept
        std = np.std(y - (slope * x + intercept))
        lower = mean_fc - 1.28 * std
        upper = mean_fc + 1.28 * std
        freq_offset = pd.tseries.frequencies.to_offset(freq)
        future_dates = pd.date_range(start=ts["ds"].max() + freq_offset, periods=periods, freq=freq)
        fig = _build_figure(ts, future_dates, mean_fc, lower, upper, "Linear Trend")
        out = pd.DataFrame({"ds": future_dates, "yhat": mean_fc, "yhat_lower": lower, "yhat_upper": upper})
        return {"forecast": out, "figure": fig, "model": "Linear Trend (fallback)", "periods": periods,
                "note": "Install prophet or statsmodels for ML forecasting"}
    except Exception as e:
        return {"error": str(e)}


def run_forecast(df, date_col, sales_col, periods=6, freq="ME"):
    """Prophet → ARIMA → Linear Trend fallback chain."""
    freq_map = {"M": "ME", "Q": "QE", "A": "YE"}
    freq = freq_map.get(freq, freq)

    ts = prepare_time_series(df, date_col, sales_col, freq)
    if len(ts) < 3:
        return {"error": "Not enough time periods for forecasting (need at least 3)."}

    if PROPHET_AVAILABLE and len(ts) >= 6:
        r = forecast_prophet(ts, periods, freq)
        if "error" not in r:
            return r

    if ARIMA_AVAILABLE and len(ts) >= 6:
        r = forecast_arima(ts, periods, freq)
        if "error" not in r:
            return r

    return forecast_linear(ts, periods, freq)