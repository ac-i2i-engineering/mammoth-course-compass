from datetime import datetime
from django.utils import timezone
from dateutil import parser
import json
import os
import difflib
import logging
from access_amherst_algo.models import Event
from django.db.models import Q
import pytz
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("calendar_events_processing.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_calendar_json(folder_path):
    """
    Load the most recent JSON file from the specified folder.
    """
    try:
        json_files = [
            f for f in os.listdir(folder_path) if f.endswith(".json")
        ]
        if not json_files:
            logger.warning("No JSON files found in the specified directory")
            return None

        latest_file = sorted(json_files)[-1]
        file_path = os.path.join(folder_path, latest_file)
        logger.info(f"Loading JSON file: {file_path}")

        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception as e:
        logger.error(f"Error loading JSON file: {e}")
        return None


def parse_calendar_datetime(date_str, pub_date=None):
    """
    Parse datetime strings and convert to UTC. Assumes ISO 8601 as primary format.
    """
    if not date_str:
        return None

    try:
        dt = parser.parse(date_str)

        if dt.tzinfo is None:
            dt = pytz.timezone("America/New_York").localize(dt)
        
        return dt.astimezone(pytz.UTC)
    except parser.ParserError as e:
        logger.warning(f"Error parsing date string '{date_str}': {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error parsing date '{date_str}': {e}")
        return None


def is_calendar_event_similar(event_data):
    """
    Check if a similar event exists using cosine similarity of titles.
    """
    try:
        pub_date = parse_calendar_datetime(event_data.get("pub_date"))
        start_time = parse_calendar_datetime(event_data.get("start_time"), pub_date)
        end_time = parse_calendar_datetime(event_data.get("end_time"), pub_date)

        query = Q()
        if start_time:
            query &= Q(start_time=start_time)
        if end_time:
            query &= Q(end_time=end_time)

        # Convert QuerySet to list early to avoid indexing issues
        similar_events = list(Event.objects.all())
        if query:
            similar_events = [event for event in similar_events if event in Event.objects.filter(query)]
        
        # Get all event titles
        existing_titles = [event.title for event in similar_events]
        new_title = event_data.get("title", "")
        
        if not existing_titles:
            return False
            
        # Create TF-IDF vectors
        vectorizer = TfidfVectorizer()
        all_titles = existing_titles + [new_title]
        tfidf_matrix = vectorizer.fit_transform(all_titles)
        
        # Calculate cosine similarity between new title and existing titles
        new_title_vector = tfidf_matrix[-1:]
        existing_titles_matrix = tfidf_matrix[:-1]
        similarities = cosine_similarity(new_title_vector, existing_titles_matrix)[0]
        
        # Check if any similarity exceeds threshold
        if len(similarities) > 0 and np.max(similarities) > 0.6:
            similar_index = int(np.argmax(similarities))  # Convert to standard Python int
            most_similar_event = similar_events[similar_index]
            logger.info(f"Found similar event: {most_similar_event.title}")
            return True

        return False

    except Exception as e:
        logger.error(f"Error checking for similar events: {e}")
        return False


def save_calendar_event_to_db(event_data):
    """
    Save a calendar event to the database, allowing nullable fields.
    """
    try:
        event_id = str(
            700_000_000 + hash(str(event_data["title"])) % 100_000_000
        )

        pub_date = parse_calendar_datetime(event_data.get("pub_date")) or timezone.now()
        start_time = parse_calendar_datetime(event_data.get("start_time"), pub_date)
        end_time = parse_calendar_datetime(event_data.get("end_time"), pub_date)

        link = event_data.get("link", "https://www.amherst.edu")
        description = event_data.get("event_description", "")

        Event.objects.update_or_create(
            id=event_id,
            defaults={
                "title": event_data["title"],
                "author_name": event_data.get("author_name", ""),
                "pub_date": pub_date,
                "host": json.dumps(event_data.get("host", [])),
                "link": link,
                "picture_link": event_data.get("picture_link", ""),
                "event_description": description,
                "start_time": start_time,
                "end_time": end_time,
                "location": event_data.get("location", "TBD"),
                "categories": json.dumps(event_data.get("categories", [])),
                "latitude": None,
                "longitude": None,
                "map_location": "Other",
            },
        )
        logger.info(f"Successfully saved event: {event_data['title']}")
        
    except Exception as e:
        logger.error(f"Error saving event '{event_data.get('title', 'Unknown')}': {e}")
        raise


def process_calendar_events():
    """
    Main function to process calendar-sourced events with improved error handling.
    """
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    json_folder = os.path.join(curr_dir, "calendar_json_outputs")

    events_data = load_calendar_json(json_folder)
    if not events_data:
        logger.warning("No events data to process")
        return

    for event in events_data:
        try:
            if not is_calendar_event_similar(event):
                save_calendar_event_to_db(event)
            else:
                logger.info(f"Skipping similar event: {event['title']}")
        except Exception as e:
            logger.error(
                f"Error processing event '{event.get('title', 'Unknown')}': {e}"
            )