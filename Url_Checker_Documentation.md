# URL Monitor - Complete Documentation

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Installation Guide](#installation-guide)
3. [Configuration](#configuration)
4. [CLI Reference](#cli-reference)
5. [Web Dashboard](#web-dashboard)
6. [API Reference](#api-reference)
7. [Database Schema](#database-schema)
8. [Deployment Guide](#deployment-guide)
9. [Performance Optimization](#performance-optimization)
10. [Monitoring & Logging](#monitoring--logging)
11. [Security Considerations](#security-considerations)
12. [Troubleshooting](#troubleshooting)
13. [Development Guide](#development-guide)

## Architecture Overview

### System Design

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────┐
│   Scheduler     │───▶│    Checker   │───▶│  Database   │
│  (Cron-like)    │    │  (Async)     │    │  (SQLite)   │
└─────────────────┘    └──────────────┘    └─────────────┘
         │                       │                  │
         ▼                       ▼                  ▼
┌─────────────────┐    ┌──────────────┐    ┌─────────────┐
│  Web Dashboard  │    │   Reporter   │    │    Logs     │
│   (Optional)    │    │ (Analytics)  │    │   (Files)   │
└─────────────────┘    └──────────────┘    └─────────────┘
```

### Core Components

1. **URLChecker**: HTTP client with timeout and error handling
2. **DatabaseManager**: SQLite operations for URLs and results
3. **Scheduler**: Time-based execution controller
4. **Dashboard**: Web interface for monitoring and management
5. **Reporter**: Status analysis and history management

### Execution Flow

```
Start → Load Config → Connect DB → Load URLs → Check URLs (Concurrent) → Save Results → Generate Report → Exit
```

## Installation Guide

### System Requirements

- **Python**: 3.8 or higher
- **RAM**: 128MB minimum (typically uses <50MB)
- **Storage**: 100MB for application + database growth
- **Network**: Outbound HTTP/HTTPS access

### Step-by-Step Installation

#### 1. Environment Setup

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3 python3-pip sqlite3
```

**CentOS/RHEL:**
```bash
sudo yum install python3 python3-pip sqlite
```

**macOS:**
```bash
brew install python3 sqlite3
```

**Windows:**
- Download Python from python.org
- SQLite included with Python

#### 2. Application Installation

**From Git:**
```bash
git clone https://github.com/your-username/url-monitor.git
cd url-monitor
pip3 install -r requirements.txt
```

**Manual Setup:**
```bash
mkdir url-monitor
cd url-monitor
# Copy monitor.py file
pip3 install requests flask
```

#### 3. Initialize Application

```bash
python3 monitor.py --init
```

This creates:
- `config.json` - Configuration file
- `monitor.db` - SQLite database
- `logs/` - Log directory

### Verification

```bash
# Test installation
python3 monitor.py --version

# Add test URL
python3 monitor.py --add-url https://httpstat.us/200

# Run test check
python3 monitor.py --run-check

# View results
python3 monitor.py --status
```

## Configuration

### config.json Structure

```json
{
  "application": {
    "name": "URL Monitor",
    "version": "1.0.0",
    "timezone": "UTC"
  },
  "scheduler": {
    "enabled": true,
    "schedules": ["06:00", "14:00", "20:00"],
    "run_on_startup": false
  },
  "checker": {
    "request_timeout": 10,
    "concurrent_limit": 20,
    "retry_attempts": 2,
    "retry_delay": 5,
    "user_agent": "URLMonitor/1.0"
  },
  "database": {
    "path": "monitor.db",
    "retention_days": 30,
    "auto_cleanup": true
  },
  "dashboard": {
    "enabled": true,
    "port": 8080,
    "host": "0.0.0.0",
    "debug": false
  },
  "logging": {
    "level": "INFO",
    "file": "logs/monitor.log",
    "max_size": "10MB",
    "backup_count": 5
  }
}
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MONITOR_CONFIG` | Config file path | `config.json` |
| `MONITOR_DB` | Database file path | `monitor.db` |
| `MONITOR_PORT` | Dashboard port | `8080` |
| `MONITOR_TIMEZONE` | Timezone for schedules | `UTC` |
| `MONITOR_LOG_LEVEL` | Logging level | `INFO` |

### Advanced Configuration

#### Custom Schedules

```json
{
  "scheduler": {
    "schedules": [
      "00:00",  // Midnight
      "06:00",  // 6 AM
      "12:00",  // Noon
      "18:00"   // 6 PM
    ],
    "timezone": "America/New_York"
  }
}
```

#### Performance Tuning

```json
{
  "checker": {
    "request_timeout": 15,      // Longer timeout for slow sites
    "concurrent_limit": 50,     // More concurrent checks
    "retry_attempts": 3,        // More retry attempts
    "connect_timeout": 5,       // Connection timeout
    "read_timeout": 10          // Read timeout
  }
}
```

## CLI Reference

### URL Management Commands

#### Add URL
```bash
python3 monitor.py --add-url <URL> [OPTIONS]

Options:
  --name TEXT          Friendly name for the URL
  --timeout INTEGER    Custom timeout (seconds)
  --active            Enable monitoring (default)
  --inactive          Disable monitoring

Examples:
  python3 monitor.py --add-url https://google.com
  python3 monitor.py --add-url https://api.example.com --name "API Endpoint"
  python3 monitor.py --add-url https://test.com --timeout 30
```

#### List URLs
```bash
python3 monitor.py --list-urls [OPTIONS]

Options:
  --active-only       Show only active URLs
  --inactive-only     Show only inactive URLs
  --format TABLE      Output format (TABLE, JSON, CSV)

Examples:
  python3 monitor.py --list-urls
  python3 monitor.py --list-urls --active-only
  python3 monitor.py --list-urls --format JSON
```

#### Remove URL
```bash
python3 monitor.py --remove-url <URL_OR_ID>

Examples:
  python3 monitor.py --remove-url https://google.com
  python3 monitor.py --remove-url 1  # Remove by ID
```

#### Update URL
```bash
python3 monitor.py --update-url <URL_OR_ID> [OPTIONS]

Options:
  --name TEXT         Update friendly name
  --timeout INTEGER   Update timeout
  --active           Enable monitoring
  --inactive         Disable monitoring

Examples:
  python3 monitor.py --update-url 1 --name "Google Search"
  python3 monitor.py --update-url https://google.com --inactive
```

### Monitoring Commands

#### Run Check
```bash
python3 monitor.py --run-check [OPTIONS]

Options:
  --url TEXT          Check specific URL only
  --force             Force check even if recently checked
  --verbose          Show detailed output

Examples:
  python3 monitor.py --run-check
  python3 monitor.py --run-check --url https://google.com
  python3 monitor.py --run-check --verbose
```

#### View Status
```bash
python3 monitor.py --status [OPTIONS]

Options:
  --format TABLE      Output format (TABLE, JSON, CSV)
  --show-all         Show inactive URLs too
  --details          Include response times and errors

Examples:
  python3 monitor.py --status
  python3 monitor.py --status --format JSON
  python3 monitor.py --status --details
```

#### View History
```bash
python3 monitor.py --history [OPTIONS]

Options:
  --url TEXT         Show history for specific URL
  --days INTEGER     Number of days to show (default: 7)
  --limit INTEGER    Maximum number of records
  --format TABLE     Output format

Examples:
  python3 monitor.py --history
  python3 monitor.py --history --days 30
  python3 monitor.py --history --url https://google.com
```

### Service Commands

#### Start Scheduler
```bash
python3 monitor.py --schedule [OPTIONS]

Options:
  --foreground       Run in foreground (default)
  --daemon          Run as daemon (background)
  --pid-file TEXT   PID file location for daemon

Examples:
  python3 monitor.py --schedule
  python3 monitor.py --schedule --daemon --pid-file /var/run/monitor.pid
```

#### Start Dashboard
```bash
python3 monitor.py --dashboard [OPTIONS]

Options:
  --port INTEGER     Port number (default: 8080)
  --host TEXT        Host address (default: 0.0.0.0)
  --debug           Enable debug mode

Examples:
  python3 monitor.py --dashboard
  python3 monitor.py --dashboard --port 3000
  python3 monitor.py --dashboard --debug
```

#### Combined Mode
```bash
python3 monitor.py --dashboard --schedule [OPTIONS]

# Runs both dashboard and scheduler together
```

### Maintenance Commands

#### Database Operations
```bash
# Initialize/reset database
python3 monitor.py --init [--force]

# Verify database integrity
python3 monitor.py --verify-db

# Clean old records
python3 monitor.py --cleanup [--days INTEGER]

# Export data
python3 monitor.py --export [--format JSON] [--output FILE]

# Import data
python3 monitor.py --import [--file FILE]
```

#### Configuration
```bash
# Show current configuration
python3 monitor.py --show-config

# Validate configuration
python3 monitor.py --check-config

# Reset to defaults
python3 monitor.py --reset-config
```

#### Logs and Debugging
```bash
# View recent logs
python3 monitor.py --logs [--lines INTEGER]

# Test URL connectivity
python3 monitor.py --test-url <URL>

# System information
python3 monitor.py --system-info

# Version information
python3 monitor.py --version
```

## Web Dashboard

### Accessing the Dashboard

1. **Start dashboard**: `python3 monitor.py --dashboard`
2. **Open browser**: Navigate to `http://localhost:8080`
3. **Default credentials**: No authentication required (local access)

### Dashboard Features

#### Overview Page (`/`)

**Status Summary:**
- Total URLs monitored
- Current up/down counts
- Last check timestamp
- Overall system health

**Recent Activity:**
- Last 10 check results
- Response time trends
- Error notifications

**Quick Actions:**
- Add new URL
- Run immediate check
- Access detailed views

#### URL Management (`/urls`)

**URL List:**
- All monitored URLs with status
- Response times and status codes
- Enable/disable monitoring
- Edit URL settings

**Add New URL:**
```html
Form fields:
- URL (required)
- Friendly name (optional)
- Custom timeout (optional)
- Monitoring enabled (checkbox)
```

**Bulk Operations:**
- Enable/disable multiple URLs
- Delete multiple URLs
- Export URL list

#### Historical Data (`/history`)

**Charts and Graphs:**
- Response time trends
- Uptime percentage
- Status code distribution
- Error frequency

**Filter Options:**
- Date range selection
- Specific URL filtering
- Status code filtering
- Error type filtering

**Data Export:**
- CSV download
- JSON export
- Print-friendly view

#### Real-time Monitor (`/live`)

**Live Updates:**
- Auto-refreshing status (30 seconds)
- Real-time check results
- Status change notifications
- Response time monitoring

**Alert Indicators:**
- 🟢 All systems operational
- 🟡 Some issues detected
- 🔴 Critical issues found

### API Integration

The dashboard provides REST API endpoints:

```javascript
// Get all URLs status
fetch('/api/status')
  .then(response => response.json())
  .then(data => console.log(data));

// Add new URL
fetch('/api/urls', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    url: 'https://example.com',
    name: 'Example Site'
  })
});

// Trigger manual check
fetch('/api/check', {method: 'POST'});
```

## API Reference

### REST Endpoints

#### GET /api/status
Get current status of all monitored URLs.

**Response:**
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "total_urls": 5,
  "up_count": 4,
  "down_count": 1,
  "urls": [
    {
      "id": 1,
      "url": "https://google.com",
      "name": "Google",
      "is_up": true,
      "status_code": 200,
      "response_time": 127.5,
      "last_checked": "2024-01-15T10:28:00Z",
      "error_message": null
    }
  ]
}
```

#### GET /api/urls
List all monitored URLs.

**Query Parameters:**
- `active`: Filter by active status (true/false)
- `limit`: Maximum number of results
- `offset`: Pagination offset

#### POST /api/urls
Add a new URL to monitor.

**Request Body:**
```json
{
  "url": "https://example.com",
  "name": "Example Site",
  "timeout": 10,
  "active": true
}
```

**Response:**
```json
{
  "success": true,
  "id": 6,
  "message": "URL added successfully"
}
```

#### PUT /api/urls/:id
Update existing URL settings.

#### DELETE /api/urls/:id
Remove URL from monitoring.

#### GET /api/history/:id
Get historical data for specific URL.

**Query Parameters:**
- `days`: Number of days (default: 7)
- `limit`: Maximum records (default: 100)

#### POST /api/check
Trigger immediate check of all active URLs.

**Response:**
```json
{
  "success": true,
  "checked_urls": 5,
  "duration": 2.3,
  "results": [...]
}
```

## Database Schema

### Tables Structure

#### urls
Stores URL configuration and metadata.

```sql
CREATE TABLE urls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT UNIQUE NOT NULL,
    name TEXT,
    timeout INTEGER DEFAULT 10,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_checked TIMESTAMP
);
```

#### url_checks
Stores historical check results.

```sql
CREATE TABLE url_checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url_id INTEGER,
    status_code INTEGER,
    response_time REAL,
    is_up BOOLEAN,
    error_message TEXT,
    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (url_id) REFERENCES urls (id) ON DELETE CASCADE
);
```

#### system_info
Stores application metadata.

```sql
CREATE TABLE system_info (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Indexes

```sql
-- Performance indexes
CREATE INDEX idx_url_checks_url_id ON url_checks(url_id);
CREATE INDEX idx_url_checks_checked_at ON url_checks(checked_at);
CREATE INDEX idx_urls_active ON urls(is_active);
CREATE INDEX idx_urls_last_checked ON urls(last_checked);
```

### Database Maintenance

#### Automatic Cleanup
```python
# Configurable retention period
DELETE FROM url_checks 
WHERE checked_at < datetime('now', '-30 days');
```

#### Manual Maintenance
```bash
# Vacuum database (reclaim space)
python3 monitor.py --vacuum-db

# Analyze query performance
python3 monitor.py --analyze-db

# Export database
python3 monitor.py --export-db backup.sql
```

## Deployment Guide

### Render Deployment

#### Method 1: Direct Git Deploy

1. **Fork repository** to your GitHub account

2. **Create Render account** at render.com

3. **Create new Web Service:**
   - Connect GitHub repository
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python monitor.py --dashboard --schedule`

4. **Configure environment variables:**
   ```
   MONITOR_PORT=10000
   MONITOR_TIMEZONE=UTC
   ```

5. **Initialize with URLs:**
   ```bash
   # Use Render Shell or connect via SSH
   python monitor.py --add-url https://your-site.com
   ```

#### Method 2: External Cron Trigger

1. **Deploy as Web Service** (same as above)

2. **Modify Start Command:**
   ```bash
   python monitor.py --dashboard
   ```

3. **Setup External Cron** (cron-job.org):
   - `06:00 UTC`: `GET https://your-app.onrender.com/api/check`
   - `14:00 UTC`: `GET https://your-app.onrender.com/api/check`
   - `20:00 UTC`: `GET https://your-app.onrender.com/api/check`

### Docker Deployment

#### Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create data directory
RUN mkdir -p data logs

# Initialize database
RUN python monitor.py --init

EXPOSE 8080

CMD ["python", "monitor.py", "--dashboard", "--schedule"]
```

#### docker-compose.yml
```yaml
version: '3.8'

services:
  url-monitor:
    build: .
    ports:
      - "8080:8080"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - MONITOR_TIMEZONE=UTC
      - MONITOR_DB=/app/data/monitor.db
    restart: unless-stopped
```

#### Deployment Commands
```bash
# Build and run
docker-compose up -d

# Add URLs
docker-compose exec url-monitor python monitor.py --add-url https://example.com

# View logs
docker-compose logs -f url-monitor
```

### Traditional VPS Deployment

#### Systemd Service

**Create service file**: `/etc/systemd/system/url-monitor.service`

```ini
[Unit]
Description=URL Monitor Service
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/url-monitor
ExecStart=/usr/bin/python3 /opt/url-monitor/monitor.py --schedule --dashboard
Restart=always
RestartSec=5

Environment=MONITOR_CONFIG=/opt/url-monitor/config.json
Environment=MONITOR_DB=/opt/url-monitor/data/monitor.db

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable url-monitor
sudo systemctl start url-monitor
sudo systemctl status url-monitor
```

#### Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name monitor.yourdomain.com;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Performance Optimization

### Resource Usage Optimization

#### Memory Management
```python
# Limit concurrent checks to control memory
{
  "checker": {
    "concurrent_limit": 20,  # Reduce for low-memory systems
    "request_timeout": 10,
    "connection_pool_size": 10
  },
  "database": {
    "retention_days": 30,     # Limit historical data
    "auto_cleanup": true      # Enable automatic cleanup
  }
}
```

#### CPU Optimization
```python
# Efficient request handling
import asyncio
import aiohttp

async def check_urls_async(urls):
    async with aiohttp.ClientSession() as session:
        tasks = [check_single_url(session, url) for url in urls]
        return await asyncio.gather(*tasks, return_exceptions=True)
```

#### Database Performance
```sql
-- Optimize queries with proper indexes
CREATE INDEX idx_url_checks_composite ON url_checks(url_id, checked_at DESC);

-- Use PRAGMA for SQLite optimization
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA cache_size=10000;
PRAGMA temp_store=memory;
```

### Scaling Strategies

#### Horizontal Scaling
```python
# Split URLs across multiple instances
{
  "checker": {
    "shard_id": 1,
    "total_shards": 3,
    "url_distribution": "hash"  # or "round_robin"
  }
}
```

#### Caching Strategies
```python
# Response time caching
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_url_history(url_id, days=7):
    # Cache frequently accessed historical data
    pass
```

## Monitoring & Logging

### Logging Configuration

#### Log Levels
```python
LOGGING_CONFIG = {
    'DEBUG': 'Detailed diagnostic information',
    'INFO': 'General application flow',
    'WARNING': 'Potential issues',
    'ERROR': 'Error conditions',
    'CRITICAL': 'Serious errors'
}
```

#### Log Format
```python
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
```

#### Log Rotation
```python
{
  "logging": {
    "file": "logs/monitor.log",
    "max_size": "10MB",
    "backup_count": 5,
    "rotation": "time",  # or "size"
    "when": "midnight",
    "interval": 1
  }
}
```

### Application Metrics

#### Performance Metrics
```python
METRICS = {
    'total_checks': 'Counter of all URL checks',
    'successful_checks': 'Counter of successful checks',
    'failed_checks': 'Counter of failed checks',
    'average_response_time': 'Average response time',
    'check_duration': 'Time taken for full check cycle'
}
```

#### Health Endpoints
```python
# GET /health
{
  "status": "healthy",
  "uptime": 3600,
  "last_check": "2024-01-15T10:30:00Z",
  "database_status": "connected",
  "urls_monitored": 25,
  "memory_usage": "45MB"
}
```

### External Monitoring Integration

#### Prometheus Metrics
```python
from prometheus_client import Counter, Histogram, Gauge

url_checks_total = Counter('url_checks_total', 'Total URL checks')
response_time_histogram = Histogram('response_time_seconds', 'Response time')
urls_up_gauge = Gauge('urls_up', 'Number of URLs currently up')
```

#### Grafana Dashboard
```json
{
  "dashboard": {
    "title": "URL Monitor Dashboard",
    "panels": [
      {
        "title": "URLs Status",
        "type": "stat",
        "targets": ["urls_up", "urls_down"]
      },
      {
        "title": "Response Times",
        "type": "graph",
        "targets": ["response_time_histogram"]
      }
    ]
  }
}
```

## Security Considerations

### Application Security

#### Input Validation
```python
import re
from urllib.parse import urlparse

def validate_url(url):
    # URL format validation
    pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+), re.IGNORECASE)
    
    if not pattern.match(url):
        raise ValueError("Invalid URL format")
    
    parsed = urlparse(url)
    if parsed.scheme not in ['http', 'https']:
        raise ValueError("Only HTTP/HTTPS URLs allowed")
    
    return True
```

#### Rate Limiting
```python
from time import time
from collections import defaultdict

class RateLimiter:
    def __init__(self, max_requests=100, time_window=3600):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = defaultdict(list)
    
    def is_allowed(self, identifier):
        now = time()
        requests = self.requests[identifier]
        
        # Clean old requests
        requests[:] = [req_time for req_time in requests 
                      if now - req_time < self.time_window]
        
        if len(requests) >= self.max_requests:
            return False
        
        requests.append(now)
        return True
```

#### Environment Security
```python
# Secure configuration loading
import os
from pathlib import Path

def load_secure_config():
    config_path = os.environ.get('MONITOR_CONFIG', 'config.json')
    
    # Validate config file path
    if not Path(config_path).resolve().is_relative_to(Path.cwd()):
        raise SecurityError("Config file outside allowed directory")
    
    return load_config(config_path)
```

### Network Security

#### SSL/TLS Verification
```python
import ssl
import requests

def create_secure_session():
    session = requests.Session()
    
    # Enable SSL verification
    session.verify = True
    
    # Custom SSL context for enhanced security
    context = ssl.create_default_context()
    context.check_hostname = True
    context.verify_mode = ssl.CERT_REQUIRED
    
    return session
```

#### Request Headers
```python
SECURE_HEADERS = {
    'User-Agent': 'URLMonitor/1.0 (+https://your-domain.com/monitor)',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}
```

### Data Protection

#### Database Security
```sql
-- Restrict database permissions
PRAGMA secure_delete = ON;
PRAGMA foreign_keys = ON;

-- Create read-only user for reporting
CREATE USER monitor_readonly;
GRANT SELECT ON urls TO monitor_readonly;
GRANT SELECT ON url_checks TO monitor_readonly;
```

#### Sensitive Data Handling
```python
# Avoid logging sensitive information
def sanitize_url_for_logging(url):
    from urllib.parse import urlparse, urlunparse
    
    parsed = urlparse(url)
    if parsed.password:
        # Remove password from logs
        sanitized = parsed._replace(
            netloc=f"{parsed.username}:***@{parsed.hostname}:{parsed.port or ''}"
        )
        return urlunparse(sanitized)
    return url
```

## Troubleshooting

### Common Issues

#### Database Problems

**Error: "database is locked"**
```bash
# Solution 1: Check for running processes
ps aux | grep monitor.py
kill <process_id>

# Solution 2: Enable WAL mode
sqlite3 monitor.db "PRAGMA journal_mode=WAL;"

# Solution 3: Reset database
python monitor.py --init --force
```

**Error: "no such table: urls"**
```bash
# Reinitialize database
python monitor.py --init

# Verify tables exist
sqlite3 monitor.db ".tables"
```

#### Network Issues

**Error: "Connection timeout"**
```python
# Increase timeout in config.json
{
  "checker": {
    "request_timeout": 30,
    "connect_timeout": 10
  }
}
```

**Error: "SSL certificate verify failed"**
```python
# For development only - disable SSL verification
{
  "checker": {
    "verify_ssl": false
  }
}
```

#### Memory Issues

**Error: "Memory usage too high"**
```python
# Reduce concurrent checks
{
  "checker": {
    "concurrent_limit": 5
  },
  "database": {
    "retention_days": 7  # Keep less history
  }
}
```

#### Permission Issues

**Error: "Permission denied"**
```bash
# Fix file permissions
chmod 755 monitor.py
chmod 644 config.json
chmod 666 monitor.db

# Fix directory permissions
mkdir -p logs data
chmod 755 logs data
```

### Debugging Tools

#### Debug Mode
```bash
# Enable verbose logging
python monitor.py --run-check --debug --verbose

# Test single URL
python monitor.py --test-url https://example.com --debug
```

#### Database Inspection
```bash
# View database contents
sqlite3 monitor.db "SELECT * FROM urls;"
sqlite3 monitor.db "SELECT * FROM url_checks ORDER BY checked_at DESC LIMIT 10;"

# Database statistics
python monitor.py --db-stats
```

#### Performance Profiling
```python
# Enable profiling
python -m cProfile -o profile.stats monitor.py --run-check

# Analyze profile
python -c "import pstats; pstats.Stats('profile.stats').sort_stats('cumulative').print_stats(20)"
```

### Log Analysis

#### Common Log Patterns
```bash
# Find errors
grep -i error logs/monitor.log

# Check response times
grep "Response time" logs/monitor.log | awk '{print $NF}' | sort -n

# Monitor memory usage
grep -i memory logs/monitor.log
```

#### Log Rotation Issues
```bash
# Check log file size
ls -lh logs/monitor.log*

# Manual log rotation
python monitor.py --rotate-logs
```

## Development Guide

### Setting Up Development Environment

#### Prerequisites
```bash
# Development dependencies
pip install pytest pytest-cov black flake8 mypy

# Pre-commit hooks
pip install pre-commit
pre-commit install
```

#### Project Structure
```
url-monitor/
├── monitor.py              # Main application
├── src/                    # Source modules
│   ├── __init__.py
│   ├── checker.py          # URL checking logic
│   ├── database.py         # Database operations
│   ├── scheduler.py        # Scheduling logic
│   └── dashboard.py        # Web interface
├── tests/                  # Unit tests
│   ├── __init__.py
│   ├── test_checker.py
│   ├── test_database.py
│   └── test_integration.py
├── docs/                   # Documentation
├── requirements/           # Requirements files
│   ├── base.txt
│   ├── dev.txt
│   └── prod.txt
└── scripts/                # Utility scripts
    ├── deploy.sh
    └── backup.sh
```

### Testing

#### Unit Tests
```python
# tests/test_checker.py
import pytest
from src.checker import URLChecker

class TestURLChecker:
    def setup_method(self):
        self.checker = URLChecker()
    
    def test_valid_url(self):
        result = self.checker.check_url('https://httpstat.us/200')
        assert result.is_up is True
        assert result.status_code == 200
    
    def test_invalid_url(self):
        result = self.checker.check_url('https://httpstat.us/404')
        assert result.is_up is False
        assert result.status_code == 404
    
    def test_timeout(self):
        result = self.checker.check_url('https://httpstat.us/200?sleep=20000')
        assert result.is_up is False
        assert 'timeout' in result.error_message.lower()
```

#### Integration Tests
```python
# tests/test_integration.py
import pytest
import tempfile
from src.database import DatabaseManager
from src.checker import URLChecker

class TestIntegration:
    def setup_method(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.db = DatabaseManager(self.temp_db.name)
        self.checker = URLChecker()
    
    def test_full_check_cycle(self):
        # Add URL
        url_id = self.db.add_url('https://httpstat.us/200')
        
        # Check URL
        result = self.checker.check_url('https://httpstat.us/200')
        
        # Save result
        self.db.save_check_result(url_id, result)
        
        # Verify saved
        history = self.db.get_url_history(url_id, limit=1)
        assert len(history) == 1
        assert history[0]['is_up'] is True
```

#### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_checker.py

# Run with verbose output
pytest -v tests/
```

### Code Quality

#### Code Formatting
```bash
# Format code with Black
black src/ tests/

# Check formatting
black --check src/ tests/
```

#### Linting
```bash
# Flake8 linting
flake8 src/ tests/

# Type checking with mypy
mypy src/
```

#### Pre-commit Configuration
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.1.0
    hooks:
      - id: black
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.0.1
    hooks:
      - id: mypy
```

### Contributing Guidelines

#### Pull Request Process
1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/amazing-feature`
3. **Make changes** with tests
4. **Run quality checks**: `pytest && black . && flake8`
5. **Commit changes**: `git commit -m 'Add amazing feature'`
6. **Push to branch**: `git push origin feature/amazing-feature`
7. **Create Pull Request**

#### Code Review Checklist
- [ ] Tests added for new functionality
- [ ] Documentation updated
- [ ] Code follows style guidelines
- [ ] No breaking changes without migration path
- [ ] Performance impact considered
- [ ] Security implications reviewed

### Release Process

#### Version Management
```python
# src/version.py
__version__ = "1.0.0"
__version_info__ = (1, 0, 0)
```

#### Release Checklist
1. **Update version numbers**
2. **Update CHANGELOG.md**
3. **Run full test suite**
4. **Build and test package**
5. **Tag release**: `git tag v1.0.0`
6. **Push to repository**
7. **Create GitHub release**
8. **Deploy to production**

---

## Appendices

### A. Configuration Examples

#### Production Configuration
```json
{
  "application": {
    "name": "URL Monitor - Production",
    "version": "1.0.0",
    "timezone": "UTC"
  },
  "scheduler": {
    "enabled": true,
    "schedules": ["06:00", "14:00", "20:00"],
    "run_on_startup": false
  },
  "checker": {
    "request_timeout": 15,
    "concurrent_limit": 50,
    "retry_attempts": 3,
    "retry_delay": 5,
    "user_agent": "URLMonitor-Production/1.0"
  },
  "database": {
    "path": "/app/data/monitor.db",
    "retention_days": 90,
    "auto_cleanup": true
  },
  "dashboard": {
    "enabled": true,
    "port": 8080,
    "host": "0.0.0.0",
    "debug": false
  },
  "logging": {
    "level": "INFO",
    "file": "/app/logs/monitor.log",
    "max_size": "50MB",
    "backup_count": 10
  }
}
```

### B. SQL Queries Reference

#### Common Queries
```sql
-- Get uptime percentage for last 30 days
SELECT 
    u.url,
    u.name,
    COUNT(*) as total_checks,
    SUM(CASE WHEN uc.is_up THEN 1 ELSE 0 END) as up_checks,
    ROUND(
        (SUM(CASE WHEN uc.is_up THEN 1 ELSE 0 END) * 100.0 / COUNT(*)), 2
    ) as uptime_percentage
FROM urls u
JOIN url_checks uc ON u.id = uc.url_id
WHERE uc.checked_at >= datetime('now', '-30 days')
GROUP BY u.id, u.url, u.name;

-- Average response times by hour
SELECT 
    strftime('%H', checked_at) as hour,
    AVG(response_time) as avg_response_time,
    COUNT(*) as check_count
FROM url_checks 
WHERE checked_at >= datetime('now', '-7 days')
    AND is_up = 1
GROUP BY strftime('%H', checked_at)
ORDER BY hour;

-- Most frequent errors
SELECT 
    error_message,
    COUNT(*) as error_count
FROM url_checks 
WHERE error_message IS NOT NULL
    AND checked_at >= datetime('now', '-7 days')
GROUP BY error_message
ORDER BY error_count DESC;
```

### C. Resource Requirements

#### Minimum Requirements
- **CPU**: 0.1 vCPU (shared)
- **RAM**: 64MB minimum, 128MB recommended
- **Storage**: 100MB for app + 10MB/month for database
- **Network**: Outbound HTTP/HTTPS access

#### Recommended Requirements
- **CPU**: 0.25 vCPU for 100+ URLs
- **RAM**: 256MB for better performance
- **Storage**: 1GB for long-term historical data
- **Network**: Stable internet connection

#### Scaling Guidelines
| URLs | RAM Usage | Storage/Month | Check Duration |
|------|-----------|---------------|----------------|
| 1-10 | 50-80MB   | 1-5MB        | 5-15 seconds   |
| 11-50 | 80-150MB  | 5-25MB       | 15-45 seconds  |
| 51-100 | 150-250MB | 25-50MB      | 30-90 seconds  |
| 100+ | 250-500MB  | 50-100MB     | 60-180 seconds |

---

*This documentation is continuously updated. For the latest version, visit the [GitHub repository](https://github.com/your-username/url-monitor).*