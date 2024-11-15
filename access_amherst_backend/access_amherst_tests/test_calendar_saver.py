import pytest
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime
import pytz
import json
from access_amherst_algo.calendar_scraper.calendar_saver import (
    load_calendar_json,
    parse_calendar_datetime,
    is_calendar_event_similar,
    save_calendar_event_to_db,
    process_calendar_events,
)
from access_amherst_algo.models import Event


# Mock data for testing
mock_event_data = {
    "title": "Sample Event",
    "pub_date": "2024-11-15",
    "start_time": "2024-11-15T10:00:00",
    "end_time": "2024-11-15T12:00:00",
    "location": "Main Hall",
    "event_description": "Sample description",
    "host": ["Sample Host"],
    "link": "https://sample.com",
    "picture_link": "https://sample.com/image.jpg",
    "categories": ["Category 1"],
    "author_name": "John Doe",
    "author_email": "john.doe@example.com",
}

mock_events_list = [mock_event_data]


def test_load_calendar_json(tmpdir):
    """Test loading JSON from a folder."""
    json_folder = tmpdir.mkdir("calendar_json_outputs")
    json_file = json_folder.join("events.json")
    json_file.write(json.dumps(mock_events_list))

    with patch("access_amherst_algo.calendar_scraper.calendar_saver.os.listdir", return_value=["events.json"]):
        data = load_calendar_json(str(json_folder))
        assert data == mock_events_list


def test_load_calendar_json_no_files(tmpdir):
    """Test loading JSON when no files are present."""
    empty_folder = tmpdir.mkdir("empty_folder")
    with patch("access_amherst_algo.calendar_scraper.calendar_saver.os.listdir", return_value=[]):
        data = load_calendar_json(str(empty_folder))
        assert data is None


def test_parse_calendar_datetime():
    """Test parsing and converting datetime strings."""
    date_str = "2024-11-15T10:00:00"
    parsed_dt = parse_calendar_datetime(date_str)
    expected_dt = datetime(2024, 11, 15, 15, 0, tzinfo=pytz.UTC)
    assert parsed_dt == expected_dt


def test_parse_calendar_datetime_with_invalid_date():
    """Test parsing an invalid datetime string."""
    invalid_date = "invalid-date"
    parsed_dt = parse_calendar_datetime(invalid_date)
    assert parsed_dt is None


@pytest.mark.django_db
def test_is_calendar_event_similar(mocker):
    """Test checking for similar events."""
    mock_event = Event(
        title="Sample Event",
        start_time=datetime(2024, 11, 15, 10, 0, tzinfo=pytz.UTC),
        end_time=datetime(2024, 11, 15, 12, 0, tzinfo=pytz.UTC),
    )

    # Create a mock QuerySet
    mock_queryset = MagicMock()
    mock_queryset.filter.return_value = [mock_event]

    # Mock Event.objects.all() to return the mock QuerySet
    mocker.patch("access_amherst_algo.calendar_scraper.calendar_saver.Event.objects.all", return_value=mock_queryset)

    similar = is_calendar_event_similar(mock_event_data)
    assert similar is True


@pytest.mark.django_db
def test_is_calendar_event_similar_no_match(mocker):
    """Test when no similar events are found."""
    mocker.patch("access_amherst_algo.calendar_scraper.calendar_saver.Event.objects.all", return_value=[])

    similar = is_calendar_event_similar(mock_event_data)
    assert similar is False


@pytest.mark.django_db
def test_save_calendar_event_to_db(mocker):
    """Test saving an event to the database."""
    mock_update_or_create = mocker.patch("access_amherst_algo.calendar_scraper.calendar_saver.Event.objects.update_or_create")
    
    save_calendar_event_to_db(mock_event_data)
    
    mock_update_or_create.assert_called_once()
    call_args = mock_update_or_create.call_args[1]
    assert call_args["defaults"]["title"] == mock_event_data["title"]
    assert call_args["defaults"]["location"] == mock_event_data["location"]


def test_process_calendar_events(tmpdir, mocker):
    """Test the main event processing function."""
    # Mock JSON loading
    json_folder = tmpdir.mkdir("calendar_json_outputs")
    json_file = json_folder.join("events.json")
    json_file.write(json.dumps(mock_events_list))
    
    mocker.patch("access_amherst_algo.calendar_scraper.calendar_saver.load_calendar_json", return_value=mock_events_list)

    # Mock similar event checking
    mocker.patch("access_amherst_algo.calendar_scraper.calendar_saver.is_calendar_event_similar", return_value=False)

    # Mock saving to the database
    mock_save_event = mocker.patch("access_amherst_algo.calendar_scraper.calendar_saver.save_calendar_event_to_db")

    # Run the function
    process_calendar_events()

    # Ensure saving was called
    mock_save_event.assert_called_once_with(mock_event_data)


def test_process_calendar_events_no_data(mocker):
    """Test processing with no events data."""
    mocker.patch("access_amherst_algo.calendar_scraper.calendar_saver.load_calendar_json", return_value=None)

    process_calendar_events()

    # No events should be saved
    assert True  # No exceptions mean the test passed