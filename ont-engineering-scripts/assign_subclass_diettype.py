from owlready2 import *

# Load ontology
onto = get_ontology("../ontology-owl/test.owl").load()

# Ensure DietType and subclasses exist in ontology
with onto:
    class DietType(Thing): pass
    class Omnivore(DietType): pass
    class Vegetarian(DietType): pass
    class Vegan(DietType): pass
    class Halal(DietType): pass
    class Kosher(DietType): pass
    class Anytime(DietType): pass

# Keyword mapping (lowercase)
keyword_to_class = {
    "omnivore": Omnivore,
    "vegetarian": Vegetarian,
    "vegan": Vegan,
    "halal": Halal,
    "kosher": Kosher,
    "anytime": Anytime
}

# Get Dish class
Dish = onto.search_one(iri="*#Dish")
if not Dish:
    raise Exception("❌ Dish class not found in ontology.")

# Process all Dish instances
for dish in Dish.instances():
    print(f"\n🍽️ Processing dish: {dish.name}")

    if not hasattr(dish, "hasDietType") or not dish.hasDietType:
        print("⚠️ No diet type found.")
        continue

    for dt in dish.hasDietType:
        label = dt.name
        if not label:
            print("⚠️ Diet type has no label.")
            continue

        print(f"🔍 Detected diet label: {label}")

        # Normalize and split by comma/underscore/whitespace
        raw_labels = label.lower().replace("_", ",").replace(" ", ",").split(",")
        parsed_labels = [d for d in raw_labels if d]

        for diet_name in parsed_labels:
            if diet_name in keyword_to_class:
                subclass = keyword_to_class[diet_name]
                if subclass not in dish.is_a:
                    dish.is_a.append(subclass)
                    print(f"✅ Assigned {dish.name} to subclass {subclass.name}")
            else:
                print(f"⚠️ Unknown diet type label: {diet_name}")

# Save the modified ontology
output_file = "dietsubclasses.owl"
onto.save(file=output_file, format="rdfxml")
print(f"\n✅ Ontology saved to {output_file}")
