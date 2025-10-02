# FILE: tests/test_database.py
import pytest
from app.database import DatabaseManager, get_database, reset_database

@pytest.fixture
def db():
    """Fixture to provide an in-memory database for testing."""
    # Use the singleton getter with a specific path for an in-memory db
    db_instance = get_database(db_path=":memory:")
    yield db_instance
    # Reset the singleton after the test
    reset_database()

def test_initialization(db: DatabaseManager):
    """Tests that the database and tables are created on initialization."""
    with db.get_cursor() as cursor:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='urls'")
        assert cursor.fetchone() is not None
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='url_checks'")
        assert cursor.fetchone() is not None

def test_add_and_get_url(db: DatabaseManager):
    """Tests adding a URL and retrieving it."""
    url_to_add = "https://example.com"
    url_id = db.add_url(url_to_add, name="Example", timeout=15)
    
    assert url_id is not None
    
    retrieved_url = db.get_url(url_id)
    assert retrieved_url.id == url_id
    assert retrieved_url.url == url_to_add
    assert retrieved_url.name == "Example"
    assert retrieved_url.timeout == 15
    assert retrieved_url.is_active is True

def test_prevent_duplicate_urls(db: DatabaseManager):
    """Tests that adding a duplicate URL is prevented."""
    url_to_add = "https://unique-url.com"
    first_id = db.add_url(url_to_add)
    second_id = db.add_url(url_to_add)
    
    assert first_id is not None
    assert second_id is None

def test_list_urls(db: DatabaseManager):
    """Tests listing all URLs, including active-only filtering."""
    db.add_url("https://site1.com", active=True)
    db.add_url("https://site2.com", active=True)
    db.add_url("https://site3.com", active=False)
    
    all_urls = db.list_urls()
    active_urls = db.list_urls(active_only=True)
    
    assert len(all_urls) == 3
    assert len(active_urls) == 2
    assert all(url.is_active for url in active_urls)

def test_delete_url(db: DatabaseManager):
    """Tests that deleting a URL also removes its check history."""
    url_id = db.add_url("https://todelete.com")
    assert url_id is not None
    
    # Add some check history
    db.save_check_result(url_id, 200, 150.5, True)
    
    # Verify history exists
    history = db.get_url_history(url_id)
    assert len(history) == 1
    
    # Delete the URL
    success = db.delete_url(url_id)
    assert success is True
    
    # Verify URL is gone
    assert db.get_url(url_id) is None
    
    # Verify history is also gone (due to ON DELETE CASCADE)
    with db.get_cursor() as cursor:
        cursor.execute("SELECT * FROM url_checks WHERE url_id = ?", (url_id,))
        assert cursor.fetchone() is None

def test_save_and_get_status(db: DatabaseManager):
    """Tests saving a check result and retrieving the latest status."""
    url_id = db.add_url("https://status-check.com")
    assert url_id is not None
    
    db.save_check_result(url_id, 200, 123.45, True, None)
    db.save_check_result(url_id, 500, 5000.1, False, "Server Error")
    
    status = db.get_url_status(url_id)
    assert status['is_up'] is False
    assert status['status_code'] == 500
    assert status['response_time'] == 5000.1
    assert status['error_message'] == "Server Error"