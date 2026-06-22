import pandas as pd
import os

folder = "data/raw"

for file in os.listdir(folder):

    if file.endswith(".csv"):

        df = pd.read_csv(folder + "/" + file)

        print("\nFILE:", file)

        print("Shape:", df.shape)

        print("\nData Types:")
        print(df.dtypes)

        print("\nFirst 5 rows:")
        print(df.head())