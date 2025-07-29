import csv
import os

# Path where your CSV files are located
input_dir = "./"  # change this if your CSVs are in a subdirectory

# List of input files

input_files = [f"./data/webscraped-data/dishes{i}.csv" for i in range(1, 3)]
seen_dishes = set()
final_dishes = []

# Read and combine dish names
for file in input_files:
    file_path = os.path.join(input_dir, file)
    try:
        with open(file_path, newline='', encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                dish = row["DishName"].strip()
                if dish and dish not in seen_dishes:
                    seen_dishes.add(dish)
                    final_dishes.append(dish)
    except Exception as e:
        print(f"❌ Error reading {file_path}: {e}")

# Save to final output file
output_path = os.path.join(input_dir, "final_gerichte.csv")
with open(output_path, "w", newline='', encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["DishName"])
    for dish in sorted(final_dishes):
        writer.writerow([dish])

print(f"✅ Union completed. {len(final_dishes)} unique dishes written to {output_path}")
