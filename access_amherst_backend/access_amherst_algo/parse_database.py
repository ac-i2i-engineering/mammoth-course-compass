from django.db.models import Count
from django.db.models.functions import ExtractHour
from .models import Event
from datetime import datetime, time
import pytz
import re


def filter_events(query="", locations=None, start_date=None, end_date=None):
    """Filter events based on query, location, and date range."""
    events = Event.objects.all()

    if query:
        events = events.filter(title__icontains=query)

    if locations:
        events = events.filter(map_location__in=locations)

    if start_date and end_date:
        events = events.filter(start_time__date__range=[start_date, end_date])

    return events.distinct()


def get_unique_locations():
    """Retrieve distinct event locations for filtering."""
    return Event.objects.values_list("map_location", flat=True).distinct()


def get_events_by_hour(events, timezone):
    """Group events by the hour and adjust to specified timezone."""
    events_by_hour = (
        events.exclude(
            start_time__isnull=True
        )  # Exclude events with null start_time
        .annotate(hour=ExtractHour("start_time"))
        .values("hour")
        .annotate(event_count=Count("id"))
        .order_by("hour")
    )

    # Convert to local time
    for event in events_by_hour:
        if event["hour"] is not None:  # Handle None values
            start_time_utc = datetime.combine(
                datetime.now(), time(event["hour"])
            ).replace(tzinfo=pytz.utc)
            event["hour"] = start_time_utc.astimezone(timezone).hour
        else:
            event["hour"] = (
                None  # Optionally, you can log or handle this differently
            )

    return events_by_hour


def get_category_data(events, timezone):
    """Parse and clean category data for events, grouping by hour."""
    category_data = []

    # Filter out events with null start_time
    events = events.exclude(start_time__isnull=True)

    for event in events:
        if event.start_time:  # Ensure start_time is not None
            hour = event.start_time.astimezone(timezone).hour
            categories = event.categories.strip('[]"').split(",")

            for category in categories:
                cleaned_category = re.sub(
                    r"[^a-z0-9]+", " ", category.strip().lower()
                ).strip()
                category_data.append(
                    {"category": cleaned_category, "hour": hour}
                )
        else:
            # Optionally log or handle events with missing start_time
            pass

    return category_data
