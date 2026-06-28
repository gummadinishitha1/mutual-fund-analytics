# Mutual Fund Analytics - Exploratory Data Analysis (EDA)

## Project Overview

This project performs Exploratory Data Analysis (EDA) on mutual fund datasets to understand NAV trends, AUM growth, SIP investments, investor behaviour, geographic distribution, fund performance, and portfolio allocation.

The analysis includes interactive visualizations using Plotly and statistical charts using Seaborn.

---

## Objectives

- Analyze daily NAV trends of mutual fund schemes from 2022–2026
- Study AUM growth across different fund houses
- Analyze SIP inflow trends and investment patterns
- Understand investor demographics and geographic distribution
- Explore fund category performance and portfolio allocation
- Identify important insights from mutual fund data

---

## Technologies Used

- Python
- Pandas
- NumPy
- Matplotlib
- Seaborn
- Plotly
- Jupyter Notebook

---

## Project Structure

Mutual_Fund_Analytics/

│
├── data/
│ ├── raw/
│ └── processed/
│
├── notebooks/
│ └── EDA_Analysis.ipynb
│
├── reports/
│ └── exported_charts/
│
├── src/
│
├── requirements.txt
│
└── README.md



---

## EDA Analysis Performed

### 1. NAV Trend Analysis
- Plotted daily NAV movement for 40 schemes (2022–2026)
- Highlighted:
  - 2023 market bull run
  - 2024 market corrections

### 2. AUM Growth Analysis
- Created grouped bar chart by fund house (2022–2025)
- Compared yearly AUM growth
- Highlighted SBI AUM dominance

### 3. SIP Inflow Analysis
- Created monthly SIP inflow trend (Jan 2022–Dec 2025)
- Marked highest SIP inflow point

### 4. Category Inflow Heatmap
- Compared monthly net inflows across fund categories
- Visualized investment trends

### 5. Investor Demographics
- Age group distribution analysis
- SIP amount comparison by age group
- Gender split analysis

### 6. Geographic Distribution
- State-wise SIP contribution analysis
- T30 vs B30 city investment comparison

### 7. Folio Growth Analysis
- Tracked folio growth from Jan 2022 to Dec 2025
- Highlighted important milestones

### 8. NAV Return Correlation
- Calculated daily return correlation
- Created correlation heatmap for selected funds

### 9. Sector Allocation Analysis
- Aggregated portfolio holdings
- Created sector allocation donut chart

---

## Key Deliverables

✔ `EDA_Analysis.ipynb`  
✔ 15+ visualization charts  
✔ Exported PNG charts for final report  
✔ Markdown documentation with 10 key findings  

---

## How to Run

Clone the repository:

```bash
git clone <repository-url>


Install dependencies:

pip install -r requirements.txt

Run Jupyter Notebook:

jupyter notebook

Open:

notebooks/EDA_Analysis.ipynb

Key Insights
Identified NAV growth trends across mutual fund schemes
Observed AUM growth patterns among fund houses
Found SIP investment trends over time
Analyzed investor behaviour by demographics and location
Compared fund performance using correlation analysis

