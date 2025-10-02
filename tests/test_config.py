# FILE: tests/test_config.py
import os
import json
import pytest
from app.config import Config

@pytest.fixture
def temp_config_file(tmp_path):
    config_data = {"test_key": "test_value", "nested": {"key": "nested_value"}}
    config_file = tmp_path / "test_config.json"
    with open(config_file, 'w') as f:
        json.dump(config_data, f)
    return str(config_file)

def test_load_from_file(temp_config_file):
    """Tests that configuration is loaded correctly from a file."""
    config = Config(config_file=temp_config_file)
    assert config.get('test_key') == 'test_value'
    assert config.get('nested.key') == 'nested_value'

def test_default_config_creation():
    """Tests that a default config is created if no file exists."""
    config = Config(config_file='non_existent_file.json')
    assert config.get('application.name') == 'URL Monitor'
    assert isinstance(config.get('scheduler.schedules'), list)

def test_get_value():
    """Tests retrieving values using dot notation."""
    config = Config() # Uses default
    assert config.get('dashboard.port') == 8080
    assert config.get('non.existent.key', 'default') == 'default'

def test_set_value():
    """Tests setting values using dot notation."""
    config = Config()
    config.set('database.path', '/new/path/test.db')
    assert config.get('database.path') == '/new/path/test.db'
    config.set('new.nested.key', 'new_value')
    assert config.get('new.nested.key') == 'new_value'

def test_env_variable_override():
    """Tests that environment variables correctly override defaults."""
    os.environ['MONITOR_PORT'] = '9999'
    os.environ['MONITOR_TIMEOUT'] = '25'
    
    # We must instantiate a new Config object to read the new env vars
    config = Config() 
    
    assert config.get('dashboard.port') == 9999
    assert config.get('checker.request_timeout') == 25
    
    # Cleanup
    del os.environ['MONITOR_PORT']
    del os.environ['MONITOR_TIMEOUT']

def test_config_validation():
    """Tests the validation logic."""
    config = Config()
    is_valid, errors = config.validate()
    assert is_valid is True
    assert len(errors) == 0
    
    # Test invalid port
    config.set('dashboard.port', 99999)
    is_valid, errors = config.validate()
    assert is_valid is False
    assert "dashboard.port must be between 1-65535" in errors[0]