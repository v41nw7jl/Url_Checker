# URL Monitor

A lightweight, serverless-style URL monitoring application designed for free-tier hosting platforms like Render. Monitors website availability with minimal resource usage while providing comprehensive status tracking and reporting.

## 🚀 Features

- **Serverless-style execution** - Runs periodically then exits (perfect for free hosting)
- **Resource optimized** - Uses <1% of free tier limits on most platforms
- **Concurrent checking** - Fast parallel URL processing
- **Historical tracking** - Complete check history with timestamps
- **Web dashboard** - Clean interface to view status and trends
- **CLI management** - Easy command-line URL management
- **Flexible scheduling** - Configurable check times
- **SQLite database** - No external database required
- **Response time monitoring** - Track performance over time

## 📋 Requirements

- Python 3.8+
- SQLite3 (included with Python)
- Internet connection

## 🔧 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/url-monitor.git
cd url-monitor
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Initialize the Application
```bash
python monitor.py --init
```

## 🚀 Quick Start

### Add URLs to Monitor
```bash
# Add your first URLs
python monitor.py --add-url https://google.com
python monitor.py --add-url https://github.com
```

### Run a Check
```bash
# Manual check of all URLs
python monitor.py --run-check
```

### View Status
```bash
# CLI status report
python monitor.py --status

# Start web dashboard
python monitor.py --dashboard
# Visit http://localhost:8080
```

### Scheduled Monitoring
```bash
# Run with built-in scheduler (6 AM, 2 PM, 8 PM UTC)
python monitor.py --schedule
```

## 🕐 Default Schedule

The application runs checks **3 times daily** by default:
- **06:00 UTC** (Early morning check)
- **14:00 UTC** (Afternoon peak check)  
- **20:00 UTC** (Evening check)

**Detection Window:** Issues are detected within 4-10 hours maximum.

## 📊 Resource Usage

Optimized for free hosting tiers:

| URLs | Time per Run | Daily Usage | Monthly Usage |
|------|-------------|-------------|---------------|
| 2    | ~5 seconds  | 15 seconds  | 8 minutes     |
| 10   | ~10 seconds | 30 seconds  | 15 minutes    |
| 50   | ~30 seconds | 90 seconds  | 45 minutes    |
| 100  | ~60 seconds | 180 seconds | 90 minutes    |

*Well within free tier limits (usually 750+ hours/month available)*

## 🖥️ Web Dashboard

Access the dashboard at `http://localhost:8080` when running:

### Features:
- **Status Overview** - Current up/down status of all URLs
- **Response Time Charts** - Performance trends over time
- **Recent Activity** - Last 24 hours of checks
- **Historical Data** - Weekly/monthly summaries
- **URL Management** - Add/remove URLs via web interface

### Screenshots:
```
┌─────────────────────────────────────┐
│ URL Monitor Dashboard               │
├─────────────────────────────────────┤
│ ✅ https://google.com     (127ms)   │
│ ❌ https://example-down.com (timeout)│
│ ✅ https://github.com     (89ms)    │
├─────────────────────────────────────┤
│ Total: 3 URLs | Up: 2 | Down: 1     │
│ Last Check: 2 minutes ago           │
└─────────────────────────────────────┘
```

## 🔧 CLI Commands

### URL Management
```bash
# Add URL
python monitor.py --add-url https://example.com

# List all URLs
python monitor.py --list-urls

# Remove URL
python monitor.py --remove-url https://example.com

# Check single URL
python monitor.py --check-url https://example.com
```

### Monitoring
```bash
# Run single check cycle
python monitor.py --run-check

# View status summary
python monitor.py --status

# View detailed history
python monitor.py --history --days 7

# Start scheduled monitoring
python monitor.py --schedule
```

### Dashboard
```bash
# Start web dashboard on default port (8080)
python monitor.py --dashboard

# Custom port
python monitor.py --dashboard --port 3000

# Dashboard with scheduled checks
python monitor.py --dashboard --schedule
```

## ⚙️ Configuration

### config.json
```json
{
  "schedules": ["06:00", "14:00", "20:00"],
  "timezone": "UTC",
  "request_timeout": 10,
  "concurrent_limit": 20,
  "database_path": "monitor.db",
  "dashboard_port": 8080,
  "retention_days": 30
}
```

### Environment Variables
```bash
# Override config file location
export MONITOR_CONFIG="/path/to/config.json"

# Set timezone
export MONITOR_TIMEZONE="America/New_York"

# Dashboard port
export MONITOR_PORT=3000
```

