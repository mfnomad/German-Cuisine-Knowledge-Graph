import pandas as pd

# Load the original beverages CSV (with 'BeverageName' column)
file_path = "../data/beverages.csv"
df = pd.read_csv(file_path)

# Define new columns to represent beverage properties in the knowledge graph
new_columns = [
    "Description",                  # Short description of the beverage
    "Region",                       # Regions in Germany where it's popular
    "MainIngredient",              # Main component (e.g., barley, grapes, apple)
    "Ingredients",                 # Comma-separated full ingredient list
    "FlavorProfiles",             # e.g., fruity, bitter, sweet, herbal
    "IsCarbonated",                # 'yes' or 'no'
    "AlcoholContent",              # Percentage value or 'non-alcoholic'
    "BeverageType",                # e.g., beer, wine, soda, juice
    "ServingTemperature",          # e.g., chilled, room temperature, hot
    "IsGermanStaple",              # 'yes' if culturally significant
]

# Add new columns to the dataframe with empty/default values
for col in new_columns:
    df[col] = ""

# Save the enriched CSV to a new file
output_path = "../data/beverages_enriched.csv"
df.to_csv(output_path, index=False)
print(f"✅ Enriched CSV saved to: {output_path}")
