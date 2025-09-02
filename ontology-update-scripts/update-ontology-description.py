import pandas as pd
from rdflib import Graph, Namespace, Literal, RDF, URIRef
from rdflib.namespace import RDFS, OWL

# === Load Ontology ===
g = Graph()
g.parse("v8-ontology.rdf", format="xml")
print("Ontology loaded")

# Define namespaces (adapt to your ontology!)
EX = Namespace("http://example.org/german-cuisine#")
g.bind("gc", EX)

# === Load CSVs ===
df_dishes = pd.read_csv("dishes.csv")
df_drinks = pd.read_csv("drinks.csv")
print("CSV files loaded")

# Track missing names
missing_dishes = []
missing_drinks = []

# === Helper function ===
def update_descriptions(df, category, missing_list):
    print("Running update_descriptions")

    for _, row in df.iterrows():
        name = str(row["Name"]).strip()
        desc = str(row["Description"]).strip()

        # Create URI for the individual
        ind_uri = EX[name]

        if (ind_uri, None, None) in g:
            print(f"Found in ontology: {name}")

            # Remove old description triples
            g.remove((ind_uri, EX.hasDescription, None))

            # Add new description
            g.add((ind_uri, EX.hasDescription, Literal(desc)))

            print(f"✅ Updated {category} '{name}' with description: {desc}")
        else:
            print(f"❌ {category} '{name}' not found in ontology")
            missing_list.append(row)


# === Update dishes ===
update_descriptions(df_dishes, "Dish", missing_dishes)

# === Update drinks ===
update_descriptions(df_drinks, "Drink", missing_drinks)

# === Save new unique rows ===
if missing_dishes:
    pd.DataFrame(missing_dishes).to_csv("dishes_new_unique.csv", index=False, encoding="utf-8-sig")
if missing_drinks:
    pd.DataFrame(missing_drinks).to_csv("drinks_new_unique.csv", index=False, encoding="utf-8-sig")

# === Save updated ontology ===
g.serialize(destination="v9-ontology.rdf", format="xml")

print("🎉 Ontology update complete. Saved as v9-ontology.rdf")