## 🚢 Deployment

### Render (Recommended for Free Tier)

1. **Fork this repository** to your GitHub account

2. **Create new Web Service** on Render:
   - Connect your GitHub repository
   - Build command: `pip install -r requirements.txt`
   - Start command: `python monitor.py --dashboard --schedule`

3. **Add URLs via CLI** (one-time setup):
   ```bash
   # SSH into your Render instance or use local CLI
   python monitor.py --add-url https://your-website.com
   ```

4. **Access your dashboard** at `https://your-app.onrender.com`

### Alternative: External Cron Trigger
For even lower resource usage, use external cron service:

1. **Deploy as web service** with endpoint `/run-check`
2. **Setup external cron** (e.g., cron-job.org) to hit your endpoint:
   - `6:00 UTC`: `GET https://your-app.onrender.com/run-check`
   - `14:00 UTC`: `GET https://your-app.onrender.com/run-check`  
   - `20:00 UTC`: `GET https://your-app.onrender.com/run-check`

### Docker Deployment
```bash
# Build
docker build -t url-monitor .

# Run with volume for persistence
docker run -d -p 8080:8080 -v $(pwd)/data:/app/data url-monitor
```

### Other Platforms
- **Heroku**: Use `Procfile` with web and scheduler dynos
- **Railway**: Similar to Render setup
- **DigitalOcean App Platform**: Deploy as web service
- **AWS Lambda**: Convert to serverless functions (advanced)

## 📁 Project Structure

```
url-monitor/
├── monitor.py          # Main application
├── requirements.txt    # Python dependencies
├── config.json         # Configuration file
├── README.md          # This file
├── docs/              # Additional documentation
│   └── API.md         # API documentation
├── templates/         # Web dashboard templates
│   ├── index.html     # Dashboard home
│   └── history.html   # Historical data view
├── static/           # CSS/JS for dashboard
│   ├── style.css     # Dashboard styles
│   └── app.js        # Dashboard JavaScript
├── data/             # Data directory
│   ├── monitor.db    # SQLite database
│   └── logs/         # Log files
└── tests/            # Unit tests
    └── test_monitor.py
```

## 🔍 API Endpoints

When running with `--dashboard`, the following endpoints are available:

- `GET /` - Dashboard homepage
- `GET /api/status` - JSON status of all URLs
- `GET /api/history/<url>` - Historical data for specific URL
- `POST /api/urls` - Add new URL
- `DELETE /api/urls/<id>` - Remove URL
- `POST /run-check` - Trigger manual check

## 📈 Monitoring Best Practices

1. **Start Small**: Begin with 2-5 critical URLs
2. **Monitor Gradual Growth**: Add URLs as needed
3. **Check Resource Usage**: Monitor your hosting platform's metrics
4. **Review History**: Weekly review of trends and patterns
5. **Cleanup Old Data**: Regularly archive historical data if needed

## 🔧 Customization

### Custom Check Schedules
Edit `config.json` to modify check times:
```json
{
  "schedules": ["03:00", "09:00", "15:00", "21:00"],
  "timezone": "America/New_York"
}
```

### Custom Timeouts and Limits
```json
{
  "request_timeout": 30,
  "concurrent_limit": 10,
  "retry_attempts": 3
}
```

### Dashboard Customization
Modify templates in `templates/` directory and styles in `static/style.css`.

## 🐛 Troubleshooting

### Common Issues

**URLs not being checked:**
```bash
# Verify URLs are active
python monitor.py --list-urls

# Test single URL
python monitor.py --check-url https://example.com
```

**Database issues:**
```bash
# Reinitialize database
python monitor.py --init --force

# Check database integrity
python monitor.py --verify-db
```

**Dashboard not accessible:**
```bash
# Check if port is available
python monitor.py --dashboard --port 3000

# View logs
python monitor.py --logs
```

## 📝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Support

- **Issues**: [GitHub Issues](https://github.com/your-username/url-monitor/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/url-monitor/discussions)
- **Documentation**: See `docs/` directory for detailed guides

## 🙏 Acknowledgments

- Built for developers who need reliable monitoring on free hosting tiers
- Inspired by the need for simple, effective website monitoring
- Optimized for modern free hosting platforms like Render, Railway, and Heroku

---

**Made with ❤️ for the developer community**

*Perfect for startups, side projects, and anyone who needs reliable monitoring without the enterprise cost.*