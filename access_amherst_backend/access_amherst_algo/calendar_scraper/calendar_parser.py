import requests
import json
import os
import logging
from bs4 import BeautifulSoup
from datetime import datetime

BASE_URL = "https://www.amherst.edu/news/events/calendar"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Referer": "https://www.amherst.edu/",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
}

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("scraping_log.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def fetch_page(url):
    logger.info(f"Fetching URL: {url}")
    
    try:
        session = requests.Session()
        response = session.get(url, headers=headers)
        if response.status_code != 200:
            return None
        return response.content
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
        logger.error(f"Error fetching {url}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching {url}: {e}")
        return None

def scrape_page(url):
    logger.info(f"Scraping page: {url}")

    try:
        html = fetch_page(url)
        if not html:
            logger.warning(f"Page {url} does not exist or failed to load.")
            return []

        soup = BeautifulSoup(html, "html.parser")

        if "captcha" in soup.text.lower():
            logger.warning("CAPTCHA detected. Unable to scrape this page.")
            return []

        events = []
        for article in soup.find_all("article", class_="mm-calendar-event"):
            event = {
                "title": None,
                "author_name": None,
                "author_email": None,
                "pub_date": None,
                "host": None,
                "link": None,
                "picture_link": None,
                "event_description": None,
                "start_time": None,
                "end_time": None,
                "location": None
            }

            # Extract basic event information
            title_tag = article.find("h2", class_="mm-event-listing-title").find("a")
            if title_tag:
                event["title"] = title_tag.text.strip()
                event["link"] = title_tag["href"]

            period_tag = article.find("h3", class_="mm-calendar-period")
            if period_tag:
                start_meta = period_tag.find("meta", itemprop="startDate")
                if start_meta:
                    event["start_time"] = start_meta["content"]

                end_meta = period_tag.find("meta", itemprop="endDate")
                if end_meta:
                    event["end_time"] = end_meta["content"]

            location_tag = article.find("p", class_="mm-event-listing-location")
            if location_tag:
                event["location"] = location_tag.get_text(strip=True)

            description_tag = article.find("div", class_="mm-event-listing-description")
            if description_tag:
                event["event_description"] = description_tag.get_text(strip=True)

            picture_tag = article.find("img", itemprop="image")
            if picture_tag and "data-src" in picture_tag.attrs:
                event["picture_link"] = "https://www.amherst.edu" + picture_tag.attrs["data-src"]

            events.append(event)

        logger.info(f"Scraped {len(events)} events from {url}")
    
    except Exception as e:
        logger.error(f"Error Scraping page {url}: {e}")
        return []

    return events

def scrape_all_pages():
    logger.info("Starting scrape of all pages")
    page = 0
    all_events = []

    while True:
        url = f"{BASE_URL}?_page={page}"
        events = scrape_page(url)

        if not events:
            logger.info(f"No events found on page {page}. Stopping scrape.")
            break

        all_events.extend(events)
        logger.info(f"Total events scraped so far: {len(all_events)}")
        page += 1

    logger.info(f"Scraping completed. Total events scraped: {len(all_events)}")
    return all_events

def save_to_json(events):
    logger.info("Saving events to JSON file")
    
    try:
        output_dir = "access_amherst_algo/calendar_scraper/calendar_json_outputs"
        os.makedirs(output_dir, exist_ok=True)

        date_str = datetime.now().strftime("%Y-%m-%d")
        file_name = f"{output_dir}/events_{date_str}.json"

        if os.path.exists(file_name):
            logger.info(f"JSON file for today already exists: {file_name}. Skipping save.")
            return

        cleaned_events = [{k: v for k, v in event.items() if v is not None} for event in events]

        with open(file_name, "w", encoding="utf-8") as file:
            json.dump(cleaned_events, file, indent=4, ensure_ascii=False)

        logger.info(f"Events saved to {file_name}")

    except PermissionError as e:
        logger.error(f"Permission denied while saving JSON: {e}")
        raise