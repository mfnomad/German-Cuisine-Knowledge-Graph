import pandas as pd

# Load the CSV file
df = pd.read_csv("../data/beverages.csv")

# Load the beertypes CSV file
df_beer = pd.read_csv("../data/beertypes.csv")

# Merge the two DataFrames on 'BeverageName'
merged_df = pd.merge(df, df_beer, on="BeverageName", how="outer")

# Save the merged DataFrame to a new CSV file
merged_df.to_csv("beverages_beertypes_merged.csv", index=False)