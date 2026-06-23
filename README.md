# Mutual Fund Analytics Project 📊

## Overview

This project focuses on building a Mutual Fund Analytics pipeline using Python.

It includes:
- Data ingestion
- Data quality checking
- Live NAV extraction using API
- AMFI code validation

---

## Technologies Used

- Python
- Pandas
- NumPy
- Matplotlib
- Seaborn
- Plotly
- Requests
- SciPy
- SQLAlchemy
- Jupyter Notebook

---

## Project Structure




---

## Features Completed

✅ Created project folder structure

✅ Installed required libraries

✅ Loaded 10 CSV datasets using Pandas

Checked:

- shape
- datatypes
- first rows

✅ Performed data quality checks

Checked:

- missing values
- duplicates
- anomalies

✅ Fetched live NAV data from MF API

API:

https://api.mfapi.in/mf/

✅ Fetched NAV for:

- SBI Bluechip
- ICICI Bluechip
- Nippon Large Cap
- Axis Bluechip
- Kotak Bluechip

✅ AMFI code validation completed

Result:

All AMFI codes are valid

---

## Running the Project

Install dependencies:

```bash
pip install -r requirements.txt

Run data ingestion:

```bash
python src/data_ingestion.py


paste this:

```markdown
Run NAV fetch:

```bash
python src/live_nav_fetch.py

Run AMFI validation:

```bash
python src/amfi_validation.py

---

## Data Quality Checks

The project checks:

- Missing values
- Duplicate records
- Data types
- Invalid AMFI codes

Report generated:

reports/data_quality_summary.txt

---

## GitHub Commit

Day 1 completion:

Day 1: Data ingestion complete

---

## Future Improvements

- Data cleaning pipeline
- SQL database integration
- Dashboard creation
- Mutual fund performance analysis

---

## Author

Gummadi Nishitha

Mutual Fund Analytics Project