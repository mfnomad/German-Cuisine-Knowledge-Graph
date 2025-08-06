from owlready2 import *
import os

# === Load ontology ===
onto_path.append("../ontology-owl")  # Make sure you're in the same directory
onto = get_ontology("test.owl").load()

# === Define the class hierarchy base ===
Beverage = onto.search_one(iri="*#Beverage")
if not Beverage:
    raise ValueError("Beverage class not found.")

# Ensure Alcoholic and NonAlcoholic exist
with onto:
    Alcoholic = onto.search_one(iri="*#Alcoholic") or types.new_class("Alcoholic", (Beverage,))
    NonAlcoholic = onto.search_one(iri="*#NonAlcoholic") or types.new_class("NonAlcoholic", (Beverage,))

# === Define beverage type lists ===
non_alcoholic_types = {
    "Coffee", "FermentedNonAlcoholic", "Herbal_Infusion", "Hot_Chocolate", "Icetea",
    "Juice", "MaltNonAlcoholic", "Soda", "Water", "Tea", "Fermented_beverage", "Hot_Beverage", "Non-alcoholic_Beer", "Infusion"
}
alcoholic_types = {
    "Beer", "Brandy", "Cocktail", "Digestif", "FermentedAlcoholic", 
    "Liqeur", "Spirit", "Spritzer", "Wine", "Spirits", "Malt_beverage", "Liquor", " Liqeur", "Liqueur"
}

# === Process individuals ===
for indiv in Beverage.instances():

    beverage_types = list(indiv.hasBeverageType)
    
    for btype in beverage_types:
        type_name = btype.name
        if not type_name:
            print(f"⚠️ Empty type name for {indiv.name}, skipping...")
            continue

        subclass_name = type_name[0].upper() + type_name[1:]  # Capitalize
        parent_class = None

        if subclass_name in alcoholic_types:
            parent_class = Alcoholic
        elif subclass_name in non_alcoholic_types:
            parent_class = NonAlcoholic
        else:
            print(f"⚠️ Unknown beverage type: {subclass_name}")
            print(f"Available types: {', '.join(alcoholic_types.union(non_alcoholic_types))}")
            print(f"Skipping {indiv.name}...")
            continue  # Skip unknowns

        # Find or create subclass
        subclass = onto.search_one(iri="*#" + subclass_name)
        if not subclass or not isinstance(subclass, ThingClass):
            with onto:
                print(f"Creating subclass: {subclass_name} for {indiv.name}")
                subclass = types.new_class(subclass_name, (parent_class,))

        # Assign individual to the subclass
        if subclass not in indiv.is_a:
            indiv.is_a.append(subclass)

        # Optional: remove Beverage from is_a if you want
        if Beverage in indiv.is_a:
            indiv.is_a.remove(Beverage)

# === Save updated ontology ===
output_file = "beveragetypes-merged.owl"
onto.save(file=output_file, format="rdfxml")
print(f"✅ Ontology saved to {output_file}")
