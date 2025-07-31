import pandas as pd

# Load the CSV file
# Load the cleaned dishes CSV
df = pd.read_csv("../data/dishes_cleaned.csv", encoding='latin1')

# Load the wurst.txt file, each line as a dish name
with open("../data/wurst.txt", encoding='latin1') as f:
    wurst_dishes = [line.strip() for line in f if line.strip()]

# Create a DataFrame for wurst dishes
df_wurst = pd.DataFrame({'DishName': wurst_dishes})

# Union the two DataFrames
df = pd.concat([df, df_wurst], ignore_index=True)


# for sorting alphabetically
'''
# Drop rows where 'DishName' is NaN or empty/whitespace
df = df[df['DishName'].notna()]
df = df[df['DishName'].str.strip() != ""]

# Sort alphabetically
df = df.sort_values(by='DishName')

# Save back to CSV (overwrite or change filename as needed)
df.to_csv("../data/dishes_cleaned.csv", index=False)
'''