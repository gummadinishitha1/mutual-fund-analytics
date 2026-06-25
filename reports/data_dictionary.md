# Data Dictionary

This document describes the SQLite tables loaded into `bluestock_mf.db` from the cleaned CSV files in `data/processed`. Source references point to both the cleaned dataset used for ingestion and the raw dataset it was derived from.

## Table Sources

| SQLite table | Cleaned source | Raw source | Grain |
| --- | --- | --- | --- |
| `dim_fund` | `data/processed/fund_master_cleaned.csv` | `data/raw/01_fund_master.csv` | One row per mutual fund scheme |
| `fact_nav` | `data/processed/nav_history_cleaned.csv` | `data/raw/02_nav_history.csv` | One row per fund per NAV date |
| `fact_aum_by_fund_house` | `data/processed/aum_by_fund_house_cleaned.csv` | `data/raw/03_aum_by_fund_house.csv` | One row per fund house per date |
| `fact_monthly_sip_inflows` | `data/processed/monthly_sip_inflows_cleaned.csv` | `data/raw/04_monthly_sip_inflows.csv` | One row per month |
| `fact_category_inflows` | `data/processed/category_inflows_cleaned.csv` | `data/raw/05_category_inflows.csv` | One row per category per month |
| `fact_industry_folio_count` | `data/processed/industry_folio_count_cleaned.csv` | `data/raw/06_industry_folio_count.csv` | One row per month |
| `fact_performance` | `data/processed/scheme_performance_cleaned.csv` | `data/raw/07_scheme_performance.csv` | One row per mutual fund scheme |
| `fact_transactions` | `data/processed/investor_transactions_cleaned.csv` | `data/raw/08_investor_transactions.csv` | One row per investor transaction |
| `fact_portfolio_holdings` | `data/processed/portfolio_holdings_cleaned.csv` | `data/raw/09_portfolio_holdings.csv` | One row per fund holding per portfolio date |
| `fact_benchmark_indices` | `data/processed/benchmark_indices_cleaned.csv` | `data/raw/10_benchmark_indices.csv` | One row per benchmark index per date |

## `dim_fund`

Business purpose: master dimension for identifying mutual fund schemes and their descriptive attributes.

| Column | SQLite type | Business definition | Source reference |
| --- | --- | --- | --- |
| `amfi_code` | `BIGINT` | AMFI scheme code used as the fund identifier across datasets. | `fund_master_cleaned.csv` |
| `fund_house` | `TEXT` | Asset management company or fund house that manages the scheme. | `fund_master_cleaned.csv` |
| `scheme_name` | `TEXT` | Official mutual fund scheme name. | `fund_master_cleaned.csv` |
| `category` | `TEXT` | Broad fund category, such as equity, debt, hybrid, or other. | `fund_master_cleaned.csv` |
| `sub_category` | `TEXT` | More specific classification within the broad category. | `fund_master_cleaned.csv` |
| `plan` | `TEXT` | Scheme plan option, such as growth or dividend. | `fund_master_cleaned.csv` |
| `launch_date` | `TEXT` | Date on which the scheme was launched. | `fund_master_cleaned.csv` |
| `benchmark` | `TEXT` | Benchmark index used to compare scheme performance. | `fund_master_cleaned.csv` |
| `expense_ratio_pct` | `FLOAT` | Annual fund expense ratio as a percentage of assets. | `fund_master_cleaned.csv` |
| `exit_load_pct` | `FLOAT` | Exit load percentage charged on applicable redemptions. | `fund_master_cleaned.csv` |
| `min_sip_amount` | `BIGINT` | Minimum allowed SIP investment amount in INR. | `fund_master_cleaned.csv` |
| `min_lumpsum_amount` | `BIGINT` | Minimum allowed one-time investment amount in INR. | `fund_master_cleaned.csv` |
| `fund_manager` | `TEXT` | Name of the scheme's fund manager. | `fund_master_cleaned.csv` |
| `risk_category` | `TEXT` | Risk classification assigned to the scheme. | `fund_master_cleaned.csv` |
| `sebi_category_code` | `TEXT` | SEBI category code or classification identifier. | `fund_master_cleaned.csv` |

## `fact_nav`

Business purpose: historical NAV time series for fund-level trend and return analysis.

| Column | SQLite type | Business definition | Source reference |
| --- | --- | --- | --- |
| `amfi_code` | `BIGINT` | AMFI scheme code for the fund whose NAV is recorded. | `nav_history_cleaned.csv` |
| `date` | `TEXT` | Date of the NAV observation. | `nav_history_cleaned.csv` |
| `nav` | `FLOAT` | Net asset value of the scheme on the observation date. | `nav_history_cleaned.csv` |
| `nav_was_forward_filled` | `INTEGER` | Boolean flag indicating the NAV was forward-filled for a non-trading day such as a weekend or holiday. | `nav_history_cleaned.csv` |

## `fact_aum_by_fund_house`

Business purpose: tracks assets under management and scheme count at the fund-house level.

