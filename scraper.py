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

            # Optionally update cached games
            update_game_list(games)
            callback(games)
        else:
            print("Game list element not found in page source.")

    except Exception as e:
        print(f"Error fetching the page: {e}")
    finally:
        driver.quit()

def generate_random_filename():
    return f"list_{''.join(random.choices(string.ascii_letters + string.digits, k=5))}.json"

def compare_and_delete_files(new_file, cached_file):
    with open(new_file, "r", encoding="utf-8") as new_f, open(cached_file, "r", encoding="utf-8") as cached_f:
        new_games = json.load(new_f)
        cached_games = json.load(cached_f)

    new_titles = {game[0] for game in new_games}
    cached_titles = {game[0] for game in cached_games}

    added_games = new_titles - cached_titles

    if added_games:
        print(f"New games added: {added_games}")

    # Delete the temporary file
    os.remove(new_file)

def update_game_list(new_games):
    cached_file = "cached_games.json"
    new_file = generate_random_filename()

    with open(new_file, "w", encoding="utf-8") as file:
        json.dump(new_games, file, indent=4)

    if os.path.exists(cached_file):
        compare_and_delete_files(new_file, cached_file)

    # Sort games alphabetically by title and save to cache
    sorted_games = sorted(new_games, key=lambda x: x[0])
    with open(cached_file, "w", encoding="utf-8") as file:
        json.dump(sorted_games, file, indent=4)

def load_cached_games():
    if os.path.exists("cached_games.json"):
        with open("cached_games.json", "r", encoding="utf-8") as file:
            return json.load(file)
    return []

if __name__ == "__main__":
    # Example usage
    def print_games(games):
        for title, url in games:
            print(f"Title: {title}, URL: {url}")

    get_game_list(print_games, "chromedriver.exe", "https://steamunlocked.net/all-games-2/")
