import re
from owlready2 import get_ontology, Thing
from urllib.parse import urlparse

# Load the ontology
onto = get_ontology("../ontology-owl/v1-ontology.owl").load()

# Find the base classes
Dish = onto.search_one(iri="*#Dish")
MealEatenAtPartOfDay = onto.search_one(iri="*#MealEatenAtPartOfDay")

# Define subclasses of MealEatenAtPartOfDay at program start
with onto:
    class Anytime(MealEatenAtPartOfDay):
        pass
    
    class Breakfast(MealEatenAtPartOfDay):
        pass
    
    class Lunch(MealEatenAtPartOfDay):
        pass
    
    class Dinner(MealEatenAtPartOfDay):
        pass

# Create instances of each meal type
anytime_instance = Anytime("anytime")
breakfast_instance = Breakfast("breakfast")
lunch_instance = Lunch("lunch")
dinner_instance = Dinner("dinner")

# Map lowercase labels to ontology instances
meal_label_map = {
    "anytime": anytime_instance,
    "breakfast": breakfast_instance,
    "lunch": lunch_instance,
    "dinner": dinner_instance
}

def clean_label(label):
    """Convert to lowercase, strip spaces, and convert underscores to spaces (if needed)."""
    return label.strip(" _").lower().replace("_", " ")

# Process all dish instances
for dish in Dish.instances():
    print(f"\n🍽️ Processing dish: {dish.name}")
    
    existing_labels = getattr(dish, "hasMealEatenAtPartOfDay", [])
    print(f"🔍 Raw existing_labels: {existing_labels}")

    if not existing_labels:
        print("⚠️ No meal type found.")
        continue
    
    # Clear existing assignments
    #dish.hasMealEatenAtPartOfDay = []
    assigned_meals = set()
    

    print("🔍 Existing labels before processing: ", existing_labels)
    for i, m in enumerate(existing_labels):
        print(f"🔍 Processing label {i}: {m}")
        
        m_str = str(m)

        # Use regex to extract label fragment after 'german-cuisine.'
        match = re.search(r'german-cuisine\.([^\]]+)', m_str)
        print(f"🔍 Match found: {match}")
        if not match:
            print(f"⚠️ Could not extract fragment from: {m_str}")
            continue

        fragment = match.group(1)  # e.g. 'lunch,_dinner'
        print(f"🔍 Extracted fragment: '{fragment}'")

        # Split by comma
        raw_labels = fragment.split(',')
        print(f"🔍 Raw split labels: {raw_labels}")

        # Clean and normalize labels
        meal_labels = [clean_label(label) for label in raw_labels if label.strip()]
        print(f"🔍 Cleaned labels: {meal_labels}")

        for label in meal_labels:
            if label in meal_label_map and label not in assigned_meals:
                meal_instance = meal_label_map[label]
                dish.hasMealEatenAtPartOfDay.append(meal_instance)
                assigned_meals.add(label)
                print(f"✅ Assigned {label} to {dish.name}")
            elif label in assigned_meals:
                print(f"ℹ️ {label} already assigned to {dish.name}")
            else:
                print(f"⚠️ Unknown meal time label: '{label}'")

    if not assigned_meals:
        pass
        print(f"❌ No valid meal assignments for {dish.name}")
    else:
        print(f"✅ Assigned meals: {assigned_meals}")

# Save updated ontology
onto.save(file="updated_ontology.owl")
print("\n✅ Ontology saved with updated meal assignments.")
