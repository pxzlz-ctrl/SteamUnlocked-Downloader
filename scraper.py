import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import os
import random
import string

def get_game_list(callback, driver_path, url):
    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--disable-gpu")  # Disable GPU
    chrome_options.add_argument("--no-sandbox")  # Bypass OS security model
    chrome_options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems
    chrome_options.add_argument("--window-size=1920x1080")  # Set window size to mimic a real user
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    # Set up the WebDriver
    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        driver.get(url)
        # Wait for the specific element to be present
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="main-wrapper"]/div/div/div/div[1]/div/div[3]/ul'))
        )
        # Get the page source
        page_source = driver.page_source

        # Save the page source to a file
        with open("page_source.html", "w", encoding="utf-8") as file:
            file.write(page_source)

        print("Page source saved to 'page_source.html'")

        # Process the page source with BeautifulSoup
        soup = BeautifulSoup(page_source, "html.parser")
        game_list_element = soup.select_one('#main-wrapper > div > div > div > div:nth-child(1) > div > div:nth-child(3) > ul')
        if game_list_element:
            games = []
            for li in game_list_element.find_all('li'):
                a_tag = li.find('a')
                title = a_tag.get_text(strip=True)
                url = a_tag['href']
                games.append((title, url))

            new_cache_file = update_game_list(games)
            compare_with_cached_games(new_cache_file, callback)
        else:
            print("Game list element not found in page source.")

    except Exception as e:
        print(f"Error fetching the page: {e}")
    finally:
        driver.quit()

def update_game_list(new_games):
    # Generate a random 5-letter and number combination for the new cache file name
    random_suffix = ''.join(random.choices(string.ascii_letters + string.digits, k=5))
    new_cache_file = f"list_{random_suffix}.json"

    sorted_games = sorted(new_games, key=lambda x: x[0])
    with open(new_cache_file, "w", encoding="utf-8") as file:
        json.dump(sorted_games, file, indent=4)
    
    return new_cache_file

def load_cached_games():
    if os.path.exists("cached_games.json"):
        with open("cached_games.json", "r", encoding="utf-8") as file:
            return json.load(file)
    return []

def compare_with_cached_games(new_cache_file, callback):
    cached_games = load_cached_games()
    new_games = []

    with open(new_cache_file, "r", encoding="utf-8") as file:
        new_games = json.load(file)

    cached_titles = {title for title, url in cached_games}
    new_titles = {title for title, url in new_games}

    added_games = [game for game in new_games if game[0] not in cached_titles]

    if added_games:
        callback(added_games)
    else:
        print("No new games found.")

if __name__ == "__main__":
    # Example usage
    def print_games(games):
        for title, url in games:
            print(f"Title: {title}, URL: {url}")

    get_game_list(print_games, "chromedriver.exe", "https://steamunlocked.net/all-games-2/")
