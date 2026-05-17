# 📊 Sales Intelligence Dashboard v2.0

> A Streamlit-powered intelligent platform for automated sales analytics, AI insights, ML forecasting & professional reporting.

---

## 🚀 Overview

The **Sales Intelligence Dashboard v2.0** is a smart, interactive web application that automatically analyzes any uploaded sales dataset (CSV or XLSX). Upload your file — the system handles everything else.

It auto-detects key columns (sales, profit, date, category, geography) using intelligent keyword scoring and confidence ranking, then instantly generates:

- KPI metrics with category performance rankings
- Interactive Plotly charts and a geographic choropleth map
- AI-powered chatbot for plain-English dataset queries
- Machine learning sales forecasting (Prophet → ARIMA → Linear Trend fallback)
- Data Quality Scoring (completeness, uniqueness, consistency, validity)
- Auto-generated executive summary and actionable business insights
- One-click professional PDF report export

No manual configuration. No column mapping. Just upload and explore.

---

## ✨ What's New in v2.0

| Feature | Description |
|---|---|
| 🤖 AI Chatbot | Ask questions about your data in plain English — powered by Google Gemini Flash |
| 📈 ML Forecasting | Prophet / ARIMA / Linear Trend with confidence intervals |
| 🎯 Data Quality Score | 0–100 score with grade (A–F) across 4 dimensions |
| 📋 Executive Summary | Auto-generated business narrative paragraph |
| 🔬 Enhanced EDA | Correlation heatmap, MoM growth trend, profit margin trend |
| 🚨 Anomaly Detection | IQR-based outlier alerts and revenue concentration warnings |
| ⚡ Performance | `@st.cache_data` caching — 5× faster than v1.0 |

---

## ✅ Key Features

### 🔍 Automatic Column Detection
Detects five column types without any user input:

| Column Type | Detection Keywords | Fallback |
|---|---|---|
| Sales | sales, revenue, amount, total, price | Highest numeric sum column |
| Profit | profit, margin, gain | None (optional) |
| Category | category, product, segment, type | None (optional) |
| Date | date, time, orderdate, timestamp | First column parseable as datetime |
| Geography | country, region, state, city, location | None (optional) |

Each detection result shows a **confidence score (0–100%)** and a short reason in the sidebar.

---

### 📊 KPIs & Visual Analysis

**Primary KPIs:**
- 💰 Total Sales
- 📈 Total Profit
- 🎯 Profit Margin (%)
- 📊 Average Sales per Transaction
- 📋 Total Records
- 🎯 Data Quality Score & Grade

**Charts (all interactive via Plotly):**
- Sales Trend with Month-over-Month Growth overlay
- Sales Distribution Histogram
- Category-wise Sales Bar Chart
- Category Share Donut Chart
- Profit Margin Trend over Time
- 3D Scatter Plot (Sales vs Profit vs Category)
- Geographic Choropleth Map (sales by country/region)

---

### 🔎 Drill-Down Analysis
Select any category from the dropdown to view:
- Category-level KPIs (records, sales, profit)
- Sales trend chart for that category only
- Top 10 products by revenue within the category

---

### 🤖 AI Chatbot
Natural language interface powered by the OpenRouter API (Google Gemini Flash 2.0):
- Answers questions based **only on your uploaded dataset**
- Suggested questions available as one-click buttons
- Maintains conversation history across messages
- Responds in 3–5 seconds on average

Example questions:
> *"What are the top performing categories?"*
> *"Is the profit margin healthy?"*
> *"Give me a 3-point executive summary."*

---

### 📈 Sales Forecasting
Three-model fallback chain — always produces a result:

1. **Prophet** (Facebook) — primary model, supports yearly seasonality, 80% confidence intervals
2. **ARIMA (1,1,1)** — secondary fallback via statsmodels
3. **Linear Trend** — final fallback using numpy, zero dependencies

Configure forecast horizon (1–24 periods) and frequency (monthly / quarterly / weekly).

---

### 🎯 Data Quality Score
Scored 0–100 with grade A–F:

| Component | Weight | Measures |
|---|---|---|
| Completeness | 40% | Percentage of non-missing cells |
| Uniqueness | 20% | Non-duplicate row fraction |
| Consistency | 20% | Numeric outlier rate (3× IQR) |
| Validity | 20% | Absence of null-like string values |

