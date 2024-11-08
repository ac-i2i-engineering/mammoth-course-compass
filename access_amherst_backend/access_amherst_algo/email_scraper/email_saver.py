from datetime import datetime, timedelta
from django.utils import timezone
import json
import os
import difflib
from access_amherst_algo.models import Event
from django.db.models import Q

def load_json_file(folder_path):
    """
    Load the most recent JSON file from the specified folder
    """
    try:
        json_files = [f for f in os.listdir(folder_path) if f.endswith('.json')]
        if not json_files:
            print("No JSON files found in the specified directory")
            return None
        
        latest_file = sorted(json_files)[-1]
        file_path = os.path.join(folder_path, latest_file)
        
        with open(file_path, 'r') as file:
            return json.load(file)
    except Exception as e:
        print(f"Error loading JSON file: {e}")
        return None

def parse_datetime(date_str, pub_date=None):
    """
    Parse different datetime formats and return timezone-aware datetime object
    Now handles time-only strings by combining them with pub_date
    """
    if not date_str:
        return None
        
    try:
        # First try parsing as full datetime
        formats = [
            '%Y-%m-%d',  # YYYY-MM-DD
            '%Y-%m-%dT%H:%M:%S',  # ISO format
            '%a, %d %b %Y %H:%M:%S %Z'  # RFC format
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return timezone.make_aware(dt)
            except ValueError:
                continue

        # If that fails, try parsing as time only
        try:
            # Parse time-only format
            time = datetime.strptime(date_str, '%H:%M:%S').time()
            
            # If we have a pub_date, use it as the base date
            if pub_date:
                if isinstance(pub_date, str):
                    pub_date = parse_datetime(pub_date)
                    
                if pub_date:
                    # Combine the date from pub_date with the time
                    dt = datetime.combine(pub_date.date(), time)
                    return timezone.make_aware(dt)
            
            # If no pub_date, use current date
            dt = datetime.combine(timezone.now().date(), time)
            return timezone.make_aware(dt)
            
        except ValueError:
            raise ValueError(f"Unable to parse date string: {date_str}")
            
    except Exception as e:
        print(f"Error parsing date: {e}")
        return None

def is_similar_event(event_data):
    """
    Check if a similar event already exists in the database, considering start and end times only if they are present.
    """
    try:
        pub_date = parse_datetime(event_data.get('pub_date'))
        start_time = parse_datetime(event_data.get('starttime'), pub_date)
        end_time = parse_datetime(event_data.get('endtime'), pub_date)

        # Start with filtering only by title similarity if times are missing
        similar_events = Event.objects.all()

        # If start_time and end_time are provided, filter events by these times
        if start_time and end_time:
            similar_events = similar_events.filter(
                Q(start_time=start_time) & Q(end_time=end_time)
            )
        
        # Check title similarity
        for event in similar_events:
            title_similarity = difflib.SequenceMatcher(None, event_data['title'], event.title).ratio()
            if title_similarity > 0.8:
                return True
        
        return False
    except Exception as e:
        print(f"Error checking for similar events: {e}")
        return False


def save_event_to_db(event_data):
    """
    Save an event to the database, allowing nullable start and end times.
    """
    try:
        # Generate a unique ID for email-sourced events
        event_id = str(600_000_000 + hash(str(event_data['title'])) % 100_000_000)
        
        # Parse dates
        pub_date = parse_datetime(event_data.get('pub_date')) or timezone.now()
        start_time = parse_datetime(event_data.get('starttime'), pub_date)
        end_time = parse_datetime(event_data.get('endtime'), pub_date)
        
        # Ensure 'link' and 'event_description' have default values
        link = event_data.get('link', 'https://www.amherst.edu')
        description = event_data.get('event_description', '')

        # Update or create the event
        Event.objects.update_or_create(
            id=event_id,
            defaults={
                "title": event_data['title'],
                "author_name": event_data.get('author_name', ''),
                "pub_date": pub_date,
                "host": json.dumps(event_data.get('host', [])),
                "link": link,
                "picture_link": event_data.get('picture_link', ''),
                "event_description": description,
                "start_time": start_time,
                "end_time": end_time,
                "location": event_data.get('location', 'TBD'),
                "categories": json.dumps(event_data.get('categories', [])),
                "latitude": None,
                "longitude": None,
                "map_location": "Other"
            }
        )
        print(f"Successfully saved/updated event: {event_data['title']}")
    except Exception as e:
        print(f"Error saving event to database: {e}")
        raise

# Process each event with updated logging
def process_email_events():
    """
    Main function to process email-sourced events with improved error handling.
    """
    # Get the current directory
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    json_folder = os.path.join(curr_dir, "json_outputs")
    
    # Load the JSON data
    events_data = load_json_file(json_folder)
    if not events_data:
        print("No events data to process")
        return
    
    # Process each event
    for event in events_data:
        try:
            if not is_similar_event(event):
                save_event_to_db(event)
            else:
                print(f"Skipping similar event: {event['title']}")
        except Exception as e:
            print(f"Error processing event '{event.get('title', 'Unknown')}': {e}")