import json
import os
import sys
import time
import requests
import re
from bs4 import BeautifulSoup

# --- Selenium and WebDriver imports ---
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- Path setup ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.logger import log

# --- Constants ---
LIST_URL = "https://www.adcc.gov.hk/zh-hk/alerts.html"
URL_TEMPLATE = "https://www.adcc.gov.hk/zh-hk/alerts-detail/alerts-{}.html"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
OUTPUT_FILENAME = "scraped_alerts.json"
LIMIT = None # Set to None to fetch all articles

def load_existing_urls(filepath):
    """
    Read the existing JSON file and return a set of article URLs for quick lookup.
    """
    if not os.path.exists(filepath):
        return set()
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return {item['link'] for item in data if 'link' in item}
    except (json.JSONDecodeError, IOError) as e:
        log.error(f"Error reading existing data file: {e}. Starting fresh.")
        return set()

def get_all_article_urls_via_render():
    """
    Stage 1: Use Selenium to render the JavaScript-driven page, parse the HTML,
    extract article IDs and construct their detail URLs.
    """
    log.info("--- STAGE 1: Using Selenium once to render the page and extract all IDs ---")
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--start-maximized")
    options.add_argument("--no-sandbox")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")
    
    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    try:
        driver.get(LIST_URL)
        list_page_selector = "a._grid-item"
        log.info("Waiting for JavaScript to render all article items...")
        
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, list_page_selector)))
        time.sleep(5) 

        log.info("Page rendered. Grabbing final HTML source...")
        html_source = driver.page_source
        
    finally:
        driver.quit()
        log.info("Selenium's job is done. WebDriver closed.")

    soup = BeautifulSoup(html_source, 'html.parser')
    urls = []
    article_items = soup.select("a._grid-item")
    
    for item in article_items:
        img_tag = item.select_one("img")
        if img_tag and img_tag.get('src'):
            img_src = img_tag.get('src')
            match = re.search(r'(\d{19})', img_src)
            if match:
                article_id = match.group(1)
                urls.append(URL_TEMPLATE.format(article_id))
    
    unique_urls = list(set(urls))
    log.info(f"URL construction complete. Found {len(unique_urls)} unique URLs on the site.")
    return unique_urls

def scrape_article_details(url, session):
    """
    Stage 2: Use multiple selector strategies to robustly scrape the details
    of a single article page.
    """
    try:
        response = session.get(url, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        title_tag = soup.select_one("h1._content-title") or soup.select_one("h1._page-title")
        date_tag = soup.select_one("div.publish-date")
        content_tag = soup.select_one("div.fr-view") or soup.select_one("div._rich-text")

        title = title_tag.get_text(strip=True) if title_tag else "Title not found"
        date = date_tag.get_text(strip=True) if date_tag else ""
        content = ""
        if content_tag:
            content = content_tag.get_text(strip=True, separator='\n')

        if not content:
            log.warning(f"  -> Content not found with primary selectors for {url}. Check page structure.")
        
        return {
            "title": title, 
            "date": date, 
            "link": url, 
            "source": "ADCC", 
            "content": content
        }
    except Exception as e:
        log.error(f"  -> Failed to parse {url}. Error: {e}")
        return None

def process_data(data):
    """
    Process the list of data items to move date from title to date field if applicable.
    """
    date_pattern = re.compile(r'(\d{4}-\d{2}-\d{2})$')
    
    for item in data:
        title = item.get('title', '')
        match = date_pattern.search(title)
        if match:
            extracted_date = match.group(1)
            # Move to date field if it's empty or doesn't exist
            if 'date' not in item or not item['date']:
                item['date'] = extracted_date
            # Remove the date from the title
            item['title'] = title[:match.start()].strip()
    return data

def main():
    """
    Main program that orchestrates the scraping and incremental update flow.
    """
    output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILENAME)
    
    # Step 1: Load existing URLs
    existing_urls = load_existing_urls(output_path)
    log.info(f"Found {len(existing_urls)} existing articles in the local data file.")

    # Step 2: Get all latest URLs from the site
    all_site_urls = get_all_article_urls_via_render()

    # Step 3: Identify which URLs are new and need scraping
    new_urls_to_scrape = [url for url in all_site_urls if url not in existing_urls]
    
    if not new_urls_to_scrape:
        log.info("--- No new articles to scrape. The local data is up-to-date. ---")
        return

    log.info(f"--- STAGE 2: Found {len(new_urls_to_scrape)} new articles. Starting precise content scraping ---")
    new_data = []
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
    })

    for i, url in enumerate(new_urls_to_scrape):
        log.info(f"Scraping new article {i+1}/{len(new_urls_to_scrape)}...")
        data = scrape_article_details(url, session)
        if data and data['content']: # Only add entries that have content
            new_data.append(data)
        elif data:
            log.warning(f"  -> Scraped data for {url} has no content. Skipping.")
        time.sleep(0.1)

    if not new_data:
        log.info("--- No new articles with content were found. Data file remains unchanged. ---")
        return

    existing_data = []
    if os.path.exists(output_path):
        with open(output_path, 'r', encoding='utf-8') as f:
            try:
                existing_data = json.load(f)
            except json.JSONDecodeError:
                log.error("Could not parse existing JSON file. It will be overwritten.")

    combined_data = existing_data + new_data
    
    # Process the combined data to handle date extraction
    combined_data = process_data(combined_data)
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(combined_data, f, ensure_ascii=False, indent=4)
        
    log.info(f"Scraping complete. Added {len(new_data)} new articles.")
    log.info(f"Total articles now: {len(combined_data)}.")
    log.info(f"Data saved to: {output_path}")


if __name__ == "__main__":
    main()