# URL Monitor - Technology Stack

## Overview

This document outlines the complete technology stack and architectural decisions for the URL Monitor application, specifically optimized for free-tier hosting platforms like Render.

## Tech Stack

### Backend/Core
- **Python 3.8+** - Main programming language
- **SQLite** - Database (lightweight, serverless, perfect for free tier)
- **Requests** - HTTP client for URL checking
- **AsyncIO/Threading** - Concurrent URL checking
- **APScheduler** - Job scheduling (cron-like functionality)

### Web Interface
- **Flask** - Lightweight web framework for dashboard
- **Jinja2** - HTML templating (comes with Flask)
- **Bootstrap 5** - Frontend CSS framework (responsive design)
- **Chart.js** - JavaScript charting library for graphs
- **SQLite** - Same database for web interface

### Dependencies (minimal)
```txt
requests>=2.28.0
flask>=2.3.0
apscheduler>=3.10.0
```

## Architecture Pattern

### Serverless-Style Monolith
```
┌─────────────────────────────────────────────────────────┐
│                 Single Python Process                   │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐ │
│  │  Scheduler  │  │ URL Checker  │  │  Web Dashboard  │ │
│  │ (APScheduler)│  │(Async/Sync) │  │    (Flask)      │ │
│  └─────────────┘  └──────────────┘  └─────────────────┘ │
├─────────────────────────────────────────────────────────┤
│                 Database Layer                          │
│            SQLite + Python sqlite3                     │
└─────────────────────────────────────────────────────────┘
```

### Component Interaction Flow
```
User Request → Flask Router → Database Query → Template Render → Response
                    ↓
Scheduler Trigger → URL Checker → Concurrent HTTP Requests → Database Save
                    ↓
APScheduler (6AM, 2PM, 8PM UTC) → Check All Active URLs → Store Results
```

## Architectural Benefits

### Perfect for Free Tier Hosting
✅ **Lightweight**: Minimal dependencies, low memory usage
✅ **Single Process**: No complex microservices
✅ **No External Services**: SQLite eliminates need for separate database
✅ **Fast Startup**: Quick cold starts on Render
✅ **Resource Efficient**: <256MB RAM usage typical

### Simple & Reliable
✅ **Python**: Easy to develop, debug, and maintain
✅ **Flask**: Simple web framework, not overkill like Django
✅ **SQLite**: Zero configuration, reliable, handles target scale
✅ **Standard Libraries**: Minimal external dependencies

### Scalable Within Constraints
✅ **Concurrent Processing**: Handle 100+ URLs efficiently
✅ **Fast Execution**: Complete check cycles in 30-60 seconds
✅ **Optimized Queries**: Indexed database for quick lookups
✅ **Memory Management**: Efficient request handling

## File Structure

```
url-monitor/
├── monitor.py              # Main application entry point
├── src/
│   ├── __init__.py
│   ├── checker.py          # URL checking logic
│   ├── database.py         # Database operations  
│   ├── scheduler.py        # APScheduler integration
│   ├── dashboard.py        # Flask web interface
│   └── config.py           # Configuration management
├── templates/              # HTML templates
│   ├── base.html          # Base template with Bootstrap
│   ├── dashboard.html     # Main dashboard view
│   ├── history.html       # Historical data view
│   └── manage.html        # URL management interface
├── static/                 # CSS/JS assets
│   ├── css/
│   │   ├── style.css      # Custom styles
│   │   └── bootstrap.min.css
│   └── js/
│       ├── dashboard.js   # Dashboard interactions
│       └── chart.min.js   # Chart.js library
├── data/                   # Data directory
│   ├── monitor.db         # SQLite database
│   └── logs/              # Application logs
├── requirements.txt        # Python dependencies
├── config.json            # Application configuration
├── README.md              # User documentation
├── tech_stack.md          # This file
└── Documentation.md       # Complete technical docs
```

## Technology Decisions

### Framework Selection

#### Flask vs FastAPI vs Django
**Chosen: Flask**
- **Flask**: Lightweight, simple, perfect for small dashboard
- **FastAPI**: Async-first but overkill for our needs  
- **Django**: Too heavy, includes ORM we don't need

**Rationale**: Flask provides exactly what we need without bloat. The dashboard doesn't require complex async operations or heavy ORM features.

#### Database: SQLite vs PostgreSQL vs MySQL
**Chosen: SQLite**
- **SQLite**: File-based, no server needed, perfect for read-heavy workload
- **PostgreSQL**: Would require external service, more complex
- **MySQL**: Similar complexity to PostgreSQL

**Rationale**: SQLite eliminates the need for external database services, reducing complexity and cost while providing excellent performance for our scale.

#### Scheduling: APScheduler vs Cron vs Celery
**Chosen: APScheduler**
- **APScheduler**: Python-native, runs in-process
- **System Cron**: Would require external trigger setup
- **Celery**: Requires Redis/RabbitMQ, too complex

**Rationale**: APScheduler integrates seamlessly with Python applications and doesn't require additional infrastructure.

#### HTTP Client: Requests vs aiohttp vs urllib
**Chosen: Requests + Threading**
- **Requests**: Simple, reliable, well-documented
- **aiohttp**: Async but adds complexity
- **urllib**: Lower-level, more complex to use

**Rationale**: Requests with threading provides good concurrency without the complexity of async programming.

### What We're NOT Using (and why)

❌ **FastAPI**: Overkill for this use case, Flask is simpler
❌ **PostgreSQL/MySQL**: External database = complexity + potential costs
❌ **Redis**: No need for caching at this scale
❌ **Celery**: APScheduler is simpler for periodic tasks
❌ **React/Vue**: Plain HTML + Bootstrap is sufficient for dashboard needs
❌ **Docker**: Not needed for Render deployment
❌ **Microservices**: Single monolith is perfect for this scale
❌ **GraphQL**: REST API is simpler for basic CRUD operations
❌ **MongoDB**: No need for NoSQL complexity

