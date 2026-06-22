import requests
import pandas as pd


url = "https://api.mfapi.in/mf/119551"

response = requests.get(url)

data = response.json()

df = pd.DataFrame(data["data"])

print(df.head())

df.to_csv(
    "data/raw/live_nav_data.csv",
    index=False
)

print("NAV data saved successfully")