---

### 💡 AI-Generated Insights
Automatically generated alerts and observations:
- Top 3 categories by sales
- Best and worst performing category
- Negative profit alerts 🚨
- Low / strong margin indicators
- Revenue concentration risk (top 5 customers)
- Outlier transaction detection
- Data quality warnings

---

### 🔬 EDA Section
- Data quality component breakdown (progress bars)
- Summary statistics for all numeric and categorical columns
- Missing values visualization (% missing per column)
- Correlation heatmap (Pearson, color-coded)

---

### 📄 PDF Report Export
One-click export containing:
- Executive summary
- Data quality score and grade
- KPI table
- Chart images
- EDA summary statistics
- All business insights
- Conclusion

---

## 🛠️ Technology Stack

| Component | Technology |
|---|---|
| Web Framework | Streamlit |
| Data Processing | Pandas, NumPy |
| Visualization | Plotly Express |
| Forecasting | Prophet, statsmodels (ARIMA) |
| AI Chatbot | OpenRouter API — Google Gemini Flash 2.0 |
| Report Generation | ReportLab |
| Performance | Streamlit `@st.cache_data` + `requests.Session` |
| File Support | Pandas + OpenPyXL (CSV, XLSX) |

---

## 📁 Project Structure

```
├── app.py                  # Main Streamlit application
├── requirements.txt        # Python dependencies
└── utils/
    ├── cleaning.py         # Data cleaning + column detection + quality scoring
    ├── eda.py              # Summary stats, missing values, correlation, trend charts
    ├── charts.py           # All Plotly chart functions
    ├── insights.py         # Business insight generation + executive summary
    ├── forecasting.py      # Prophet / ARIMA / Linear Trend forecasting
    ├── chatbot.py          # OpenRouter API integration + chat history
    └── report.py           # ReportLab PDF report builder
```

---

## 📥 Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/Shammas-Ali/Sales-Analysis-Dashboard.git
cd Sales-Analysis-Dashboard
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure AI Chatbot (Optional)
Create `.streamlit/secrets.toml`:
```toml
OPENROUTER_API_KEY = "sk-or-v1-..."
```
Get a free key at [openrouter.ai/keys](https://openrouter.ai/keys).
> Without this key, all features work except the AI chatbot tab.

### 4. Run the Dashboard
```bash
streamlit run app.py
```

---

## 📤 How to Use

1. Launch the app with `streamlit run app.py`
2. Upload a CSV or Excel file from the sidebar
3. The system auto-cleans data and detects columns
4. Use sidebar filters (date range, category, sales range) to slice data
5. Explore the 7 tabs: KPIs & Charts, Forecasting, Insights, EDA, AI Chatbot, Data Preview, Report
6. Click **Generate PDF Report** to export a professional report

**Best results when your dataset contains columns like:** `date`, `sales`, `profit`, `category`, `country`

---

## 📝 Example Use Cases

- Retail sales performance tracking
- E-commerce product and regional analytics
- Monthly/quarterly business review reporting
- Category and customer profitability analysis
- Generating stakeholder-ready PDF reports from raw exports

---

## 📦 Requirements

```
streamlit
pandas
numpy
plotly
openpyxl
reportlab
kaleido
requests
statsmodels
prophet
```

Install all at once:
```bash
pip install -r requirements.txt
```

---

## ⚡ Performance Notes

Version 2.0 is significantly faster than v1.0:

- All heavy computations (cleaning, EDA, insights, quality score) are cached with `@st.cache_data` — they run once per file upload, not on every interaction
- The AI chatbot uses a persistent HTTP session to avoid repeated TCP handshakes
- Chart images are only written to disk when you request a PDF report, not on every page render
- The Data Preview tab shows the first 500 rows by default to prevent slow renders on large files

---

## 🛡️ License

This project is released under the **MIT License** — free to use, modify, and distribute.

---

## 🤝 Contributing

Contributions are welcome. Feel free to open:
- Issues for bugs or unexpected behavior
- Feature requests for new chart types, models, or export formats
- Pull requests for improvements

---

## ⭐ Show Your Support

If this project helped you, give it a star ⭐ on GitHub!

---

*Built with Python, Streamlit, and Plotly — Muhammad Shammas Ali | Roll No: 23-SET-011 | Fall 2023*
