import pytest
from unittest.mock import patch, mock_open
from datetime import datetime
import json
import os
import pytz
from access_amherst_algo.calendar_scraper.calendar_parser import (
    fetch_page,
    scrape_page,
    scrape_all_pages,
    save_to_json,
)

# Mock HTML content
mock_html_response = """
<html>
    <article class="mm-calendar-event">
        <h2 class="mm-event-listing-title">
            <a href="https://example.com/event1">Event Title 1</a>
        </h2>
        <h3 class="mm-calendar-period">
            <meta itemprop="startDate" content="2024-11-20T10:00:00">
            <meta itemprop="endDate" content="2024-11-20T12:00:00">
        </h3>
        <p class="mm-event-listing-location">Main Hall</p>
        <div class="mm-event-listing-description">Sample description</div>
        <img itemprop="image" src="https://example.com/image1.jpg" />
    </article>
</html>
"""

mock_events = [
    {
        "title": "Event Title 1",
        "link": "https://example.com/event1",
        "start_time": "2024-11-20T10:00:00",
        "end_time": "2024-11-20T12:00:00",
        "location": "Main Hall",
        "event_description": "Sample description",
        "picture_link": "https://example.com/image1.jpg",
    }
]


def test_fetch_page_success(requests_mock):
    """Test fetch_page with a successful response."""
    url = "https://www.amherst.edu/news/events/calendar"
    requests_mock.get(url, text=mock_html_response, status_code=200)

    content = fetch_page(url)
    assert content is not None
    assert "Event Title 1" in content.decode("utf-8")


def test_fetch_page_failure(requests_mock):
    """Test fetch_page with a failed response."""
    url = "https://www.amherst.edu/news/events/calendar"
    requests_mock.get(url, status_code=404)

    content = fetch_page(url)
    assert content is None


def test_scrape_page_success(requests_mock):
    """Test scrape_page with valid HTML content."""
    url = "https://www.amherst.edu/news/events/calendar"
    requests_mock.get(url, text=mock_html_response, status_code=200)

    events = scrape_page(url)
    assert len(events) == 1
    assert events[0]["title"] == "Event Title 1"
    assert events[0]["location"] == "Main Hall"
    assert events[0]["start_time"] == "2024-11-20T10:00:00"


def test_scrape_page_no_events():
    """Test scrape_page with no event content."""
    no_event_html = "<html><body>No events here</body></html>"
    with patch(
        "access_amherst_algo.calendar_scraper.calendar_parser.fetch_page",
        return_value=no_event_html,
    ):
        events = scrape_page("https://www.amherst.edu/news/events/calendar")
        assert len(events) == 0


def test_scrape_all_pages(requests_mock):
    """Test scrape_all_pages with multiple pages."""
    page1_url = "https://www.amherst.edu/news/events/calendar?_page=0"
    page2_url = "https://www.amherst.edu/news/events/calendar?_page=1"
    requests_mock.get(page1_url, text=mock_html_response, status_code=200)
    requests_mock.get(page2_url, text="<html><body>No events here</body></html>", status_code=200)

    with patch("access_amherst_algo.calendar_scraper.calendar_parser.scrape_page", side_effect=[mock_events, []]):
        events = scrape_all_pages()
        assert len(events) == 1
        assert events[0]["title"] == "Event Title 1"


@patch("access_amherst_algo.calendar_scraper.calendar_parser.open", new_callable=mock_open)
@patch("access_amherst_algo.calendar_scraper.calendar_parser.os.makedirs")
def test_save_to_json(mock_makedirs, mock_open_file):
    """Test save_to_json function."""
    output_dir = "access_amherst_algo/calendar_scraper/calendar_json_outputs"
    
    # Call os.makedirs in the test setup
    os.makedirs(output_dir, exist_ok=True)
    
    # Reset the mock to avoid interference from the setup call
    mock_makedirs.reset_mock()

    date_str = datetime.now().strftime("%Y-%m-%d")
    file_path = os.path.join(output_dir, f"events_{date_str}.json")

    # Call the actual function
    save_to_json(mock_events)

    # Verify that makedirs was called only once within save_to_json
    mock_makedirs.assert_called_once_with(output_dir, exist_ok=True)

    # Verify file opening and writing
    mock_open_file.assert_called_once_with(file_path, "w", encoding="utf-8")
    handle = mock_open_file()
    written_content = "".join(call.args[0] for call in handle.write.call_args_list)
    assert json.loads(written_content) == mock_events