import csv
import time
import os
import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# German character map for normalization
CHAR_MAP = {
    "ä": "ae", "ö": "oe", "ü": "ue",
    "Ä": "Ae", "Ö": "Oe", "Ü": "Ue",
    "ß": "ss"
}

def normalize(text):
    for k, v in CHAR_MAP.items():
        text = text.replace(k, v)
    return text

def setup_driver():
    chrome_options = Options()
    # Disable headless mode to allow CAPTCHA solving
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("start-maximized")

    # Set a realistic User-Agent
    user_agent = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/115.0.0.0 Safari/537.36")
    chrome_options.add_argument(f"user-agent={user_agent}")
    chrome_options.add_argument("--incognito")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def scrape_rewe_dishes():
    driver = setup_driver()
    base_url = "https://www.rewe.de/rezeptsammlung/deutschland/?pageNumber=7"
    all_dishes = set()

    
    url = base_url
    try:
        driver.get(url)
        print(f"[INFO] Loaded page : {url}")
        print("→ Please solve any CAPTCHA manually if it appears...")

            # Allow time for CAPTCHA (or page to load)
        time.sleep(3)

        recipe_tiles = driver.find_elements(By.CSS_SELECTOR, '[data-testid="recipe-tile-component"]')

        if not recipe_tiles:
            print("[WARN] No recipe tiles found — possible CAPTCHA or layout issue.")
            input("🔒 Press [Enter] after solving CAPTCHA and verifying page is fully loaded...")

        for tile in recipe_tiles:
            try:
                link = tile.find_element(By.TAG_NAME, "a")
                dish_name = normalize(link.text.strip())
                if dish_name:
                    if dish_name not in all_dishes:
                        print("✔ dish parsed:", dish_name)
                    all_dishes.add(dish_name)
            except Exception as e:
                print("❌ Fehler beim Parsen eines Rezepts:", e)
                continue

            # Add randomized delay (10–20s) between pages
        delay = random.randint(2, 4)
        print(f"⏳ Waiting {delay} seconds before next page...")
        time.sleep(delay)

    except Exception as e:
        print(f"[ERROR] on page: {e}")
        

    driver.quit()
    return sorted(all_dishes)

# Save to CSV
rewe_dishes = scrape_rewe_dishes()
csv_path = "./data/rewe_deutsche_gerichte7.csv"

# Ensure data directory exists
os.makedirs(os.path.dirname(csv_path), exist_ok=True)

with open(csv_path, "w", newline='', encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["DishName"])
    for dish in rewe_dishes:
        writer.writerow([dish])

print(f"\n✅ Successfully saved {len(rewe_dishes)} dishes to {csv_path}")
