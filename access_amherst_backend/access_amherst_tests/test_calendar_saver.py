import pytest
import pytz
from unittest.mock import patch, mock_open, MagicMock
from datetime import datetime, timedelta
from django.utils import timezone
import json
import os
from access_amherst_algo.calendar_scraper.calendar_saver import (
    load_calendar_json,
    parse_calendar_datetime,
    is_calendar_event_similar,
    save_calendar_event_to_db,
    process_calendar_events,
)

# Sample test data
sample_calendar_event = {
    "title": "Test Calendar Event",
    "pub_date": "2024-11-07T14:00:00Z",
    "start_time": "2024-11-07T15:00:00Z",
    "end_time": "2024-11-07T16:00:00Z",
    "location": "Test Hall",
    "event_description": "Test description",
    "host": ["Test Host"],
    "link": "https://test.com",
    "picture_link": "https://test.com/image.jpg",
    "categories": ["Test Category"],
    "author_name": "Test Author",
}

# Sample list of events for testing
sample_calendar_events_list = [sample_calendar_event]


@pytest.fixture
def mock_event_queryset():
    """Create a mock queryset that simulates Django's queryset behavior."""
    mock_event = MagicMock()
    mock_event.title = "Test Calendar Event"

    mock_qs = MagicMock()
    mock_qs.all.return_value = mock_qs
    mock_qs.filter.return_value = [mock_event]

    return mock_qs


@pytest.fixture
def mock_event_model(mock_event_queryset):
    """Create a mock Event model with proper queryset behavior."""
    with patch(
        "access_amherst_algo.calendar_scraper.calendar_saver.Event"
    ) as mock_event:
        mock_event.objects = mock_event_queryset
        yield mock_event


def test_load_calendar_json_success():
    """Test successful loading of calendar JSON file."""
    with patch("os.listdir") as mock_listdir, \
         patch("builtins.open", mock_open(read_data=json.dumps(sample_calendar_events_list))):
        mock_listdir.return_value = ["events_20241107.json", "events_20241106.json"]
        result = load_calendar_json("test_folder")
        assert result == sample_calendar_events_list


def test_load_calendar_json_no_files():
    """Test behavior when no JSON files are present."""
    with patch("os.listdir") as mock_listdir:
        mock_listdir.return_value = []
        result = load_calendar_json("test_folder")
        assert result is None


def test_load_calendar_json_error():
    """Test error handling during JSON loading."""
    with patch("os.listdir", side_effect=Exception("File system error")):
        result = load_calendar_json("test_folder")
        assert result is None


def test_parse_calendar_datetime_with_timezone():
    """Test parsing datetime string with timezone information."""
    result = parse_calendar_datetime("2024-11-07T14:00:00Z")
    expected = datetime(2024, 11, 7, 14, 0, tzinfo=pytz.UTC)
    assert result == expected


def test_parse_calendar_datetime_without_timezone():
    """Test parsing datetime string without timezone (should assume EST)."""
    result = parse_calendar_datetime("2024-11-07 14:00:00")
    est = pytz.timezone("America/New_York")
    expected = est.localize(datetime(2024, 11, 7, 14, 0)).astimezone(pytz.UTC)
    assert result == expected


def test_parse_calendar_datetime_invalid():
    """Test parsing invalid datetime string."""
    result = parse_calendar_datetime("invalid-date")
    assert result is None


def test_parse_calendar_datetime_empty():
    """Test parsing empty datetime string."""
    result = parse_calendar_datetime("")
    assert result is None


def test_is_calendar_event_similar_true(mock_event_model):
    """Test detection of similar calendar events when one exists."""
    result = is_calendar_event_similar(sample_calendar_event)
    assert result is True
    mock_event_model.objects.filter.assert_called()


def test_is_calendar_event_similar_false(mock_event_model, mock_event_queryset):
    """Test detection of similar calendar events when none exist."""
    mock_event = MagicMock()
    mock_event.title = "Different Event"
    mock_event_queryset.filter.return_value = [mock_event]

    result = is_calendar_event_similar(sample_calendar_event)
    assert result is False


