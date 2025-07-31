import pandas as pd
import requests
import json
import json5

# Load the top 5 rows of the CSV file
df = pd.read_csv("../data/dishes_extracols.csv").head(5)

# Define the list of columns to be filled in
columns_to_fill = [
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

# Ensure all columns exist and are strings
for col in columns_to_fill:
    if col not in df.columns:
        df[col] = ""
    df[col] = df[col].astype("string")


# Function to generate a prompt from the entire row
def generate_row_prompt(row):
    dish_name = row["DishName"]
    known_fields = {col: row[col] for col in columns_to_fill if pd.notna(row[col]) and row[col].strip() != ""}
    missing_fields = [col for col in columns_to_fill if col not in known_fields]

    prompt = (
        f"You are an expert in German cuisine. You will receive partial information about a dish, "
        f"and your task is to fill in the missing fields. Respond in English and Only fill in fields that are missing (leave existing ones unchanged).\n\n"
        f"DishName: {dish_name}\n"
    )
    for key, value in known_fields.items():
        prompt += f"{key}: {value}\n"

    prompt += "\nNow fill in ONLY the missing fields with realistic and concise values. "
    prompt += "Return your answer as a valid JSON object with keys ONLY from this list:\n"
    prompt += f"{missing_fields}\n\n"
    prompt += (
        "Field Restrictions:\n"
        "- Description: Short dish description - String.\n"
        "- Region: Region in Germany - String.\n"
        "- MainIngredient: Main component - String.\n"
        "- Ingredients: comma-separated list - String.\n"
        "- StateOfMainIngredient: e.g. raw, boiled, sliced - String.\n"
        "- DietType: comma-separated from ['vegetarian', 'vegan', 'omnivore', 'halal', 'kosher'].\n"
        "- MealEatenAtPartOfDay: comma-separated from ['breakfast', 'lunch', 'dinner', 'snackDuringDay'].\n"
        "- Variations: comma-separated list - String.\n"
        "- FlavorProfiles: comma-separated from ['sweet', 'sour', 'bitter', 'spicy', 'savory', 'umami', 'aromatic'].\n"
        "- PreparationMethod: Short preparation method - String.\n"
        "- PreparationTimeMinutes: Estimated preparation time - Integer.\n"
        "- MeatCut: Cut of meat if applicable - String or empty."
    )
    print("Prompt for LLM:", prompt)  # Debugging line to see the generated prompt
    return prompt

def clean_ollama_json(raw_output):
    """
    Fix common LLM JSON formatting issues before parsing.
    """
    try:
        # Extract JSON portion
        json_start = raw_output.find("{")
        json_str = raw_output[json_start:]

        # Fix common formatting issues
        # Replace semicolon line endings with commas (only outside of strings)
        json_str = json_str.replace('";', '",')  # closing quote + semicolon
        json_str = json_str.replace(';', '')     # remove any remaining stray semicolons
        json_str = json_str.replace(',}', '}')   # remove trailing commas
        json_str = json_str.replace(',]', ']')   # just in case

        # Fix booleans or numeric fields quoted (optional, json5 handles this)
        return json5.loads(json_str)

    except Exception as e:
        print("Failed to clean/parse JSON:", e)
        print("Raw possibly malformed JSON:", raw_output)
        return {}


# Query the local Ollama model
def query_ollama(prompt, model="llama3.2:1b"):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": False
        }
    )
    if response.status_code == 200:
        raw_output = response.json()["response"].strip()
        print("Ollama response:", raw_output)
        return clean_ollama_json(raw_output)
    else:
        print("Ollama request failed:", response.text)
        return {}




# Fill the missing fields using LLM
for idx, row in df.iterrows():
    prompt = generate_row_prompt(row)
    filled_values = query_ollama(prompt)

    for field, value in filled_values.items():
        df.at[idx, field] = str(value).strip()

# Show the filled dataframe
print(df)

# Save to file
df.to_csv("../data/dishes_filled_top5.csv", index=False)
