import requests
from bs4 import BeautifulSoup
import csv
import re

# Map for replacing German special characters
CHAR_MAP = {
    "ä": "ae", "ö": "oe", "ü": "ue",
    "Ä": "Ae", "Ö": "Oe", "Ü": "Ue",
    "ß": "ss"
}

def normalize(text):
    for k, v in CHAR_MAP.items():
        text = text.replace(k, v)
    return text

def scrape_german_dishes():
    url = "https://de.wikipedia.org/wiki/Kategorie:Deutsche_K%C3%BCche"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    content_div = soup.find("div", id="mw-pages")
    dish_names = []

    if content_div:
        for ul in content_div.find_all("ul"):
            for li in ul.find_all("li"):
                title = li.get_text(strip=True)
                title = re.sub(r"\s*\[.*?\]$", "", title)  # remove footnotes if any
                normalized_title = normalize(title)
                dish_names.append(normalized_title)

    return sorted(set(dish_names))

# Scrape and save to CSV
dishes = scrape_german_dishes()
csv_path = "./data/deutsche_gerichte.csv"

if dishes:
    with open(csv_path, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["DishName"])
        for dish in dishes:
            writer.writerow([dish])

    print(f" Saved {len(dishes)} dishes to: {csv_path}")
else:
    print("⚠️ No dishes found or an error occurred.")
