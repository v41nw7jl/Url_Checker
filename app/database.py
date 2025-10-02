"""
Database management for URL Monitor
SQLite-based storage optimized for Render free tier
"""

import sqlite3
import logging
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
from contextlib import contextmanager
from dataclasses import dataclass

from .config import get_config

logger = logging.getLogger(__name__)


@dataclass
class URLRecord:
    """Data class for URL records"""
    id: Optional[int]
    url: str
    name: Optional[str]
    timeout: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_checked: Optional[datetime]


@dataclass
class CheckResult:
    """Data class for URL check results"""
    id: Optional[int]
    url_id: int
    status_code: Optional[int]
    response_time: Optional[float]
    is_up: bool
    error_message: Optional[str]
    checked_at: datetime


class DatabaseManager:
    """SQLite database manager with connection pooling and thread safety"""
    
    def __init__(self, db_path: Optional[str] = None):
        self.config = get_config()
        self.db_path = db_path or self.config.get('database.path', 'data/monitor.db')
        self._local = threading.local()
        self._lock = threading.Lock()
        self._initialized = False
        
        # Ensure database directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database on first access
        self.initialize()
    
    @property
    def connection(self) -> sqlite3.Connection:
        """Get thread-local database connection"""
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            conn = sqlite3.connect(
                self.db_path,
                timeout=self.config.get('database.connection_timeout', 30),
                check_same_thread=False
            )
            
            # Enable foreign keys and optimize SQLite
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA synchronous = NORMAL")
            conn.execute("PRAGMA cache_size = 10000")
            conn.execute("PRAGMA temp_store = MEMORY")
            
            # Row factory for dict-like access
            conn.row_factory = sqlite3.Row
            
            self._local.connection = conn
        
        return self._local.connection
    
    @contextmanager
    def get_cursor(self):
        """Get database cursor with automatic transaction handling"""
        cursor = self.connection.cursor()
        try:
            yield cursor
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            cursor.close()
    
    def initialize(self) -> bool:
        """Initialize database schema"""
        if self._initialized:
            return True
        
        try:
            with self._lock:
                if self._initialized:  # Double-check pattern
                    return True
                
                with self.get_cursor() as cursor:
                    # Create URLs table
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS urls (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            url TEXT UNIQUE NOT NULL,
                            name TEXT,
                            timeout INTEGER DEFAULT 10,
                            is_active BOOLEAN DEFAULT 1,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            last_checked TIMESTAMP
                        )
                    """)
                    
                    # Create URL checks table
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS url_checks (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            url_id INTEGER NOT NULL,
                            status_code INTEGER,
                            response_time REAL,
                            is_up BOOLEAN NOT NULL,
                            error_message TEXT,
                            checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (url_id) REFERENCES urls (id) ON DELETE CASCADE
                        )
                    """)
                    
                    # Create system info table for metadata
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS system_info (
                            key TEXT PRIMARY KEY,
                            value TEXT,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    
                    # Create indexes for performance
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_url_checks_url_id ON url_checks(url_id)")
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_url_checks_checked_at ON url_checks(checked_at)")
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_urls_active ON urls(is_active)")
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_urls_last_checked ON urls(last_checked)")
                    
                    # Set database version
                    cursor.execute("""
                        INSERT OR REPLACE INTO system_info (key, value, updated_at)
                        VALUES ('schema_version', '1.0.0', CURRENT_TIMESTAMP)
                    """)
                    
                    logger.info("Database initialized successfully")
                    self._initialized = True
                    return True
                    
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            return False
    
    def add_url(self, url: str, name: Optional[str] = None, 
                timeout: int = 10, active: bool = True) -> Optional[int]:
        """Add a new URL to monitor"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO urls (url, name, timeout, is_active, created_at, updated_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """, (url, name, timeout, active))
                
                url_id = cursor.lastrowid
                logger.info(f"Added URL: {url} (ID: {url_id})")
                return url_id
                
        except sqlite3.IntegrityError:
            logger.warning(f"URL already exists: {url}")
            return None
        except Exception as e:
            logger.error(f"Failed to add URL {url}: {e}")
            return None
    
    def get_url(self, url_id: int) -> Optional[URLRecord]:
        """Get URL by ID"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT * FROM urls WHERE id = ?", (url_id,))
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_url_record(row)
                return None
                
        except Exception as e:
            logger.error(f"Failed to get URL {url_id}: {e}")
            return None
    
    def get_url_by_address(self, url: str) -> Optional[URLRecord]:
        """Get URL by address"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT * FROM urls WHERE url = ?", (url,))
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_url_record(row)
                return None
                
        except Exception as e:
            logger.error(f"Failed to get URL {url}: {e}")
            return None
    
    def list_urls(self, active_only: bool = False) -> List[URLRecord]:
        """List all URLs"""
        try:
            with self.get_cursor() as cursor:
                query = "SELECT * FROM urls"
                params = ()
                
                if active_only:
                    query += " WHERE is_active = 1"
                
                query += " ORDER BY created_at"
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                return [self._row_to_url_record(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to list URLs: {e}")
            return []
    
    def update_url(self, url_id: int, **kwargs) -> bool:
        """Update URL properties"""
        if not kwargs:
            return False
        
        try:
            # Build dynamic update query
            set_clauses = []
            params = []
            
            allowed_fields = {'name', 'timeout', 'is_active', 'last_checked'}
            for field, value in kwargs.items():
                if field in allowed_fields:
                    set_clauses.append(f"{field} = ?")
                    params.append(value)
            
            if not set_clauses:
                return False
            
            set_clauses.append("updated_at = CURRENT_TIMESTAMP")
            params.append(url_id)
            
            with self.get_cursor() as cursor:
                query = f"UPDATE urls SET {', '.join(set_clauses)} WHERE id = ?"
                cursor.execute(query, params)
                
                if cursor.rowcount > 0:
                    logger.info(f"Updated URL {url_id}")
                    return True
                else:
                    logger.warning(f"URL {url_id} not found for update")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to update URL {url_id}: {e}")
            return False
    
    def delete_url(self, url_id: int) -> bool:
        """Delete URL and its check history"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("DELETE FROM urls WHERE id = ?", (url_id,))
                
                if cursor.rowcount > 0:
                    logger.info(f"Deleted URL {url_id}")
                    return True
                else:
                    logger.warning(f"URL {url_id} not found for deletion")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to delete URL {url_id}: {e}")
            return False
    
    def delete_url_by_address(self, url: str) -> bool:
        """Delete URL by address"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("DELETE FROM urls WHERE url = ?", (url,))
                
                if cursor.rowcount > 0:
                    logger.info(f"Deleted URL {url}")
                    return True
                else:
                    logger.warning(f"URL {url} not found for deletion")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to delete URL {url}: {e}")
            return False
    
    def save_check_result(self, url_id: int, status_code: Optional[int], 
                         response_time: Optional[float], is_up: bool,
                         error_message: Optional[str] = None) -> Optional[int]:
        """Save URL check result"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO url_checks 
                    (url_id, status_code, response_time, is_up, error_message, checked_at)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (url_id, status_code, response_time, is_up, error_message))
                
                check_id = cursor.lastrowid
                
                # Update last_checked timestamp in urls table
                cursor.execute("""
                    UPDATE urls SET last_checked = CURRENT_TIMESTAMP 
                    WHERE id = ?
                """, (url_id,))
                
                return check_id
                
        except Exception as e:
            logger.error(f"Failed to save check result for URL {url_id}: {e}")
            return None
    
    def get_url_status(self, url_id: int) -> Optional[Dict[str, Any]]:
        """Get latest status for a URL"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("""
                    SELECT u.*, 
                           uc.status_code, uc.response_time, uc.is_up, 
                           uc.error_message, uc.checked_at
                    FROM urls u
                    LEFT JOIN url_checks uc ON u.id = uc.url_id
                    WHERE u.id = ?
                    ORDER BY uc.checked_at DESC
                    LIMIT 1
                """, (url_id,))
                
                row = cursor.fetchone()
                if row:
                    return dict(row)
                return None
                
        except Exception as e:
            logger.error(f"Failed to get URL status {url_id}: {e}")
            return None
    
    def get_all_status(self) -> List[Dict[str, Any]]:
        """Get current status of all URLs"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("""
                    SELECT u.id, u.url, u.name, u.is_active, u.last_checked,
                           latest.status_code, latest.response_time, 
                           latest.is_up, latest.error_message, latest.checked_at
                    FROM urls u
                    LEFT JOIN (
                        SELECT url_id, status_code, response_time, is_up, 
                               error_message, checked_at,
                               ROW_NUMBER() OVER (PARTITION BY url_id ORDER BY checked_at DESC) as rn
                        FROM url_checks
                    ) latest ON u.id = latest.url_id AND latest.rn = 1
                    ORDER BY u.created_at
                """)
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get all status: {e}")
            return []
    
    def get_url_history(self, url_id: int, days: int = 7, limit: int = 100) -> List[Dict[str, Any]]:
        """Get check history for a URL"""
        try:
            with self.get_cursor() as cursor:
                since_date = datetime.now() - timedelta(days=days)
                
                cursor.execute("""
                    SELECT * FROM url_checks 
                    WHERE url_id = ? AND checked_at >= ?
                    ORDER BY checked_at DESC
                    LIMIT ?
                """, (url_id, since_date, limit))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get URL history {url_id}: {e}")
            return []
    
    def get_uptime_stats(self, url_id: int, days: int = 30) -> Dict[str, Any]:
        """Calculate uptime statistics for a URL"""
        try:
            with self.get_cursor() as cursor:
                since_date = datetime.now() - timedelta(days=days)
                
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_checks,
                        SUM(CASE WHEN is_up THEN 1 ELSE 0 END) as up_checks,
                        AVG(CASE WHEN is_up AND response_time IS NOT NULL THEN response_time END) as avg_response_time,
                        MIN(CASE WHEN is_up AND response_time IS NOT NULL THEN response_time END) as min_response_time,
                        MAX(CASE WHEN is_up AND response_time IS NOT NULL THEN response_time END) as max_response_time
                    FROM url_checks
                    WHERE url_id = ? AND checked_at >= ?
                """, (url_id, since_date))
                
                row = cursor.fetchone()
                if row and row['total_checks'] > 0:
                    uptime_percentage = (row['up_checks'] / row['total_checks']) * 100
                    return {
                        'total_checks': row['total_checks'],
                        'up_checks': row['up_checks'],
                        'down_checks': row['total_checks'] - row['up_checks'],
                        'uptime_percentage': round(uptime_percentage, 2),
                        'avg_response_time': round(row['avg_response_time'] or 0, 2),
                        'min_response_time': row['min_response_time'],
                        'max_response_time': row['max_response_time'],
                        'period_days': days
                    }
                
                return {
                    'total_checks': 0,
                    'up_checks': 0,
                    'down_checks': 0,
                    'uptime_percentage': 0,
                    'avg_response_time': 0,
                    'min_response_time': None,
                    'max_response_time': None,
                    'period_days': days
                }
                
        except Exception as e:
            logger.error(f"Failed to get uptime stats for URL {url_id}: {e}")
            return {}
    
    def cleanup_old_records(self, retention_days: Optional[int] = None) -> int:
        """Clean up old check records"""
        retention_days = retention_days or self.config.get('database.retention_days', 30)
        
        try:
            with self.get_cursor() as cursor:
                cutoff_date = datetime.now() - timedelta(days=retention_days)
                
                cursor.execute("""
                    DELETE FROM url_checks 
                    WHERE checked_at < ?
                """, (cutoff_date,))
                
                deleted_count = cursor.rowcount
                logger.info(f"Cleaned up {deleted_count} old check records")
                
                # Vacuum database to reclaim space
                cursor.execute("VACUUM")
                
                return deleted_count
                
        except Exception as e:
            logger.error(f"Failed to cleanup old records: {e}")
            return 0
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            with self.get_cursor() as cursor:
                stats = {}
                
                # Count tables
                cursor.execute("SELECT COUNT(*) FROM urls")
                stats['total_urls'] = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM urls WHERE is_active = 1")
                stats['active_urls'] = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM url_checks")
                stats['total_checks'] = cursor.fetchone()[0]
                
                # Recent activity
                cursor.execute("""
                    SELECT COUNT(*) FROM url_checks 
                    WHERE checked_at >= datetime('now', '-24 hours')
                """)
                stats['checks_last_24h'] = cursor.fetchone()[0]
                
                # Database file size
                stats['db_file_size'] = Path(self.db_path).stat().st_size
                
                # Schema version
                cursor.execute("""
                    SELECT value FROM system_info WHERE key = 'schema_version'
                """)
                row = cursor.fetchone()
                stats['schema_version'] = row[0] if row else 'unknown'
                
                return stats
                
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {}
    
    def _row_to_url_record(self, row: sqlite3.Row) -> URLRecord:
        """Convert database row to URLRecord"""
        return URLRecord(
            id=row['id'],
            url=row['url'],
            name=row['name'],
            timeout=row['timeout'],
            is_active=bool(row['is_active']),
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at']),
            last_checked=datetime.fromisoformat(row['last_checked']) if row['last_checked'] else None
        )
    
    def close(self):
        """Close database connections"""
        if hasattr(self._local, 'connection') and self._local.connection:
            self._local.connection.close()
            self._local.connection = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Global database instance
_db_instance = None
_db_lock = threading.Lock()


def get_database(db_path: Optional[str] = None) -> DatabaseManager:
    """Get global database instance (singleton)"""
    global _db_instance
    
    if _db_instance is None:
        with _db_lock:
            if _db_instance is None:  # Double-check pattern
                _db_instance = DatabaseManager(db_path)
    
    return _db_instance


def reset_database() -> None:
    """Reset global database instance (for testing)"""
    global _db_instance
    with _db_lock:
        if _db_instance:
            _db_instance.close()
        _db_instance = None