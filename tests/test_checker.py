# FILE: tests/test_checker.py
import pytest
import requests
import requests_mock
from app.checker import check_single_url
from app.database import URLRecord
from datetime import datetime

# A dummy URLRecord for use in tests
@pytest.fixture
def mock_url_record():
    return URLRecord(
        id=1,
        url="https://test.com",
        name="Test Site",
        timeout=5,
        is_active=True,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        last_checked=None
    )

def test_check_successful_url(mock_url_record: URLRecord):
    """Tests a successful check for a URL that is up (200 OK)."""
    with requests_mock.Mocker() as m:
        m.get(mock_url_record.url, text="OK", status_code=200)
        
        result = check_single_url(mock_url_record)
        
        assert result['url_id'] == mock_url_record.id
        assert result['is_up'] is True
        assert result['status_code'] == 200
        assert result['error_message'] is None
        assert result['response_time'] is not None

def test_check_failed_url(mock_url_record: URLRecord):
    """Tests a check for a URL that is down (503 Service Unavailable)."""
    with requests_mock.Mocker() as m:
        m.get(mock_url_record.url, status_code=503)
        
        result = check_single_url(mock_url_record)
        
        assert result['is_up'] is False
        assert result['status_code'] == 503
        assert "HTTP Status 503" in result['error_message']

def test_check_url_timeout(mock_url_record: URLRecord):
    """Tests a check that results in a connection timeout."""
    with requests_mock.Mocker() as m:
        m.get(mock_url_record.url, exc=requests.exceptions.Timeout)
        
        result = check_single_url(mock_url_record)
        
        assert result['is_up'] is False
        assert result['status_code'] is None
        assert "Request timed out" in result['error_message']

def test_check_connection_error(mock_url_record: URLRecord):
    """Tests a check that results in a generic connection error."""
    with requests_mock.Mocker() as m:
        m.get(mock_url_record.url, exc=requests.exceptions.ConnectionError)
        
        result = check_single_url(mock_url_record)
        
        assert result['is_up'] is False
        assert "Connection error: ConnectionError" in result['error_message']