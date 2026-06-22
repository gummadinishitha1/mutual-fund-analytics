import pandas as pd


fund_master = pd.read_csv("data/raw/01_fund_master.csv")

nav_history = pd.read_csv("data/raw/02_nav_history.csv")


fund_codes = set(fund_master["amfi_code"])

nav_codes = set(nav_history["amfi_code"])


missing_codes = fund_codes - nav_codes


print("Total fund codes:", len(fund_codes))

print("Total nav codes:", len(nav_codes))


if len(missing_codes) == 0:
    print("All AMFI codes are valid")
else:
    print("Missing AMFI codes:")
    print(missing_codes)