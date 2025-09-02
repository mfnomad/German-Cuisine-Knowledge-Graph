import html
import requests
import pandas as pd
from bs4 import BeautifulSoup

BASE_URL = "https://www.tasteatlas.com/api/v3/regions/55/data"
LOGIN_URL = "https://www.tasteatlas.com/account/LoginAjax"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://www.tasteatlas.com/"
}
PAGE_SIZE = 18

login_payload = {
    "Email": "aqil.ghazali2@gmail.com",
    "Password": "germancuisinekg",
    "RememberMe": "true"
}

LOGIN_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://www.tasteatlas.com",
    "Referer": "https://www.tasteatlas.com/"
}



def normalize_german_chars(text: str) -> str:
    """Replace German special characters with neutral forms."""
    return (
        text.replace("ä", "ae")
        .replace("Ä", "Ae")
        .replace("ö", "oe")
        .replace("Ö", "Oe")
        .replace("ü", "ue")
        .replace("Ü", "Ue")
        .replace("ß", "ss")
        .replace("\n", " ")
    )


def login_session():
    """Start a logged-in session with TasteAtlas."""
    session = requests.Session()
    resp = session.post(LOGIN_URL, data=login_payload, headers=LOGIN_HEADERS)
    print("Login response:", resp.text[:200], "...")
    return session


def fetch_dishes(session):
    print("Starting to fetch dishes...")
    dishes = []
    page = 0

    while True:
        url = f"{BASE_URL}?filters=1&page={page}&pageSize={PAGE_SIZE}&regionWhatToEatSortEnum=1&userViewpointRegionId=55"
        print(f"Fetching page {page} (dishes)...")
        response = session.get(url, headers=HEADERS)

        if response.status_code != 200:
            print("Error fetching dishes:", response.status_code)
            break

        data = response.json()
        items = data.get("Data", [])
        if not items:
            print("No more dishes.")
            break

        for item in items:
            if item.get("EntityType") == 1:  # dish
                name = normalize_german_chars(item.get("Name", ""))
                desc = normalize_german_chars(item.get("Description", ""))

                
                desc = html.unescape(desc)
            
                # strip tags if needed
                desc = BeautifulSoup(desc, "html.parser").get_text()
            
                # strip tags if needed

                print(f"Found dish: {name}")
                dishes.append({"Name": name, "Description": desc})

        page += 1

    return dishes


def fetch_drinks(session):
    print("Starting to fetch drinks...")
    drinks = []
    page = 0

    while True:
        url = f"{BASE_URL}?filters=2&page={page}&pageSize={PAGE_SIZE}&regionWhatToEatSortEnum=1&userViewpointRegionId=55"
        print(f"Fetching page {page} (drinks)...")
        response = session.get(url, headers=HEADERS)

        if response.status_code != 200:
            print("Error fetching drinks:", response.status_code)
            break

        data = response.json()
        items = data.get("Data", [])
        if not items:
            print("No more drinks.")
            break

        for item in items:
            if item.get("EntityType") == 2:  # beverage
                name = normalize_german_chars(item.get("Name", ""))
                desc = normalize_german_chars(item.get("Description", ""))

                desc = html.unescape(desc)
            
                # strip tags if needed
                desc = BeautifulSoup(desc, "html.parser").get_text()

                print(f"Found drink: {name}")
                drinks.append({"Name": name, "Description": desc})

        page += 1

    return drinks


if __name__ == "__main__":
    session = login_session()

    # fetch dishes
    dish_list = fetch_dishes(session)
    df = pd.DataFrame(dish_list)
    df.to_csv("dishes.csv", index=False, encoding="utf-8-sig")
    print("Saved to dishes.csv")

    # fetch drinks
    drink_list = fetch_drinks(session)
    df = pd.DataFrame(drink_list)
    df.to_csv("drinks.csv", index=False, encoding="utf-8-sig")
    print("Saved to drinks.csv")
