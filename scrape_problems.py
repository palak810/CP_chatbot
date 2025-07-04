import os
import json
import time
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

PROBLEMS_DIR = 'data/problems'
os.makedirs(PROBLEMS_DIR, exist_ok=True)

def scrape_editorial(problem_id, contest_id, letter):
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    driver = uc.Chrome(options=options)
    url = f"https://codeforces.com/contest/{contest_id}/problem/{letter}"

    editorial_text = ""
    try:
        driver.get(url)
        # Try to find the "Tutorial (en)" link
        try:
            tutorial_link = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.LINK_TEXT, "Tutorial (en)"))
            )
            tutorial_link.click()
        except Exception:
            print(f"No 'Tutorial (en)' link for {problem_id}")
            return

        # Switch to the new window
        WebDriverWait(driver, 10).until(EC.number_of_windows_to_be(2))
        driver.switch_to.window(driver.window_handles[1])

        # Wait for the blog content to load
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "ttypography")))
        soup = BeautifulSoup(driver.page_source, "html.parser")
        # Extract all text from the blog post
        content_div = soup.find("div", class_="ttypography")
        if content_div:
            editorial_text = content_div.get_text(separator="\n", strip=True)
        else:
            print(f"Editorial content not found for {problem_id}")

    except Exception as e:
        print(f"❌ Failed to get editorial for {problem_id}: {e}")
    finally:
        driver.quit()

    # Save editorial to the JSON file
    path = os.path.join(PROBLEMS_DIR, f"{problem_id}.json")
    data = {}
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    data['editorial'] = editorial_text
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    for filename in os.listdir(PROBLEMS_DIR):
        if filename.endswith(".json"):
            pid = filename.replace(".json", "")
            contest = ''.join(filter(str.isdigit, pid))
            letter = ''.join(filter(str.isalpha, pid))
            print(f"📘 Scraping editorial for {pid}")
            scrape_editorial(pid, contest, letter)
