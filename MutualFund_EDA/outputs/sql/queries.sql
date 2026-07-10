-- 1. Top 5 funds by AUM
SELECT
    amfi_code,
    scheme_name,
    fund_house,
    category,
    aum_crore
FROM fact_performance
ORDER BY aum_crore DESC
LIMIT 5;


-- 2. Average NAV per month
SELECT
    strftime('%Y-%m', date) AS month,
    ROUND(AVG(nav), 2) AS avg_nav
FROM fact_nav
GROUP BY month
ORDER BY month;


-- 3. SIP YoY growth by month
SELECT
    month,
    sip_inflow_crore,
    active_sip_accounts_crore,
    yoy_growth_pct
FROM fact_monthly_sip_inflows
ORDER BY month;


-- 4. Transactions by state
SELECT
    state,
    COUNT(*) AS transaction_count,
    SUM(amount_inr) AS total_amount_inr
FROM fact_transactions
GROUP BY state
ORDER BY transaction_count DESC;


-- 5. Funds with expense ratio below 1%
SELECT
    amfi_code,
    scheme_name,
    fund_house,
    category,
    expense_ratio_pct
FROM fact_performance
WHERE expense_ratio_pct < 1
ORDER BY expense_ratio_pct ASC;


-- 6. Top 10 funds by 5-year return
SELECT
    amfi_code,
    scheme_name,
    fund_house,
    return_5yr_pct,
    aum_crore
FROM fact_performance
ORDER BY return_5yr_pct DESC
LIMIT 10;


-- 7. Best risk-adjusted funds by Sharpe ratio
SELECT
    amfi_code,
    scheme_name,
    fund_house,
    sharpe_ratio,
    return_3yr_pct,
    std_dev_ann_pct
FROM fact_performance
ORDER BY sharpe_ratio DESC
LIMIT 10;


-- 8. Net transaction flow by fund
SELECT
    t.amfi_code,
    f.scheme_name,
    SUM(
        CASE
            WHEN t.transaction_type = 'Redemption' THEN -t.amount_inr
            ELSE t.amount_inr
        END
    ) AS net_flow_inr
FROM fact_transactions AS t
LEFT JOIN dim_fund AS f
    ON t.amfi_code = f.amfi_code
GROUP BY t.amfi_code, f.scheme_name
ORDER BY net_flow_inr DESC
LIMIT 10;


-- 9. Monthly transaction trend
SELECT
    strftime('%Y-%m', transaction_date) AS month,
    transaction_type,
    COUNT(*) AS transaction_count,
    SUM(amount_inr) AS total_amount_inr
FROM fact_transactions
GROUP BY month, transaction_type
ORDER BY month, transaction_type;


-- 10. Top portfolio sectors by total market value
SELECT
    sector,
    ROUND(SUM(market_value_cr), 2) AS total_market_value_cr,
    ROUND(AVG(weight_pct), 2) AS avg_weight_pct,
    COUNT(DISTINCT stock_symbol) AS stock_count
FROM fact_portfolio_holdings
GROUP BY sector
ORDER BY total_market_value_cr DESC;
