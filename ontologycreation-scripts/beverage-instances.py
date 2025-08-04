from owlready2 import *
import pandas as pd
from pathlib import Path

print("Loading ontology...")
ttl_path = Path("../ontology-owl/ontology.ttl").resolve()
onto = get_ontology(str(ttl_path)).load(format="turtle")
print("Ontology loaded.")

def clean_value(val):
    if pd.isna(val):
        print("Value is NaN, returning empty string.")
        return ""
    print("Cleaned value about to return: ", str(val).strip().strip('"'))
    return str(val).strip().strip('"')

print("Defining classes and properties...")
with onto:
    class Beverage(Thing): pass
    class BeverageType(Thing): pass
    class Region(Thing): pass
    class MainIngredient(Thing): pass
    class Ingredient(Thing): pass
    class FlavorProfile(Thing): pass
    class ServingTemperature(Thing): pass
    
    class hasBeverageType(Beverage >> BeverageType): pass
    class hasRegion(Beverage >> Region): pass
    class hasMainIngredient(Beverage >> MainIngredient): pass
    class hasIngredient(Beverage >> Ingredient): pass
    class hasFlavorProfile(Beverage >> FlavorProfile): pass
    class hasServingTemperature(Beverage >> ServingTemperature): pass

    class hasDescription(Beverage >> str, DataProperty): pass
    class isCarbonated(Beverage >> bool, DataProperty): pass
    class hasAlcoholContent(Beverage >> float, DataProperty): pass
    class isGermanStaple(Beverage >> bool, DataProperty): pass
print("Classes and properties defined.")

# Load CSV
csv_path = "../data/augmented_data/cleaned_beverages_augmented_gemma3_12b.csv"
print(f"Loading CSV from: {csv_path}")
df = pd.read_csv(csv_path)
print(f"CSV loaded with {len(df)} rows.")

# Fix encoding issue
print("Replacing 'WÃ¼rttemberg' with 'Wuerttemberg' in DataFrame...")
df.replace("WÃ¼rttemberg", "Wuerttemberg", inplace=True)
print("Replacement done.")

def get_or_create(cls, name):
    name = name.strip().replace(" ", "_")
    print("Returning name as cls: ", name)
    print("CLS: ", cls)
    return cls(name)


print("Beginning beverage instance creation...\n")
for idx, row in df.iterrows():
    print(f"\n--- Row {idx+1}/{len(df)} ---")
    bev_name = clean_value(row["BeverageName"]).replace(" ", "_")
    bev = Beverage(bev_name)
    print(f"Processing beverage: {bev_name}")

    bev.hasDescription = [clean_value(row["Description"])]
    print("Description set: ", bev.hasDescription[0])
    bev.isCarbonated = [clean_value(row["IsCarbonated"]).strip().lower() == "yes"]
    print("isCarbonated set: ", bev.isCarbonated[0])
    bev.isGermanStaple = [clean_value(row["IsGermanStaple"]).strip().lower() == "yes"]
    print("isGermanStaple set: ", bev.isGermanStaple[0])
    
    try:
        bev.hasAlcoholContent = [float(clean_value(row["AlcoholContent"]))]
        print("hasAlcoholContent set: ", bev.hasAlcoholContent[0])
    except ValueError:
        print(f"⚠️ Could not convert AlcoholContent for {bev_name}, setting to 0.0")
        bev.hasAlcoholContent = [0.0]
    
    print("  Setting object properties...")

    region_str = clean_value(row["Region"])
    bev.hasRegion = []
    for region in region_str.split(","):
        region = region.strip()
        print("Processing region:", repr(region))
        if region:
            print(f"Adding region: {repr(region)}")
            bev.hasRegion.append(get_or_create(Region, region))
        print("loop finished for region: ", region)
    print("hasRegion set : ", [r.name for r in bev.hasRegion])


    bev.hasMainIngredient = [get_or_create(Ingredient, clean_value(row["MainIngredient"]))]
    print("hasMainIngredient set: ", bev.hasMainIngredient[0].name)
    bev.hasBeverageType = [get_or_create(BeverageType, clean_value(row["BeverageType"]))]
    bev.hasServingTemperature = [get_or_create(ServingTemperature, clean_value(row["ServingTemperature"]))]

    print("  Setting ingredients...")
    for ing in str(clean_value(row["Ingredient"])).split(","):
        ing = ing.strip()
        if ing:
            bev.hasIngredient.append(get_or_create(Ingredient, ing))

    print("  Setting flavor profiles...")
    for flavor in str(clean_value(row["FlavorProfile"])).split(","):
        flavor = flavor.strip()
        if flavor:
            bev.hasFlavorProfile.append(get_or_create(FlavorProfile, flavor))

    print(f"✅ Added beverage: {bev_name}")

# Save ontology
owl_output_path = "../ontology-owl/german_beverages.rdf"
print(f"\nSaving ontology to: {owl_output_path} ...")
onto.save(file=owl_output_path, format="rdfxml")
print("Ontology saved.")
