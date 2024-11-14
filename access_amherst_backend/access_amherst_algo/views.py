from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.management import call_command
from django.utils.timezone import localtime
from django.utils.dateparse import parse_date
from datetime import date, datetime, timedelta
import json
import pytz
from .parse_database import (
    filter_events,
    get_unique_locations,
    get_events_by_hour,
    get_category_data,
)
from .generate_map import create_map, add_event_markers, generate_heatmap
from .parse_database import filter_events_by_category, get_unique_categories
from .models import Event


def home(request):
    """Render home page with search, location, date, and category filters."""
    # Get query parameters
    query = request.GET.get("query", "")
    locations = request.GET.getlist("locations")
    categories = request.GET.getlist("categories")

    # Calculate default start and end dates for the next week
    today = date.today()
    default_start_date = today
    default_end_date = today + timedelta(days=7)

    # Use user-provided dates or default values
    start_date = parse_date(request.GET.get("start_date")) if request.GET.get("start_date") else default_start_date
    end_date = parse_date(request.GET.get("end_date")) if request.GET.get("end_date") else default_end_date

    # Filter events
    events = filter_events(
        query=query,
        locations=locations,
        start_date=start_date,
        end_date=end_date,
    )
    events = filter_events_by_category(events, categories).order_by("start_time")

    return render(
        request,
        "access_amherst_algo/home.html",
        {
            "events": events,
            "query": query,
            "selected_locations": locations,
            "selected_categories": categories,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "unique_locations": get_unique_locations(),
            "unique_categories": get_unique_categories(),
        },
    )


def map_view(request):
    """Render map view with event markers."""
    events = Event.objects.exclude(
        latitude__isnull=True, longitude__isnull=True
    )
    folium_map = create_map([42.37031303771378, -72.51605520950432])
    add_event_markers(folium_map, events)
    return render(
        request,
        "access_amherst_algo/map.html",
        {"map_html": folium_map._repr_html_()},
    )


def data_dashboard(request):
    """Render dashboard with event insights and heatmap."""
    est = pytz.timezone("America/New_York")

    events = Event.objects.all()

    context = {
        "events_by_hour": get_events_by_hour(events, est),
        "category_data": get_category_data(
            events.exclude(categories__isnull=True), est
        ),
        "map_html": generate_heatmap(
            events, est
        )._repr_html_(),  # Convert to HTML here
    }

    return render(request, "access_amherst_algo/dashboard.html", context)


@csrf_exempt
def update_heatmap(request):
    """Update heatmap based on selected time range from request."""
    if request.method == "POST":
        data = json.loads(request.body)
        est = pytz.timezone("America/New_York")

        folium_map = generate_heatmap(
            events=Event.objects.all(),
            timezone=est,
            min_hour=data.get("min_hour", 7),
            max_hour=data.get("max_hour", 22),
        )

        map_html = folium_map._repr_html_()  # Convert to HTML here
        return JsonResponse({"map_html": map_html})



def calendar_view(request):
    today = localtime().date()
    days_of_week = [(today + timedelta(days=i)) for i in range(7)]
    times = [datetime.strptime(f"{hour}:00", "%H:%M").time() for hour in range(5, 23)]

    start_date = days_of_week[0]
    end_date = days_of_week[-1]
    events = filter_events(start_date=start_date, end_date=end_date)

    events_by_day = {}
    for day in days_of_week:
        events_by_day[day.strftime('%Y-%m-%d')] = []
    
    # Group events by day and calculate overlaps
    for event in events:
        event_date = event.start_time.date()
        event_date_str = event_date.strftime('%Y-%m-%d')
        if event_date_str in events_by_day:
            event_obj = {
                "title": event.title,
                "location": event.location,
                "start_time": event.start_time,
                "end_time": event.end_time,
                "top": (event.start_time.hour - 7) * 60 + event.start_time.minute,
                "height": ((event.end_time.hour - event.start_time.hour) * 60 + 
                          (event.end_time.minute - event.start_time.minute)),
                "column": 0,  # Will be set during overlap detection
                "columns": 1  # Will be set during overlap detection
            }
            events_by_day[event_date_str].append(event_obj)

    # Calculate overlaps for each day
    for day, events in events_by_day.items():
        if not events:
            continue
            
        # Sort events by start time
        events.sort(key=lambda x: x['start_time'])
        
        # Find overlapping groups
        for i, event in enumerate(events):
            overlapping = []
            for other in events:
                if event != other and is_overlapping(event, other):
                    overlapping.append(other)
            
            if overlapping:
                # Calculate total columns needed
                max_columns = len(overlapping) + 1
                taken_columns = set()
                for e in overlapping:
                    if 'column' in e:
                        taken_columns.add(e['column'])
                
                # Find first available column
                for col in range(max_columns):
                    if col not in taken_columns:
                        event['column'] = col
                        break
                
                # Update columns count for all overlapping events
                event['columns'] = max_columns
                for e in overlapping:
                    e['columns'] = max_columns

    return render(
        request,
        "access_amherst_algo/calendar.html",
        {
            "days_of_week": days_of_week,
            "times": times,
            "events_by_day": events_by_day,
        },
    )


def is_overlapping(event1, event2):
    return not (event1['end_time'] <= event2['start_time'] or 
               event2['end_time'] <= event1['start_time'])