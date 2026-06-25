# Mutual Fund Analytics Project

## Day 2: Data Cleaning + SQLite Database

## Project Description

This project focuses on cleaning mutual fund datasets, creating a SQLite database using a star schema design, loading cleaned data, and performing analytical SQL queries.

---

## Tasks Completed

### 1. Data Cleaning

### nav_history.csv
- Converted date column into datetime format
- Sorted data by amfi_code and date
- Filled missing NAV values for holidays/weekends
- Removed duplicate records
- Validated NAV values greater than 0


### investor_transactions.csv
- Standardized transaction types:

  - SIP
  - Lumpsum
  - Redemption

- Validated amount values
- Fixed date formats
- Checked KYC status values


### scheme_performance.csv
- Converted return columns into numeric format
- Identified incorrect values
- Checked expense ratio range:



---

## Database Design

Created SQLite database:



Designed Star Schema with:

### Dimension Tables

- dim_fund
- dim_date


### Fact Tables

- fact_nav
- fact_transactions
- fact_performance
- fact_aum


Primary keys and foreign keys were created for relationships between tables.

---

## Data Loading

Loaded cleaned CSV files into SQLite using:

- SQLAlchemy
- pandas to_sql()


Verified:

- Table creation
- Data loading
- Row counts

---

## SQL Analysis Queries

Created 10 SQL queries:

1. Top 5 funds by AUM
2. Average NAV per month
3. SIP year-over-year growth
4. Transactions by state
5. Funds with expense ratio less than 1%
6. Highest return funds
7. Category-wise performance
8. Monthly transaction trends
9. NAV growth analysis
10. Investor transaction summary

---

## Data Dictionary

Created:


Contains:

- Column names
- Data types
- Column descriptions
- Source information

---

## Project Files

mutual_fund_analytics/

│
├── data/
│ └── processed/
│ └── cleaned CSV files
│
├── sql/
│ ├── schema.sql
│ └── queries.sql
│
├── bluestock_mf.db
│
├── data_dictionary.md
│
└── README.md


---

## Technologies Used

- Python
- Pandas
- SQLite
- SQLAlchemy
- SQL
- Jupyter Notebook

---

## Git Commit


---

## Deliverables Completed

✅ 10 cleaned CSV files  
✅ bluestock_mf.db  
✅ schema.sql  
✅ queries.sql  
✅ data_dictionary.md  
✅ README.md  

---

## Status

Day 2 Mutual Fund Analytics tasks completed successfully.

