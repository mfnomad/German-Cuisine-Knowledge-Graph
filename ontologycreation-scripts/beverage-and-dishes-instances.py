from owlready2 import *
import pandas as pd
pd.set_option('display.max_colwidth', None)

from pathlib import Path

print("Loading ontology...")
ttl_path = Path("../ontology-owl/ontology.ttl").resolve()
onto = get_ontology(str(ttl_path)).load(format="turtle")
print("Ontology loaded.")

def clean_value(val):
    if pd.isna(val):
        print("!!!! Value is NaN, returning empty string. !!!!")
        print("Val considered NAN: ", val)
        return ""
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

    class Dish(Thing): pass
    class DietType(Thing): pass
    class MealEatenAtPartOfDay(Thing): pass
    class MeatCut(Thing): pass
    class PreparationMethod(Thing): pass
    class StateOfMainIngredient(Thing): pass
    class Variation(Thing): pass

    class hasBeverageType(Beverage >> BeverageType): pass
    class hasRegion(Thing >> Region): pass
    class hasMainIngredient(Thing >> MainIngredient): pass
    class hasIngredient(Thing >> Ingredient): pass
    class hasFlavorProfile(Thing >> FlavorProfile): pass
    class hasServingTemperature(Thing >> ServingTemperature): pass

    class hasDietType(Dish >> DietType): pass
    class hasMealEatenAtPartOfDay(Dish >> MealEatenAtPartOfDay): pass
    class hasMeatCut(Dish >> MeatCut): pass
    class hasPreparationMethod(Dish >> PreparationMethod): pass
    class hasStateOfMainIngredient(Dish >> StateOfMainIngredient): pass
    class hasVariation(Dish >> Variation): pass

    class hasDescription(Thing >> str, DataProperty): pass
    class isCarbonated(Beverage >> bool, DataProperty): pass
    class hasAlcoholContent(Beverage >> float, DataProperty): pass
    class hasPreparationTimeMinutes(Dish >> float, DataProperty): pass
    class isGermanStaple(Thing >> bool, DataProperty): pass

print("Classes and properties defined.")

# Load Beverages CSV
csv_bev = "../data/augmented_data/cleaned_beverages_augmented_gemma3_12b.csv"
df_bev = pd.read_csv(csv_bev)
df_bev.replace("WÃ¼rttemberg", "Wuerttemberg", inplace=True)

# Load Dishes CSV
csv_dish = "../data/augmented_data/cleaned_dishes_augmented_gemma3_12b.csv"
df_dish = pd.read_csv(csv_dish, quotechar='"', delimiter=',', skipinitialspace=True)
df_dish["MeatCut"] = df_dish["MeatCut"].fillna("")

df_dish.replace("WÃ¼rttemberg", "Wuerttemberg", inplace=True)

def get_or_create(cls, name):
    name = name.strip().replace(" ", "_")
    return cls(name)

print("\nProcessing beverages...")
for idx, row in df_bev.iterrows():
    bev_name = clean_value(row["BeverageName"]).replace(" ", "_")
    bev = Beverage(bev_name)
    bev.hasDescription = [clean_value(row["Description"])]
    bev.isCarbonated = [clean_value(row["IsCarbonated"]).lower() == "yes"]
    bev.isGermanStaple = [clean_value(row["IsGermanStaple"]).lower() == "yes"]
    try:
        bev.hasAlcoholContent = [float(clean_value(row["AlcoholContent"]))]
    except:
        bev.hasAlcoholContent = [0.0]

    bev.hasRegion = [get_or_create(Region, r.strip()) for r in clean_value(row["Region"]).split(",") if r.strip()]
    bev.hasMainIngredient = [get_or_create(Ingredient, clean_value(row["MainIngredient"]))]
    bev.hasBeverageType = [get_or_create(BeverageType, clean_value(row["BeverageType"]))]
    bev.hasServingTemperature = [get_or_create(ServingTemperature, clean_value(row["ServingTemperature"]))]

    for ing in clean_value(row["Ingredient"]).split(","):
        ing = ing.strip()
        if ing:
            bev.hasIngredient.append(get_or_create(Ingredient, ing))

    for flavor in clean_value(row["FlavorProfile"]).split(","):
        flavor = flavor.strip()
        if flavor:
            bev.hasFlavorProfile.append(get_or_create(FlavorProfile, flavor))

    print(f"✅ Added beverage: {bev_name}")

print("\nProcessing dishes...")
print(df_dish.head())
for idx, row in df_dish.iterrows():
    dish_name = clean_value(row["DishName"]).replace(" ", "_")
    dish = Dish(dish_name)
    dish.hasDescription = [clean_value(row["Description"])]
    #dish.isGermanStaple = [clean_value(row["IsGermanStaple"]).lower() == "yes"]
    try:
        dish.hasPreparationTimeMinutes = [float(clean_value(row["PreparationTimeMinutes"]))]
    except:
        dish.hasPreparationTimeMinutes = [0.0]

    dish.hasRegion = [get_or_create(Region, r.strip()) for r in clean_value(row["Region"]).split(",") if r.strip()]
    dish.hasMainIngredient = [get_or_create(MainIngredient, clean_value(row["MainIngredient"]))]
    #dish.hasServingTemperature = [get_or_create(ServingTemperature, clean_value(row["ServingTemperature"]))]

    for ing in clean_value(row["Ingredient"]).split(","):
        ing = ing.strip()
        if ing:
            dish.hasIngredient.append(get_or_create(Ingredient, ing))

    for flavor in clean_value(row["FlavorProfile"]).split(","):
        flavor = flavor.strip()
        if flavor:
            dish.hasFlavorProfile.append(get_or_create(FlavorProfile, flavor))

    for item, cls in [("DietType", DietType), ("MealEatenAtPartOfDay", MealEatenAtPartOfDay),
                      ("MeatCut", MeatCut), ("PreparationMethod", PreparationMethod),
                      ("StateOfMainIngredient", StateOfMainIngredient), ("Variation", Variation)]:
        val = clean_value(row.get(item, ""))
        if val:
            dish.__getattr__(f"has{item}").append(get_or_create(cls, val))

    print(f"✅ Added dish: {dish_name}")

# Save ontology
output_path = "../ontology-owl/german_beverages_dishes.rdf"
print(f"\nSaving ontology to: {output_path} ...")
onto.save(file=output_path, format="rdfxml")
print("Ontology saved.")
