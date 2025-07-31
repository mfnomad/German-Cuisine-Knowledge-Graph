import pandas as pd

# Load the original dishes CSV (assumed to have only 'DishName' column)
file_path = "../data/dishes.csv"
df = pd.read_csv(file_path)

# Define the new columns based on the ontology mapping
new_columns = [
    "Description",
    "Region",
    "MainIngredient",
    "Ingredients",
    "StateOfMainIngredient",
    "DietType",
    "MealEatenAtPartOfDay",
    "Variations",
    "FlavorProfiles",
    "PreparationMethod",
    "PreparationTimeMinutes",
    "MeatCut"
]

# Add new columns with empty/default values
for col in new_columns:
    df[col] = ""

# Save the enriched CSV to a new file
output_path = "../data/dishes_enriched.csv"
df.to_csv(output_path, index=False)