def test_is_calendar_event_similar_no_times():
    """Test similar event detection with missing time data."""
    event_no_times = sample_calendar_event.copy()
    del event_no_times["start_time"]
    del event_no_times["end_time"]
    
    with patch("access_amherst_algo.calendar_scraper.calendar_saver.Event") as mock_event:
        mock_event.objects.all.return_value = mock_event.objects
        mock_event.objects.filter.return_value = []
        
        result = is_calendar_event_similar(event_no_times)
        assert result is False


def test_is_calendar_event_similar_error(mock_event_model):
    """Test error handling in similar event detection."""
    mock_event_model.objects.all.side_effect = Exception("Database error")
    result = is_calendar_event_similar(sample_calendar_event)
    assert result is False


def test_save_calendar_event_to_db(mock_event_model):
    """Test saving calendar event to database."""
    save_calendar_event_to_db(sample_calendar_event)

    mock_event_model.objects.update_or_create.assert_called_once()
    call_args = mock_event_model.objects.update_or_create.call_args[1]

    assert "defaults" in call_args
    defaults = call_args["defaults"]
    assert defaults["title"] == sample_calendar_event["title"]
    assert defaults["location"] == sample_calendar_event["location"]
    assert json.loads(defaults["host"]) == sample_calendar_event["host"]
    assert json.loads(defaults["categories"]) == sample_calendar_event["categories"]


def test_save_calendar_event_to_db_missing_optional():
    """Test saving calendar event with missing optional fields."""
    event_data = sample_calendar_event.copy()
    del event_data["link"]
    del event_data["event_description"]

    with patch("access_amherst_algo.calendar_scraper.calendar_saver.Event") as mock_event:
        save_calendar_event_to_db(event_data)
        call_args = mock_event.objects.update_or_create.call_args[1]
        defaults = call_args["defaults"]

        assert defaults["link"] == "https://www.amherst.edu"
        assert defaults["event_description"] == ""


def test_save_calendar_event_to_db_error():
    """Test error handling when saving event fails."""
    with patch("access_amherst_algo.calendar_scraper.calendar_saver.Event") as mock_event:
        mock_event.objects.update_or_create.side_effect = Exception("Database error")
        
        with pytest.raises(Exception):
            save_calendar_event_to_db(sample_calendar_event)


@patch("access_amherst_algo.calendar_scraper.calendar_saver.load_calendar_json")
@patch("access_amherst_algo.calendar_scraper.calendar_saver.is_calendar_event_similar")
@patch("access_amherst_algo.calendar_scraper.calendar_saver.save_calendar_event_to_db")
def test_process_calendar_events_success(mock_save, mock_is_similar, mock_load):
    """Test successful processing of calendar events."""
    mock_load.return_value = sample_calendar_events_list
    mock_is_similar.return_value = False

    process_calendar_events()

    mock_load.assert_called_once()
    mock_is_similar.assert_called_once_with(sample_calendar_event)
    mock_save.assert_called_once_with(sample_calendar_event)


@patch("access_amherst_algo.calendar_scraper.calendar_saver.load_calendar_json")
def test_process_calendar_events_no_events(mock_load):
    """Test processing when no events are loaded."""
    mock_load.return_value = None
    process_calendar_events()
    mock_load.assert_called_once()


@patch("access_amherst_algo.calendar_scraper.calendar_saver.load_calendar_json")
@patch("access_amherst_algo.calendar_scraper.calendar_saver.is_calendar_event_similar")
@patch("access_amherst_algo.calendar_scraper.calendar_saver.save_calendar_event_to_db")
def test_process_calendar_events_error_handling(mock_save, mock_is_similar, mock_load):
    """Test error handling during event processing."""
    mock_load.return_value = sample_calendar_events_list
    mock_is_similar.return_value = False
    mock_save.side_effect = Exception("Test error")

    process_calendar_events()

    mock_load.assert_called_once()
    mock_is_similar.assert_called_once()
    mock_save.assert_called_once()