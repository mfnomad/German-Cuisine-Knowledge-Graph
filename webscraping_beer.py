import requests
from bs4 import BeautifulSoup
import csv
import time

BASE_URL = "https://de.wikipedia.org"
START_URL = BASE_URL + "/wiki/Kategorie:Biersorte"

# Mapping for German umlauts and ß
GERMAN_CHAR_MAP = {
    "ä": "ae", "ö": "oe", "ü": "ue",
    "Ä": "Ae", "Ö": "Oe", "Ü": "Ue",
    "ß": "ss"
}

def normalize_german(text):
    for char, replacement in GERMAN_CHAR_MAP.items():
        text = text.replace(char, replacement)
    return text

def get_beer_links(url):
    beer_names = []

    while url:
        print(f"Fetching page: {url}")
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")

        # Find beer names in category list
        for li in soup.select(".mw-category li a"):
            beer_name = li.text.strip()
            if beer_name:
                beer_name_normalized = normalize_german(beer_name)
                beer_names.append(beer_name_normalized)

        # Check for next page in category (pagination)
        next_link = soup.find("a", string="nächste Seite")
        if next_link:
            url = BASE_URL + next_link.get("href")
            time.sleep(1)  # polite delay
        else:
            url = None

    return beer_names

def save_to_csv(names, filename="biersorten.csv"):
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Biersorte"])
        for name in sorted(set(names)):
            writer.writerow([name])
    print(f"Saved {len(set(names))} unique beer types to {filename}")

if __name__ == "__main__":
    all_beers = get_beer_links(START_URL)
    save_to_csv(all_beers)
