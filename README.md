# Sales-Dashboard-Project
A Streamlit-powered intelligent dashboard for automated sales analytics, insights & reporting

🚀 Overview

The Sales Analysis Platform is a smart, interactive web dashboard that automatically analyzes any uploaded sales dataset (CSV/XLSX).
It detects important columns such as sales, profit, date, and category, and generates:

KPI metrics

Detailed charts

Geo-maps

EDA

Missing value insights

Actionable business insights

PDF report export

No manual configuration needed — the system auto-detects columns based on intelligent scoring.

✨ Key Features
🔍 Automatic Column Detection

The platform intelligently identifies:
✔ Sales column
✔ Profit column
✔ Category column
✔ Date column

With confidence scoring & explanations.

📈 Interactive KPIs

💰 Total Sales

📈 Total Profit

🛒 Average Sales

🗑️ Missing Value Count

📊 Visualizations (Plotly)

Sales Over Time

Sales Distribution Histogram

Category-wise Sales Bar

Donut Chart for Category Share

3D Scatter Plot (Sales, Profit, Category)

Geo-map for location-based sales

🔎 Drill-Down Analysis

Select any category → view detailed product-level performance.

💡 AI-Generated Insights

The system highlights:

Growth trends

Risk zones

Drops

High-performing categories

🔬 EDA Section

Summary statistics

Missing values visualization

Data overview

📄 Report Generation

Export a PDF report containing all KPIs for sharing or record-keeping.

🛠️ Technology Stack
Component	Technology
Web Framework	Streamlit
Visualization	Plotly, Seaborn, Matplotlib
Data Handling	Pandas, Openpyxl
Reporting	ReportLab
Cleaning, EDA, Charts	Custom-built utility modules
📁 Project Structure
├── app.py
├── requirements.txt
└── utils/
    ├── cleaning.py
    ├── eda.py
    ├── charts.py
    ├── report.py
    ├── insights.py

📥 Installation & Setup
1️⃣ Clone the Repository
git clone https://github.com/YourUsername/YourRepoName.git
cd YourRepoName

2️⃣ Install Dependencies
pip install -r requirements.txt

3️⃣ Run the Dashboard
streamlit run app.py

📤 How to Use

Launch the app

Upload a CSV or Excel file

Dashboard will auto-clean the data

View KPIs, charts, insights & EDA

Export report (PDF) if needed

Best results when your dataset contains columns like:
date, sales, profit, category, country, etc.

📝 Example Use Cases

Retail sales performance tracking

E-commerce analytics

Regional performance comparison

Product category insights

Generating business reports for stakeholders

📦 Requirements

From requirements.txt:

streamlit
pandas
plotly
seaborn
matplotlib
openpyxl
reportlab

🛡️ License

This project is released under the MIT License.

🤝 Contributing

Feel free to open:

Issues

Feature requests

Pull requests

⭐ Show Your Support

If you found this project helpful, give it a star ⭐ on GitHub!
