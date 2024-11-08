import pytest
from unittest.mock import patch, mock_open, MagicMock
from datetime import datetime
from django.utils import timezone
import json
import os
from access_amherst_algo.email_scraper.email_saver import (
    load_json_file,
    parse_datetime,
    is_similar_event,
    save_event_to_db,
    process_email_events
)

# Sample test data
sample_event = {
    "title": "Test Event",
    "pub_date": "2024-11-07",
    "starttime": "09:00:00",
    "endtime": "10:00:00",
    "location": "Test Hall",
    "event_description": "Test description",
    "host": ["Test Host"],
    "link": "https://test.com",
    "picture_link": "https://test.com/image.jpg",
    "categories": ["Test Category"],
    "author_name": "Test Author",
    "author_email": "test@example.com"
}

# Sample list of events for testing
sample_events_list = [sample_event]

@pytest.fixture
def mock_event_queryset():
    """Create a mock queryset that simulates Django's queryset behavior."""
    mock_event = MagicMock()
    mock_event.title = "Test Event"
    
    mock_qs = MagicMock()
    mock_qs.all.return_value = mock_qs
    mock_qs.filter.return_value = [mock_event]  # Return list with our mock event
    
    return mock_qs

@pytest.fixture
def mock_event_model(mock_event_queryset):
    """Create a mock Event model with proper queryset behavior."""
    with patch('access_amherst_algo.email_scraper.email_saver.Event') as mock_event:
        mock_event.objects = mock_event_queryset
        yield mock_event

def test_is_similar_event_true(mock_event_model):
    """Test detection of similar events when one exists."""
    result = is_similar_event(sample_event)
    
    # Verify the queryset was filtered correctly
    mock_event_model.objects.filter.assert_called()
    
    # Verify we got True as the result
    assert result is True

def test_is_similar_event_false(mock_event_model, mock_event_queryset):
    """Test detection of similar events when none exist."""
    # Create a mock event with different title
    mock_event = MagicMock()
    mock_event.title = "Completely Different Event"
    mock_event_queryset.filter.return_value = [mock_event]
    
    result = is_similar_event(sample_event)
    assert result is False

def test_is_similar_event_no_times(mock_event_model, mock_event_queryset):
    """Test similar event detection with missing time data."""
    event_no_times = sample_event.copy()
    del event_no_times['starttime']
    del event_no_times['endtime']
    
    mock_event = MagicMock()
    mock_event.title = "Test Event"
    mock_event_queryset.all.return_value = [mock_event]
    
    result = is_similar_event(event_no_times)
    assert result is True

def test_is_similar_event_error(mock_event_model):
    """Test error handling in similar event detection."""
    mock_event_model.objects.all.side_effect = Exception("Database error")
    
    result = is_similar_event(sample_event)
    assert result is False

def test_save_event_to_db(mock_event_model):
    """Test saving event to database."""
    save_event_to_db(sample_event)
    
    mock_event_model.objects.update_or_create.assert_called_once()
    call_args = mock_event_model.objects.update_or_create.call_args[1]
    
    assert 'defaults' in call_args
    defaults = call_args['defaults']
    assert defaults['title'] == sample_event['title']
    assert defaults['location'] == sample_event['location']
    assert json.loads(defaults['host']) == sample_event['host']
    assert json.loads(defaults['categories']) == sample_event['categories']

@patch('access_amherst_algo.email_scraper.email_saver.load_json_file')
@patch('access_amherst_algo.email_scraper.email_saver.is_similar_event')
@patch('access_amherst_algo.email_scraper.email_saver.save_event_to_db')
def test_process_email_events_success(mock_save, mock_is_similar, mock_load):
    """Test successful processing of email events."""
    # Setup mocks
    mock_load.return_value = sample_events_list
    mock_is_similar.return_value = False
    
    # Run the function
    process_email_events()
    
    # Verify calls
    mock_load.assert_called_once()
    mock_is_similar.assert_called_once_with(sample_event)
    mock_save.assert_called_once_with(sample_event)

@patch('access_amherst_algo.email_scraper.email_saver.load_json_file')
@patch('access_amherst_algo.email_scraper.email_saver.is_similar_event')
@patch('access_amherst_algo.email_scraper.email_saver.save_event_to_db')
def test_process_email_events_error_handling(mock_save, mock_is_similar, mock_load):
    """Test error handling during event processing."""
    mock_load.return_value = sample_events_list
    mock_is_similar.return_value = False
    mock_save.side_effect = Exception("Test error")
    
    # This should not raise an exception
    process_email_events()
    
    mock_load.assert_called_once()
    mock_is_similar.assert_called_once()
    mock_save.assert_called_once()

@patch('access_amherst_algo.email_scraper.email_saver.load_json_file')
@patch('access_amherst_algo.email_scraper.email_saver.is_similar_event')
@patch('access_amherst_algo.email_scraper.email_saver.save_event_to_db')
def test_process_email_events_error_handling(mock_save, mock_is_similar, mock_load):
    """Test error handling during event processing."""
    mock_load.return_value = sample_events_list
    mock_is_similar.return_value = False
    mock_save.side_effect = Exception("Test error")
    
    # This should not raise an exception
    process_email_events()
    
    mock_load.assert_called_once()
    mock_is_similar.assert_called_once()
    mock_save.assert_called_once()

if __name__ == '__main__':
    pytest.main()