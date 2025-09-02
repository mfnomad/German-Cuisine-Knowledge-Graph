import csv
from datetime import datetime

import random
import time
from httpx import TimeoutException
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException

# Setup Selenium (headless browser for scraping)
options = webdriver.ChromeOptions()
#options.add_argument("--headless")   # comment this if you want to see the browser
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(options=options)

# Open TasteAtlas Germany page
url = "https://www.tasteatlas.com/germany"
driver.get(url)

wait = WebDriverWait(driver, 10)

# Keep clicking "VIEW MORE" only inside the dishes container
clicks = 0
while True:
    try:
        view_more = wait.until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//div[contains(@class,'similar-list__container')]//button[contains(text(), 'VIEW MORE')]"
            ))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", view_more)
        time.sleep(random.uniform(1,2))
        view_more.click()
        time.sleep(random.uniform(3,6))
        clicks += 1
        print(f"Clicked 'VIEW MORE' {clicks} times...")
        time.sleep(2)  # wait for new content to load
    except TimeoutException:
        print("No more 'VIEW MORE' button in dishes container.")
        break
    except ElementClickInterceptedException:
        print("Scroll issue, retrying...")
        driver.execute_script("arguments[0].scrollIntoView(true);", view_more)
        time.sleep(1)
        continue



# Step 2: Click on "Dishes"
dishes_tab = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Dishes')]")))
driver.execute_script("arguments[0].scrollIntoView(true);", dishes_tab)
time.sleep(1)
dishes_tab.click()
time.sleep(2)

# Step 3: Scrape dish names + descriptions
results = []
dishes = driver.find_elements(By.CSS_SELECTOR, ".search-results__item-info")
for dish in dishes:
    try:
        name_el = dish.find_element(By.CSS_SELECTOR, "h2.h2 a")
        desc_el = dish.find_element(By.CSS_SELECTOR, ".search-results__item-description p")

        results.append({
            "name": name_el.text.strip(),
            "description": desc_el.text.strip()
        })
    except Exception:
        continue

# Save to CSV
filename = f"scraped_data_{datetime.now().strftime('%Y_%m_%d')}.csv"
with open(filename, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["Name", "Description"])
    for item in results:
        writer.writerow([item["name"], item["description"]])

print(f"✅ Saved {len(results)} records to {filename}")