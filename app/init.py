"""
URL Monitor Application Package
Lightweight URL monitoring application optimized for free-tier hosting
"""

__version__ = "1.0.0"
__author__ = "URL Monitor Team"
__description__ = "Lightweight URL monitoring for free hosting tiers"

# Package imports
from .config import get_config, Config
from .database import get_database, DatabaseManager, URLRecord, CheckResult

__all__ = [
    'get_config',
    'Config', 
    'get_database',
    'DatabaseManager',
    'URLRecord',
    'CheckResult',
    '__version__'
]