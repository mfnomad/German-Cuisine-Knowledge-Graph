import pandas as pd
import ollama
import json
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, OWL, XSD
import ast


def normalize_german_chars(text: str) -> str:
    """Replace German special characters with neutral forms."""
    return (
        text.replace("ä", "ae")
        .replace("Ä", "Ae")
        .replace("ö", "oe")
        .replace("Ö", "Oe")
        .replace("ü", "ue")
        .replace("Ü", "Ue")
        .replace("ß", "ss")
        .replace("\n", " ")
    )

def clean_llm_response(content: str) -> dict | None:
    """
    Cleans and parses LLM output into JSON.
    Returns a dict if successful, else None.
    """
    content = content.strip()

    # Remove code fences if model adds them
    if content.startswith("```"):
        content = content.strip("`")
        if content.lower().startswith("json"):
            content = content[4:].strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        print("Parsing error:", e, "\nRaw content:", content)
        return None


def build_prompt_drink(name: str, description: str) -> str:
    """
    Builds the ontology enrichment prompt for drinks only.
    """
    return f"""
    You are an ontology enrichment assistant in the domain of german drinks.
    You will classify the following beverage and assign attributes 
    according to the ontology provided.

    Ontology Classes:
    - Beverage
    - Alcoholic: Beer, Brandy, Cocktail, Digestif, FermentedAlcoholic, Liquor, Malt_beverage, Spirit, Spritzer, Wine
    - NonAlcoholic: Coffee, Hot_Chocolate, Icetea, Juice, NonAlcoholicBeer, Soda, Tea, Water

    Object Properties: HasBeverageType, HasFlavorProfile, HasMainIngredient, HasIngredient, HasRegion, HasServingTemperature

    Data Properties: HasAlcoholContent, HasDescription, 
    IsCarbonated, IsGermanStaple

Input:
Name: "{name}"
Description: "{description}"

Output English Values in JSON with the following keys:
{{
  "class": "...", Choose one from Alcoholic, NonAlcoholic
  "subclass": "...", -- Choose one subclass from above if Alchoholic: Beer, Brandy, Cocktail, Digestif, FermentedAlcoholic, Liquor, Malt_beverage, Spirit, Spritzer, Wine and if NonAlcoholic: Coffee, Hot_Chocolate, Icetea, Juice, NonAlcoholicBeer, Soda, Tea, Water
  "HasMainIngredient": "...", -- ONE WORD e.g. Apple, Barley, Grape, Hop, Wheat etc.
  "HasIngredient": [], -- comma seperated list of ingredients e.g. Apple, Barley, Grape, Hop, Wheat etc.
  "HasRegion": "...", -- e.g. Bavaria, Baden-Wuerttemberg etc.
  "HasServingTemperature": "...", -- only Options: Chilled, Frozen, Hot, RoomTemperature
  "HasFlavorProfile": "...", -- comma seperated flavor adjectives e.g. Bitter, Sweet, Fruity, Herbal 
  "HasAlcoholContent": "...", -- float value in percent or 0.0 for non-alcoholic
  "IsCarbonated": "...", -- true or false
  "IsGermanStaple": "...", -- true or false
}}

Make sure to only use the keys above. If a key is not applicable, set its value to null or an empty list.
Only output pure JSON. Do not include code fences, markdown, or explanations.
    """



def enrich_drinks(csv_path: str, output_path: str, limit: int | None = None):
    """
    Enrich drinks dataset with ontology attributes.
    """
    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    if limit:
        df = df.head(limit)

    enriched_rows = []
    
    df["Description"] = df["Description"].apply(normalize_german_chars)
    for _, row in df.iterrows():
        name = row["Name"]
        description = row["Description"][:160]  # limit description length

        prompt = build_prompt_drink(name, description)
        response = ollama.chat(model="gemma3:4b", messages=[{"role": "user", "content": prompt}])

        attributes = clean_llm_response(response["message"]["content"])
        if not attributes:
            continue

        enriched_rows.append({
            "name": name,
            "description": row["Description"][:40],   # REMOVE SLICING LATTER
            "category": "Beverage",
            **attributes
        })

    enriched_df = pd.DataFrame(enriched_rows)
    enriched_df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"✅ Enriched drinks saved to {output_path}")


def sanitize_uri_value(value: str) -> str:
    """Make sure the string is a safe URI fragment (remove spaces, commas)."""
    return value.strip().replace(" ", "_").replace(",", "_")