| Column | SQLite type | Business definition | Source reference |
| --- | --- | --- | --- |
| `date` | `TEXT` | Reporting date for fund-house AUM. | `aum_by_fund_house_cleaned.csv` |
| `fund_house` | `TEXT` | Asset management company or fund house. | `aum_by_fund_house_cleaned.csv` |
| `aum_lakh_crore` | `FLOAT` | Assets under management expressed in lakh crore INR. | `aum_by_fund_house_cleaned.csv` |
| `aum_crore` | `BIGINT` | Assets under management expressed in crore INR. | `aum_by_fund_house_cleaned.csv` |
| `num_schemes` | `BIGINT` | Number of schemes managed by the fund house. | `aum_by_fund_house_cleaned.csv` |

## `fact_monthly_sip_inflows`

Business purpose: industry-level monthly SIP inflow and SIP account activity metrics.

| Column | SQLite type | Business definition | Source reference |
| --- | --- | --- | --- |
| `month` | `TEXT` | Reporting month in `YYYY-MM` format. | `monthly_sip_inflows_cleaned.csv` |
| `sip_inflow_crore` | `BIGINT` | Monthly SIP inflow amount in crore INR. | `monthly_sip_inflows_cleaned.csv` |
| `active_sip_accounts_crore` | `FLOAT` | Number of active SIP accounts in crore. | `monthly_sip_inflows_cleaned.csv` |
| `new_sip_accounts_lakh` | `FLOAT` | Number of new SIP accounts opened in lakh. | `monthly_sip_inflows_cleaned.csv` |
| `sip_aum_lakh_crore` | `FLOAT` | Total SIP-linked AUM in lakh crore INR. | `monthly_sip_inflows_cleaned.csv` |
| `yoy_growth_pct` | `FLOAT` | Year-over-year SIP inflow growth percentage. | `monthly_sip_inflows_cleaned.csv` |

## `fact_category_inflows`

Business purpose: monthly net flows by fund category for category-level trend analysis.

| Column | SQLite type | Business definition | Source reference |
| --- | --- | --- | --- |
| `month` | `TEXT` | Reporting month in `YYYY-MM` format. | `category_inflows_cleaned.csv` |
| `category` | `TEXT` | Mutual fund category receiving inflows or outflows. | `category_inflows_cleaned.csv` |
| `net_inflow_crore` | `FLOAT` | Net investment flow for the month in crore INR; negative values represent outflows. | `category_inflows_cleaned.csv` |

## `fact_industry_folio_count`

Business purpose: industry folio counts by major fund category over time.

| Column | SQLite type | Business definition | Source reference |
| --- | --- | --- | --- |
| `month` | `TEXT` | Reporting month in `YYYY-MM` format. | `industry_folio_count_cleaned.csv` |
| `total_folios_crore` | `FLOAT` | Total mutual fund folios in crore. | `industry_folio_count_cleaned.csv` |
| `equity_folios_crore` | `FLOAT` | Equity fund folios in crore. | `industry_folio_count_cleaned.csv` |
| `debt_folios_crore` | `FLOAT` | Debt fund folios in crore. | `industry_folio_count_cleaned.csv` |
| `hybrid_folios_crore` | `FLOAT` | Hybrid fund folios in crore. | `industry_folio_count_cleaned.csv` |
| `others_folios_crore` | `FLOAT` | Folios in other fund categories in crore. | `industry_folio_count_cleaned.csv` |

## `fact_performance`

Business purpose: fund-level performance, risk, rating, AUM, and cost metrics.

| Column | SQLite type | Business definition | Source reference |
| --- | --- | --- | --- |
| `amfi_code` | `BIGINT` | AMFI scheme code used as the fund identifier. | `scheme_performance_cleaned.csv` |
| `scheme_name` | `TEXT` | Official mutual fund scheme name. | `scheme_performance_cleaned.csv` |
| `fund_house` | `TEXT` | Asset management company or fund house. | `scheme_performance_cleaned.csv` |
| `category` | `TEXT` | Broad mutual fund category. | `scheme_performance_cleaned.csv` |
| `plan` | `TEXT` | Scheme plan option. | `scheme_performance_cleaned.csv` |
| `return_1yr_pct` | `FLOAT` | One-year scheme return percentage. | `scheme_performance_cleaned.csv` |
| `return_3yr_pct` | `FLOAT` | Three-year scheme return percentage. | `scheme_performance_cleaned.csv` |
| `return_5yr_pct` | `FLOAT` | Five-year scheme return percentage. | `scheme_performance_cleaned.csv` |
| `benchmark_3yr_pct` | `FLOAT` | Three-year benchmark return percentage for comparison. | `scheme_performance_cleaned.csv` |
| `alpha` | `FLOAT` | Excess return measure relative to expected benchmark-adjusted return. | `scheme_performance_cleaned.csv` |
| `beta` | `FLOAT` | Sensitivity of fund returns to benchmark movements. | `scheme_performance_cleaned.csv` |
| `sharpe_ratio` | `FLOAT` | Risk-adjusted return metric using total volatility. | `scheme_performance_cleaned.csv` |
| `sortino_ratio` | `FLOAT` | Risk-adjusted return metric using downside volatility. | `scheme_performance_cleaned.csv` |
| `std_dev_ann_pct` | `FLOAT` | Annualized standard deviation of returns as a percentage. | `scheme_performance_cleaned.csv` |
| `max_drawdown_pct` | `FLOAT` | Maximum observed decline from peak to trough as a percentage. | `scheme_performance_cleaned.csv` |
| `aum_crore` | `BIGINT` | Fund-level assets under management in crore INR. | `scheme_performance_cleaned.csv` |
| `expense_ratio_pct` | `FLOAT` | Annual fund expense ratio as a percentage of assets. | `scheme_performance_cleaned.csv` |
| `morningstar_rating` | `BIGINT` | Fund rating score, typically on a numeric star scale. | `scheme_performance_cleaned.csv` |
| `risk_grade` | `TEXT` | Qualitative risk grade for the scheme. | `scheme_performance_cleaned.csv` |
| `has_non_numeric_return` | `INTEGER` | Boolean validation flag indicating at least one return field could not be parsed as numeric. | `scheme_performance_cleaned.csv` |
| `expense_ratio_out_of_range` | `INTEGER` | Boolean validation flag indicating the expense ratio is outside the expected 0.1% to 2.5% range. | `scheme_performance_cleaned.csv` |
| `performance_anomaly_flag` | `INTEGER` | Boolean rollup flag for any performance validation anomaly. | `scheme_performance_cleaned.csv` |
| `performance_anomaly_reason` | `TEXT` | Semicolon-separated anomaly reasons for flagged performance records. | `scheme_performance_cleaned.csv` |