## Deployment Architecture

### Render Free Tier
```
Internet → Render Load Balancer → Your Python App (Port 8080)
                                      ↓
                              APScheduler (Background Thread)
                                      ↓  
                              URL Checks (6AM, 2PM, 8PM UTC)
                                      ↓
                              SQLite Database (Persistent Volume)
```

### Alternative Deployment Options
- **Heroku**: Similar to Render setup
- **Railway**: Drop-in compatible
- **DigitalOcean App Platform**: Direct deployment
- **Traditional VPS**: systemd service + nginx
- **Docker**: Containerized deployment

## Resource Footprint

### Memory Usage Breakdown
| Component | Memory Usage |
|-----------|--------------|
| Base Python + Flask | 30-40MB |
| SQLite | 5-10MB |
| URL checking (per concurrent request) | 1-2MB |
| **Total Typical Usage** | **50-100MB** |

### CPU Usage Patterns
| Activity | CPU Usage | Duration |
|----------|-----------|----------|
| Idle (dashboard only) | Near 0% | Continuous |
| During URL checks | 10-30% | 30-60 seconds |
| Dashboard access | 1-5% | Per request |

### Storage Requirements
| Data Type | Storage Usage |
|-----------|---------------|
| Application code | ~10MB |
| SQLite database | 1-5MB per 1000 checks |
| Logs | ~1MB per month |
| **Total Growth** | **~5MB per month** |

## Scaling Characteristics

### URL Capacity by Resource Tier
| URLs | Memory | Check Duration | Monthly Storage |
|------|--------|----------------|-----------------|
| 2-10 | 50-80MB | 5-15 seconds | 1-5MB |
| 11-50 | 80-150MB | 15-45 seconds | 5-25MB |
| 51-100 | 150-250MB | 30-90 seconds | 25-50MB |
| 100+ | 250-500MB | 60-180 seconds | 50-100MB |

### Render Free Tier Limits
- **RAM**: 512MB available (we use <250MB for 100 URLs)
- **CPU**: Shared, adequate for periodic checking
- **Storage**: Persistent across deploys
- **Compute Hours**: 750/month (we use <2 hours/month)

## Security Considerations

### Application Security
- **Input validation** for all URLs
- **SQL injection protection** via parameterized queries
- **XSS protection** via Jinja2 auto-escaping
- **CSRF protection** for web forms
- **Rate limiting** for API endpoints

### Network Security
- **SSL/TLS verification** for outbound requests
- **Secure headers** in HTTP requests
- **Connection timeouts** to prevent hanging
- **User agent identification** for transparency

### Data Security
- **No sensitive data storage** (no passwords, tokens)
- **Secure logging** (sanitized URLs in logs)
- **Database permissions** (read-only access where possible)

## Performance Optimizations

### Database Optimizations
```sql
-- Indexed queries for fast lookups
CREATE INDEX idx_url_checks_url_id ON url_checks(url_id);
CREATE INDEX idx_url_checks_checked_at ON url_checks(checked_at);

-- SQLite optimizations
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA cache_size=10000;
```

### Concurrent Processing
```python
# Thread pool for concurrent URL checking
from concurrent.futures import ThreadPoolExecutor
from threading import BoundedSemaphore

# Limit concurrent connections
semaphore = BoundedSemaphore(20)

def check_urls_concurrently(urls):
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(check_url, url) for url in urls]
        return [future.result() for future in futures]
```

### Memory Management
- **Connection pooling** for HTTP requests
- **Database connection reuse**
- **Automatic cleanup** of old records
- **Efficient data structures** for in-memory operations

## Development Workflow

### Local Development Setup
```bash
# Clone repository
git clone https://github.com/username/url-monitor.git
cd url-monitor

# Setup virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Initialize database
python monitor.py --init

# Add test URLs
python monitor.py --add-url https://httpstat.us/200
python monitor.py --add-url https://httpstat.us/404

# Run development server
python monitor.py --dashboard --debug
```

### Testing Strategy
- **Unit tests** for individual components
- **Integration tests** for full workflow
- **Performance tests** for concurrent checking
- **Database tests** for data integrity

### Deployment Pipeline
1. **Code push** to GitHub
2. **Automated testing** (if CI/CD setup)
3. **Render auto-deploy** from main branch
4. **Health check verification**
5. **Rollback capability** if issues detected

## Future Scalability Options

### Horizontal Scaling Options
- **Multiple instances** with URL sharding
- **Load balancer** distribution
- **Database replication** for read scaling

### Vertical Scaling Paths
- **Paid hosting tiers** for more resources
- **Database upgrades** to PostgreSQL if needed
- **Caching layers** (Redis) for high-traffic scenarios

### Feature Extensions
- **API rate limiting** with Redis
- **Webhook notifications** for integrations
- **Multi-region checking** for geographic distribution
- **Advanced analytics** with time-series databases

## Conclusion

This technology stack is specifically designed to:

1. **Maximize functionality** within free hosting constraints
2. **Minimize complexity** for easy maintenance and debugging
3. **Provide clear upgrade paths** as requirements grow
4. **Ensure reliability** with battle-tested technologies
5. **Enable rapid development** with familiar tools

The chosen technologies work together to create a robust, efficient URL monitoring solution that can handle real-world workloads while staying within the resource limits of free hosting tiers.

---

**Last Updated**: January 2025
**Target Platform**: Render Free Tier (and compatible platforms)
**Recommended Python Version**: 3.9+