def update_onto_drinks(input_csv: str, input_ontology: str, output_ontology: str):
    """
    Update ontology with enriched drinks from CSV.
    """
    # Load ontology
    g = Graph()
    g.parse(input_ontology, format="xml")

    # Define namespace
    GC = Namespace("http://example.org/german-cuisine#")
    g.bind("gc", GC)

    # Load CSV
    df = pd.read_csv(input_csv, encoding="utf-8-sig")

    for _, row in df.iterrows():
        # --- Instance name ---
        name = sanitize_uri_value(row["name"])
        inst = GC[name]

        # --- Types ---
        g.add((inst, RDF.type, OWL.Thing))
        g.add((inst, RDF.type, OWL.NamedIndividual))
        if pd.notna(row["category"]):
            g.add((inst, RDF.type, GC[sanitize_uri_value(row["category"])]))
        if pd.notna(row["class"]):
            g.add((inst, RDF.type, GC[sanitize_uri_value(row["class"])]))
        if pd.notna(row["subclass"]) and row["subclass"]:
            g.add((inst, RDF.type, GC[sanitize_uri_value(row["subclass"])]))

        # --- Data properties ---
        if pd.notna(row["description"]):
            g.add((inst, GC.hasDescription, Literal(row["description"], datatype=XSD.string)))

        if pd.notna(row["HasAlcoholContent"]):
            try:
                alc = float(row["HasAlcoholContent"])
                g.add((inst, GC.hasAlcoholContent, Literal(alc, datatype=XSD.decimal)))
            except ValueError:
                pass

        if pd.notna(row["IsCarbonated"]):
            g.add((inst, GC.isCarbonated, Literal(str(row["IsCarbonated"]).lower() == "true", datatype=XSD.boolean)))

        if pd.notna(row["IsGermanStaple"]):
            g.add((inst, GC.isGermanStaple, Literal(str(row["IsGermanStaple"]).lower() == "true", datatype=XSD.boolean)))

        # --- Object properties ---
        if pd.notna(row["HasMainIngredient"]):
            g.add((inst, GC.hasMainIngredient, GC[sanitize_uri_value(row["HasMainIngredient"])]))

        if pd.notna(row["HasIngredient"]):
            try:
                ingredients = ast.literal_eval(row["HasIngredient"]) if isinstance(row["HasIngredient"], str) else []
                for ing in ingredients:
                    g.add((inst, GC.hasIngredient, GC[sanitize_uri_value(ing)]))
            except Exception:
                pass

        if pd.notna(row["HasRegion"]):
            # handle multiple values separated by comma
            regions = [sanitize_uri_value(r) for r in str(row["HasRegion"]).split(",")]
            print("Sanitzied regions:", regions)
            for reg in regions:
                try:
                    g.add((inst, GC.hasRegion, GC[reg]))
                except Exception:
                    print("Error adding region:", reg)
                

        if pd.notna(row["HasServingTemperature"]):
            g.add((inst, GC.hasServingTemperature, GC[sanitize_uri_value(row["HasServingTemperature"])]))

        if pd.notna(row["HasFlavorProfile"]):
            flavors = [sanitize_uri_value(f) for f in str(row["HasFlavorProfile"]).split(",")]
            for fl in flavors:
                g.add((inst, GC.hasFlavorProfile, GC[fl]))

    # Save new ontology
    g.serialize(destination=output_ontology, format="xml")
    print(f"✅ Ontology updated and saved to {output_ontology}")


def update_onto_drinks(input_csv: str, input_ontology: str, output_ontology: str):
    """
    Update ontology with enriched drinks from CSV.
    """
    # Load ontology
    g = Graph()
    g.parse(input_ontology, format="xml")

    # Define namespace
    GC = Namespace("http://example.org/german-cuisine#")
    g.bind("gc", GC)

    # Load CSV
    df = pd.read_csv(input_csv, encoding="utf-8-sig")

    for _, row in df.iterrows():
        name = row["name"].strip().replace(" ", "_")
        inst = GC[name]

        # --- Types ---
        g.add((inst, RDF.type, OWL.Thing))
        g.add((inst, RDF.type, OWL.NamedIndividual))
        g.add((inst, RDF.type, GC[row["category"]]))
        g.add((inst, RDF.type, GC[row["class"]]))
        if pd.notna(row["subclass"]) and row["subclass"]:
            g.add((inst, RDF.type, GC[row["subclass"]]))

        # --- Data properties ---
        if pd.notna(row["description"]):
            g.add((inst, GC.hasDescription, Literal(row["description"], datatype=XSD.string)))

        if pd.notna(row["HasAlcoholContent"]):
            try:
                alc = float(row["HasAlcoholContent"])
                g.add((inst, GC.hasAlcoholContent, Literal(alc, datatype=XSD.decimal)))
            except ValueError:
                pass

        if pd.notna(row["IsCarbonated"]):
            g.add((inst, GC.isCarbonated, Literal(str(row["IsCarbonated"]).lower() == "true", datatype=XSD.boolean)))

        if pd.notna(row["IsGermanStaple"]):
            g.add((inst, GC.isGermanStaple, Literal(str(row["IsGermanStaple"]).lower() == "true", datatype=XSD.boolean)))

        # --- Object properties ---
        if pd.notna(row["HasMainIngredient"]):
            g.add((inst, GC.hasMainIngredient, GC[row["HasMainIngredient"].strip()]))

        if pd.notna(row["HasIngredient"]):
            try:
                # Parse list string
                ingredients = eval(row["HasIngredient"]) if isinstance(row["HasIngredient"], str) else []
                for ing in ingredients:
                    g.add((inst, GC.hasIngredient, GC[ing.strip()]))
            except Exception:
                pass

        if pd.notna(row["HasRegion"]):
            regions = [r.strip() for r in str(row["HasRegion"]).split(",")]
            for reg in regions:
            # normalize for URI safety
                safe_reg = reg.replace(" ", "_")
                print("Adding region:", safe_reg)
                g.add((inst, GC.hasRegion, GC[safe_reg]))


        if pd.notna(row["HasServingTemperature"]):
            g.add((inst, GC.hasServingTemperature, GC[row["HasServingTemperature"].strip()]))

        if pd.notna(row["HasFlavorProfile"]):
            flavors = [f.strip() for f in row["HasFlavorProfile"].split(",")]
            for fl in flavors:
                g.add((inst, GC.hasFlavorProfile, GC[fl]))

    # Save new ontology
    g.serialize(destination=output_ontology, format="xml")
    print(f"✅ Ontology updated and saved to {output_ontology}")



if __name__ == "__main__":
    enrich_drinks(csv_path="drinks_new_unique.csv", output_path="enriched_beverages.csv", limit=4)
    update_onto_drinks(input_csv="enriched_beverages.csv", input_ontology="v9-ontology.rdf", output_ontology="v10-ontology.rdf")