## `fact_transactions`

Business purpose: investor transaction activity for flow, channel, location, and investor-segment analysis.

| Column | SQLite type | Business definition | Source reference |
| --- | --- | --- | --- |
| `investor_id` | `TEXT` | Anonymized investor identifier. | `investor_transactions_cleaned.csv` |
| `transaction_date` | `TEXT` | Date on which the transaction occurred. | `investor_transactions_cleaned.csv` |
| `amfi_code` | `BIGINT` | AMFI scheme code for the transacted fund. | `investor_transactions_cleaned.csv` |
| `transaction_type` | `TEXT` | Type of transaction, such as SIP, Lumpsum, or Redemption. | `investor_transactions_cleaned.csv` |
| `amount_inr` | `BIGINT` | Transaction amount in INR. | `investor_transactions_cleaned.csv` |
| `state` | `TEXT` | Investor state associated with the transaction. | `investor_transactions_cleaned.csv` |
| `city` | `TEXT` | Investor city associated with the transaction. | `investor_transactions_cleaned.csv` |
| `city_tier` | `TEXT` | Market classification of the city, such as T30 or B30. | `investor_transactions_cleaned.csv` |
| `age_group` | `TEXT` | Investor age-band segment. | `investor_transactions_cleaned.csv` |
| `gender` | `TEXT` | Investor gender segment. | `investor_transactions_cleaned.csv` |
| `annual_income_lakh` | `FLOAT` | Investor annual income in lakh INR. | `investor_transactions_cleaned.csv` |
| `payment_mode` | `TEXT` | Payment channel or mode used for the transaction. | `investor_transactions_cleaned.csv` |
| `kyc_status` | `TEXT` | Investor KYC verification status. | `investor_transactions_cleaned.csv` |

## `fact_portfolio_holdings`

Business purpose: security-level holdings for each fund portfolio snapshot.

| Column | SQLite type | Business definition | Source reference |
| --- | --- | --- | --- |
| `amfi_code` | `BIGINT` | AMFI scheme code for the fund holding the security. | `portfolio_holdings_cleaned.csv` |
| `stock_symbol` | `TEXT` | Exchange ticker or short symbol for the held security. | `portfolio_holdings_cleaned.csv` |
| `stock_name` | `TEXT` | Company or security name. | `portfolio_holdings_cleaned.csv` |
| `sector` | `TEXT` | Sector classification of the held security. | `portfolio_holdings_cleaned.csv` |
| `weight_pct` | `FLOAT` | Portfolio weight of the security as a percentage. | `portfolio_holdings_cleaned.csv` |
| `market_value_cr` | `FLOAT` | Market value of the holding in crore INR. | `portfolio_holdings_cleaned.csv` |
| `current_price_inr` | `FLOAT` | Current price of the security in INR. | `portfolio_holdings_cleaned.csv` |
| `portfolio_date` | `TEXT` | Date of the portfolio holdings snapshot. | `portfolio_holdings_cleaned.csv` |

## `fact_benchmark_indices`

Business purpose: benchmark index time series for comparing market movement and fund performance.

| Column | SQLite type | Business definition | Source reference |
| --- | --- | --- | --- |
| `date` | `TEXT` | Date of the benchmark observation. | `benchmark_indices_cleaned.csv` |
| `index_name` | `TEXT` | Name of the benchmark index. | `benchmark_indices_cleaned.csv` |
| `close_value` | `FLOAT` | Closing value of the benchmark index on the observation date. | `benchmark_indices_cleaned.csv` |
