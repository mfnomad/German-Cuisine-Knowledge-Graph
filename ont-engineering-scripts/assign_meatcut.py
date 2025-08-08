from owlready2 import get_ontology
from urllib.parse import urlparse

# === CONFIG ===
ONTOLOGY_PATH = "../ontology-owl/v2-ontology.owl"
OUTPUT_PATH = "updated_ontology2.owl"
DISH_CLASS_IRI = "*#Dish"
MEATCUT_PROPERTY = "hasMeatCut"  # Adjust if the actual property name differs

# === Load ontology ===
onto = get_ontology(ONTOLOGY_PATH).load()

# Find the Dish class
Dish = onto.search_one(iri=DISH_CLASS_IRI)
if not Dish:
    raise ValueError("❌ Could not find Dish class in ontology")

def extract_fragment(uri):
    """Extract fragment part from a URI/IRI."""
    path = urlparse(uri).fragment
    return path if path else uri.split('#')[-1]

# === Process all Dish instances ===
for dish in Dish.instances():
    if not hasattr(dish, MEATCUT_PROPERTY):
        continue  # Skip if no such property

    meatcuts = getattr(dish, MEATCUT_PROPERTY)

    if not meatcuts:
        continue

    for mc in meatcuts:
        # Handle case where mc is an ontology instance (IRI) or a string
        if hasattr(mc, "iri"):
            fragment = extract_fragment(mc.iri)
            print("iri fragment:", fragment)
        else:
            fragment = str(mc)
            print("string fragment:", fragment)

        fragment = fragment.strip(" '\"")  # Clean quotes and spaces

        # If it contains commas, keep only the first part
        if "," in fragment:
            first_cut = fragment.split(",")[0].strip()
            print(f"🔍 Found multiple cuts: {fragment} → {first_cut}")
            # Look up the ontology instance for this meat cut
            first_cut_instance = onto.search_one(iri="*" + first_cut)
            if first_cut_instance:
                setattr(dish, MEATCUT_PROPERTY, [first_cut_instance])
                print(f"🍖 Updated {dish.name}: {fragment} → {first_cut}")
            else:
                print(f"⚠️ No ontology entry found for '{first_cut}'")
        else:
            # No list, keep as is
            print(f"✅ {dish.name} already has single meat cut: {fragment}")

# === Save updated ontology ===
onto.save(file=OUTPUT_PATH)
print(f"\n✅ Ontology saved to {OUTPUT_PATH}")
