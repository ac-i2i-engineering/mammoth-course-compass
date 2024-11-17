import requests
import json
import os
import logging
from bs4 import BeautifulSoup
from datetime import datetime
import random
import re

BASE_URL = "https://www.amherst.edu/news/events/calendar"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Referer": "https://www.amherst.edu/",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
}

# Define location buckets with keywords as keys and dictionaries containing full names, latitude, and longitude as values
location_buckets = {
    "Keefe": {
        "name": "Keefe Campus Center",
        "latitude": 42.37141504481807,
        "longitude": -72.51479991450528,
    },
    "Queer": {
        "name": "Keefe Campus Center",
        "latitude": 42.37141504481807,
        "longitude": -72.51479991450528,
    },
    "Multicultural": {
        "name": "Keefe Campus Center",
        "latitude": 42.37141504481807,
        "longitude": -72.51479991450528,
    },
    "Friedmann": {
        "name": "Keefe Campus Center",
        "latitude": 42.37141504481807,
        "longitude": -72.51479991450528,
    },
    "Ford": {
        "name": "Ford Hall",
        "latitude": 42.36923506234738,
        "longitude": -72.51529130962976,
    },
    "SCCE": {
        "name": "Science Center",
        "latitude": 42.37105378715133,
        "longitude": -72.51334790776447,
    },
    "Science Center": {
        "name": "Science Center",
        "latitude": 42.37105378715133,
        "longitude": -72.51334790776447,
    },
    "Chapin": {
        "name": "Chapin Hall",
        "latitude": 42.371771820543486,
        "longitude": -72.51572746604714,
    },
    "Gym": {
        "name": "Alumni Gymnasium",
        "latitude": 42.368819594097864,
        "longitude": -72.5188658145099,
    },
    "Cage": {
        "name": "Alumni Gymnasium",
        "latitude": 42.368819594097864,
        "longitude": -72.5188658145099,
    },
    "Lefrak": {
        "name": "Alumni Gymnasium",
        "latitude": 42.368819594097864,
        "longitude": -72.5188658145099,
    },
    "Middleton Gym": {
        "name": "Alumni Gym",
        "latitude": 42.368819594097864,
        "longitude": -72.5188658145099,
    },
    "Frost": {
        "name": "Frost Library",
        "latitude": 42.37183195277655,
        "longitude": -72.51699336789369,
    },
    "Paino": {
        "name": "Beneski Museum of Natural History",
        "latitude": 42.37209277500926,
        "longitude": -72.51422459549485,
    },
    "Powerhouse": {
        "name": "Powerhouse",
        "latitude": 42.372109655195466,
        "longitude": -72.51309270030836,
    },
    "Converse": {
        "name": "Converse Hall",
        "latitude": 42.37243680844771,
        "longitude": -72.518433147017,
    },
    "Assembly Room": {
        "name": "Converse Hall",
        "latitude": 42.37243680844771,
        "longitude": -72.518433147017,
    },
    "Red Room": {
        "name": "Converse Hall",
        "latitude": 42.37243680844771,
        "longitude": -72.518433147017,
    },
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

def categorize_location(location):
    """
    Categorize a location based on keywords in the location_buckets dictionary.
    Returns the full location name if matched, otherwise returns "Other".
    """
    for keyword, info in location_buckets.items():
        if re.search(rf"\b{keyword}\b", location, re.IGNORECASE):
            return info["name"]
    return "Other"

def get_lat_lng(location):
    """
    Get the latitude and longitude for a location based on the location_buckets dictionary.
    """
    for keyword, info in location_buckets.items():
        if re.search(rf"\b{keyword}\b", location, re.IGNORECASE):
            return info["latitude"], info["longitude"]
    return None, None

def add_random_offset(lat, lng):
    """
    Add a small random offset to latitude and longitude coordinates.
    """
    offset_range = 0.00015
    lat += random.uniform(-offset_range, offset_range)
    lng += random.uniform(-offset_range, offset_range)
    return lat, lng

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
                "location": None,
                "categories": None,
                "map_location": None,
                "latitude": None,
                "longitude": None
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
                location = location_tag.get_text(strip=True)
                event["location"] = location
                # Add map location categorization
                event["map_location"] = categorize_location(location)

                # Add latitude and longitude
                lat, lng = get_lat_lng(location)
                if lat is not None and lng is not None:
                    lat, lng = add_random_offset(lat, lng)
                    event["latitude"] = lat
                    event["longitude"] = lng

            description_tag = article.find("div", class_="mm-event-listing-description")
            if description_tag:
                event["event_description"] = description_tag.get_text(strip=True)

            picture_tag = article.find("img", itemprop="image")
            if picture_tag and "src" in picture_tag.attrs:
                event["picture_link"] = picture_tag["src"]

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