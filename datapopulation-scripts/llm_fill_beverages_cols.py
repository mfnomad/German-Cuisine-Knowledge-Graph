import pandas as pd
import requests
import json
import json5


def check_ollama_model_info(model="gemma3:12b"):
    try:
        response = requests.post(
            "http://localhost:11434/api/show",
            json={"name": model}
        )
        if response.status_code == 200:
            info = response.json()
            print("Whole JSON response from Ollama:", json.dumps(info, indent=2))
            gpu_enabled = info.get("details", {}).get("gpu", False)
            model_size = info.get("details", {}).get("size", "Unknown")
            print(f"✅ Ollama model '{model}' loaded.")
            print(f"   • GPU Enabled: {gpu_enabled}")
            print(f"   • Model Size: {model_size}")
            if not gpu_enabled:
                print("⚠️ Warning: GPU is NOT enabled for this model.")
            return gpu_enabled
        else:
            print("❌ Failed to fetch model info:", response.text)
            return False
    except Exception as e:
        print("❌ Exception during model info fetch:", e)
        return False


model_name = "gemma3:12b"  # Change if using a different model
gpu_enabled = check_ollama_model_info(model=model_name)


# Load the top 10 rows of the CSV file
df = pd.read_csv("../data/beverages_enriched.csv").head(5)

# Define the list of columns to be filled in
columns_to_fill = [
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

# Ensure all columns exist and are strings
for col in columns_to_fill:
    if col not in df.columns:
        df[col] = ""
    df[col] = df[col].astype("string")


# Function to generate a prompt from the entire row
def generate_row_prompt(row):
    beverage_name = row["BeverageName"]
    known_fields = {col: row[col] for col in columns_to_fill if pd.notna(row[col]) and row[col].strip() != ""}
    missing_fields = [col for col in columns_to_fill if col not in known_fields]

    prompt = (
        f"You are an expert in German Beverages. You will receive only the name of a beverage, "
        f"and your task is to fill in the missing fields. Respond in English and don't use special german characters such as ä, ö, ü, ß. \n DO NOT add any additional information or context or comment.\n\n"
        f"BeverageName: {beverage_name}\n"
    )
    for key, value in known_fields.items():
        prompt += f"{key}: {value}\n"

    prompt += "\nNow fill in ONLY the missing fields with realistic and concise values. "
    prompt += "Return your answer as a valid JSON object with keys ONLY from this list:\n"
    prompt += f"{missing_fields}\n\n"
    prompt += (
        "Field Restrictions:\n"
        "- Description: Short beverage description, don't mention the word 'german' - String.\n"
        "- Region: Regions in Germany where the beverage is popular - can be multiple, can even include neighboring countries, don't mention the word 'Germany' - String.\n"
        "- MainIngredient: Single Main component - String.\n"
        "- Ingredients: comma-separated list - String.\n"
        "- FlavorProfiles: String list, comma-separated from ['sweet', 'bitter', 'sour', 'fruity', 'malty', 'hoppy', 'herbal', 'citrusy', 'spiced', 'floral', 'nutty', 'chocolaty', 'caramel-like', 'yeasty', 'creamy', 'smooth', 'dry', 'refreshing', 'earthy'].\n"
        "- IsCarbonated: 'yes' or 'no' - String.\n"
        "- AlcoholContent: Alcohol by volume percentage - Float.\n"
        "- BeverageType: Type of beverage e.g. beer, wine, soda, juice, coffee - String.\n"
        "- ServingTemperature: Serving temperature, e.g., 'chilled', 'room temperature', 'hot' - String.\n"
        "- IsGermanStaple: 'yes' if culturally significant, otherwise 'no' - String.\n"
    )
    print("Prompt for LLM:", prompt)  # Debugging line to see the generated prompt
    return prompt

def clean_ollama_json(raw_output):
    """
    Clean LLM-generated JSON string and parse it safely.
    """
    try:
        # Remove markdown-style code block if present
        if raw_output.startswith("```json"):
            raw_output = raw_output.strip("`")  # remove backticks
            raw_output = raw_output.replace("json", "", 1).strip()
        elif raw_output.startswith("```"):
            raw_output = raw_output.strip("`").strip()

        # Extract JSON portion
        json_start = raw_output.find("{")
        json_str = raw_output[json_start:]

        # Fix common formatting issues
        json_str = json_str.replace('";', '",')
        json_str = json_str.replace(';', '')
        json_str = json_str.replace(',}', '}')
        json_str = json_str.replace(',]', ']')

        return json5.loads(json_str)

    except Exception as e:
        print("Failed to clean/parse JSON:", e)
        print("Raw possibly malformed JSON:", raw_output)
        return {}



# Query the local Ollama model
def query_ollama(prompt, model="gemma3:12b"):
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
df.to_csv("../data/beverages_filled_top5_gemma3_12b.csv", index=False)
