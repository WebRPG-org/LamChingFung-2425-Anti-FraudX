import os
import re
from bs4 import BeautifulSoup
from pymongo import MongoClient, UpdateOne
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

MONGO_CONNECTION_STRING = os.getenv("MONGO_CONNECTION_STRING", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "financialAI_db")

# Fix for Docker container name mismatch
if "mongo:27017" in MONGO_CONNECTION_STRING:
    MONGO_CONNECTION_STRING = MONGO_CONNECTION_STRING.replace("mongo:27017", "localhost:27017")
SFC_ALERT_URL = "https://www.sfc.hk/TC/alert-list"

def _expand_and_clean_entry(raw_text: str) -> list[str]:
    """
    Expand and clean plain text. This version assumes the input raw_text no longer contains HTML tags.
    """
    # remove annotations like "(只備有英文名稱)"
    text = re.sub(r'\(.*\)', '', raw_text).strip()
    
    # Use a unified regular expression to split multiple entities
    # Separators include: i), ii), a), b), " / ", and newlines
    split_pattern = r'\s*i{1,3}\)\s*|\s*[a-z]\)\s*|\s+/\s+|\n'
    
    entities = [e.strip() for e in re.split(split_pattern, text) if e and e.strip()]
    
    if not entities:
        return []
         
    return entities

def scrape_and_store_sfc_alerts_sync():
    print("Starting Selenium Chrome driver...")
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36")
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        print(f"Scraping SFC alert list from {SFC_ALERT_URL}...")
        driver.get(SFC_ALERT_URL)
        try:
            cookie_close_button = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "closeCookiesAlert")))
            cookie_close_button.click()
            print("Cookie consent window closed.")
        except TimeoutException:
            print("Cookie consent window not found, continuing execution.")
        
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "alert-list-append-here")))
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        client = MongoClient(MONGO_CONNECTION_STRING)
        db = client[MONGO_DB_NAME]
        collection = db.sfc_alert_list
        
        data_tbody = soup.find("tbody", id="alert-list-append-here")
        if not data_tbody:
            print("Error: Could not find table body (tbody).")
            return

        updates = []
        for row in data_tbody.find_all('tr'):
            cols = row.find_all('td')
            if len(cols) >= 3:
                # separator=' ' can add spaces at <br>, strip=True removes extra whitespace
                raw_name_text = cols[0].get_text(separator=' ', strip=True)
                
                expanded_names = _expand_and_clean_entry(raw_name_text)
                
                for name in expanded_names:
                    if not name:
                        continue
                    record = {
                        "add_date": cols[2].text.strip(),
                        "company_name": name,
                        "type": cols[1].text.strip(),
                        "source_url": SFC_ALERT_URL
                    }
                    updates.append(UpdateOne(
                        {"company_name": record["company_name"]},
                        {"$set": record},
                        upsert=True
                    ))
        
        if updates:
            result = collection.bulk_write(updates)
            print(f"SFC list synchronization completed: {result.bulk_api_result}")
        else:
            print("SFC list has no new updates.")
        
        client.close()

    except Exception as e:
        print(f"Error occurred while scraping SFC list with Selenium: {e}")
        debug_dir = "/app/debug_output"
        os.makedirs(debug_dir, exist_ok=True)
        driver.save_screenshot(os.path.join(debug_dir, "sfc_error_screenshot.png"))
        with open(os.path.join(debug_dir, "sfc_error_page.html"), "w", encoding="utf-8") as f:
            f.write(driver.page_source)
    finally:
        print("shutdown Selenium Chrome driver...")
        driver.quit()