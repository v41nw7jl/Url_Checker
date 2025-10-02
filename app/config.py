"""
Configuration management for URL Monitor
Handles environment-based configuration with defaults optimized for Render free tier
"""

import os
import json
from typing import Dict, Any, Optional
from pathlib import Path

class Config:
    """Configuration management class"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or os.getenv('MONITOR_CONFIG', 'config.json')
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        config_path = Path(self.config_file)
        
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load config file {config_path}: {e}")
                print("Using default configuration")
        
        return self._default_config()
    
    def _default_config(self) -> Dict[str, Any]:
        """Default configuration optimized for Render free tier"""
        return {
            "application": {
                "name": "URL Monitor",
                "version": "1.0.0",
                "timezone": os.getenv('MONITOR_TIMEZONE', 'UTC')
            },
            "scheduler": {
                "enabled": True,
                "schedules": ["06:00", "14:00", "20:00"],
                "run_on_startup": False
            },
            "checker": {
                "request_timeout": int(os.getenv('MONITOR_TIMEOUT', '10')),
                "connect_timeout": 5,
                "read_timeout": 10,
                "concurrent_limit": 10,
                "retry_attempts": 2,
                "retry_delay": 3,
                "user_agent": "URLMonitor/1.0",
                "verify_ssl": True,
                "follow_redirects": True,
                "max_redirects": 3
            },
            "database": {
                "path": os.getenv('MONITOR_DB', 'data/monitor.db'),
                "retention_days": 30,
                "auto_cleanup": True,
                "backup_enabled": False,
                "connection_timeout": 30
            },
            "dashboard": {
                "enabled": True,
                "host": os.getenv('MONITOR_HOST', '0.0.0.0'),
                "port": int(os.getenv('PORT', os.getenv('MONITOR_PORT', '8080'))),
                "debug": os.getenv('FLASK_DEBUG', 'false').lower() == 'true',
                "secret_key": os.getenv('SECRET_KEY', 'dev-key-change-in-production'),
                "template_reload": False
            },
            "logging": {
                "level": os.getenv('MONITOR_LOG_LEVEL', 'INFO'),
                "file": "logs/monitor.log",
                "max_size": "10MB",
                "backup_count": 5,
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            },
            "performance": {
                "max_memory_mb": 200,
                "cleanup_interval": 3600,
                "response_time_threshold": 30.0,
                "error_threshold": 5
            }
        }
    
    def save_config(self) -> bool:
        """Save current configuration to file"""
        try:
            config_path = Path(self.config_file)
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_path, 'w') as f:
                json.dump(self._config, f, indent=2)
            return True
        except (IOError, OSError) as e:
            print(f"Error saving config: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation"""
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value using dot notation"""
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def update(self, updates: Dict[str, Any]) -> None:
        """Update configuration with new values"""
        def deep_update(base_dict: Dict, update_dict: Dict) -> Dict:
            for key, value in update_dict.items():
                if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                    deep_update(base_dict[key], value)
                else:
                    base_dict[key] = value
            return base_dict
        
        deep_update(self._config, updates)
    
    def validate(self) -> tuple:
        """Validate configuration and return (is_valid, errors)"""
        errors = []
        
        db_path = Path(self.get('database.path'))
        try:
            db_path.parent.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError) as e:
            errors.append(f"Cannot create database directory: {e}")
        
        log_file = Path(self.get('logging.file'))
        try:
            log_file.parent.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError) as e:
            errors.append(f"Cannot create log directory: {e}")
        
        if self.get('checker.request_timeout', 0) <= 0:
            errors.append("checker.request_timeout must be positive")
        
        if self.get('checker.concurrent_limit', 0) <= 0:
            errors.append("checker.concurrent_limit must be positive")
        
        if self.get('database.retention_days', 0) <= 0:
            errors.append("database.retention_days must be positive")
        
        port = self.get('dashboard.port', 0)
        if not (1 <= port <= 65535):
            errors.append(f"dashboard.port must be between 1-65535, got {port}")
        
        schedules = self.get('scheduler.schedules', [])
        if not isinstance(schedules, list) or not schedules:
            errors.append("scheduler.schedules must be a non-empty list")
        else:
            for schedule in schedules:
                if not isinstance(schedule, str) or not self._validate_time_format(schedule):
                    errors.append(f"Invalid schedule format: {schedule}")
        
        return len(errors) == 0, errors
    
    def _validate_time_format(self, time_str: str) -> bool:
        """Validate time format HH:MM"""
        try:
            parts = time_str.split(':')
            if len(parts) != 2:
                return False
            hour, minute = int(parts[0]), int(parts[1])
            return 0 <= hour <= 23 and 0 <= minute <= 59
        except (ValueError, IndexError):
            return False
    
    def is_production(self) -> bool:
        """Check if running in production"""
        return os.getenv('RENDER') == 'true' or os.getenv('ENVIRONMENT') == 'production'
    
    @property
    def config(self) -> Dict[str, Any]:
        """Get full configuration dictionary"""
        return self._config.copy()


# Global config instance
config = Config()


def get_config() -> Config:
    """Get global configuration instance"""
    return config


def create_default_config(output_file: str = 'config.json') -> bool:
    """Create default configuration file"""
    try:
        temp_config = Config()
        temp_config.config_file = output_file
        return temp_config.save_config()
    except Exception as e:
        print(f"Error creating default config: {e}")
        return False