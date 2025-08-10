import rdflib
import ollama

'''
BEFORE RUNNING: delete Subclasses of Dish from .owl file

'''


# === CONFIG ===
ONTOLOGY_PATH = "updated_ontology2.owl"           # Path to your ontology file
OUTPUT_PATH = "classified_dishes.owl"             # Output file with classifications
DISH_CLASS_URI = "http://example.org/german-cuisine#Dish"
DISH_SUBCLASS_BASE = "http://example.org/german-cuisine#"  # Base for subclass URIs
MODEL_NAME = "gemma3:1b"  # Ollama model name

# === SUBCLASSES ===
DISH_SUBCLASSES = [
    "Condiment",
    "Dessert",
    "Appetizer",
    "Soup",
    "MainCourse",
    "Snack"
]

def load_ontology(path):
    print("[INFO] Loading ontology...")
    g = rdflib.Graph()
    g.parse(path)
    print(f"[INFO] Ontology loaded. Total triples: {len(g)}")
    return g

def uri_to_label(uri):
    """Convert last part of URI to readable label."""
    return uri.split('#')[-1].replace('_', ' ')

def get_dish_instances(graph):
    print("[INFO] Querying all Dish instances...")
    q = f"""
    SELECT ?dish
    WHERE {{
        ?dish a <{DISH_CLASS_URI}> .
    }}
    """
    results = graph.query(q)
    dishes = [str(row.dish) for row in results]
    print(f"[INFO] Found {len(dishes)} dishes.")
    return dishes

def classify_dish_with_llm(dish_name):
    print(f"[INFO] Classifying dish: {dish_name}")
    prompt = f"""
    You are a domain expert in German cuisine.
    Classify the following dish into exactly one of these categories: 
    {', '.join(DISH_SUBCLASSES)}.

    Dish: "{dish_name}"

    Respond with only the category name.
    """
    response = ollama.chat(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}]
    )
    category = response["message"]["content"].strip()
    print(f"[RESULT] '{dish_name}' classified as '{category}'\n")
    return category

def main():
    g = load_ontology(ONTOLOGY_PATH)
    dishes = get_dish_instances(g)

    # Limit to first 5 dishes for testing
    dishes = dishes[:5]

    results = {}
    for dish_uri in dishes:
        dish_name = uri_to_label(dish_uri)
        print(f"[INFO] Processing dish: {dish_name}")
        
        category = classify_dish_with_llm(dish_name)
        results[dish_uri] = category

        # Remove ONLY the rdf:type Dish triple
        g.remove((
            rdflib.URIRef(dish_uri),
            rdflib.RDF.type,
            rdflib.URIRef(DISH_CLASS_URI)
        ))

        # Add the finer-grained subclass type
        g.add((
            rdflib.URIRef(dish_uri),
            rdflib.RDF.type,
            rdflib.URIRef(DISH_SUBCLASS_BASE + category)
        ))

        # Ensure each dish has a label for visibility
        g.add((
            rdflib.URIRef(dish_uri),
            rdflib.RDFS.label,
            rdflib.Literal(dish_name)
        ))

    # Save updated ontology
    g.serialize(destination=OUTPUT_PATH, format="xml")
    print(f"[INFO] Ontology saved to {OUTPUT_PATH}")

    # Print summary
    print("[SUMMARY] Final classification results:")
    for uri, category in results.items():
        print(f"{uri} -> {category}")

if __name__ == "__main__":
    main()
