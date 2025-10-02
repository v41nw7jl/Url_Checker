# FILE: app/dashboard.py (Corrected Version)

"""
Flask Web Dashboard for URL Monitor
Provides a web interface and API to view monitoring status.
"""

import json
from flask import Flask, render_template, jsonify
from datetime import datetime

from app.config import get_config
from app.database import get_database

# --- CHANGE START ---
# We need to tell Flask where to find the 'templates' and 'static' folders,
# because they are in the project root, not inside the 'app' directory.
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
template_folder = os.path.join(project_root, 'templates')
static_folder = os.path.join(project_root, 'static')
# --- CHANGE END ---


def create_app():
    """Create and configure the Flask application."""
    # --- CHANGE START ---
    # Pass the correct folder paths to the Flask constructor
    app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)
    # --- CHANGE END ---
    
    config = get_config()
    
    class CustomJSONEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            return super().default(obj)

    app.json_encoder = CustomJSONEncoder

    # This is a helper function to make dates look nice in the template
    @app.template_filter('datetimeformat')
    def format_datetime(value, format="%Y-%m-%d %H:%M:%S"):
        """A custom Jinja filter to format datetime objects."""
        if value is None:
            return ""

        # Special case to handle the string 'now' for the current time
        if value == 'now':
            # Use UTC time to be consistent
            dt = datetime.utcnow()
            return dt.strftime(format)

        # Handle actual datetime objects or ISO strings from the database
        dt = value
        if isinstance(value, str):
            try:
                dt = datetime.fromisoformat(value)
            except ValueError:
                return value  # If it's not a valid date string, just return it as is

        return dt.strftime(format)


    @app.route('/')
    def index():
        """Dashboard homepage."""
        db = get_database()
        all_status = db.get_all_status()
        
        stats = {
            'total': len(all_status),
            'up': sum(1 for s in all_status if s.get('is_up')),
            'down': sum(1 for s in all_status if s.get('is_up') is False and s.get('checked_at')),
            'pending': sum(1 for s in all_status if s.get('last_checked') is None)
        }
        
        return render_template('index.html', statuses=all_status, stats=stats)

    @app.route('/api/status')
    def api_status():
        """JSON API endpoint for the status of all URLs."""
        db = get_database()
        all_status = db.get_all_status()
        return jsonify(all_status)

    @app.route('/api/history/<int:url_id>')
    def api_history(url_id: int):
        """JSON API endpoint for a specific URL's history."""
        db = get_database()
        url = db.get_url(url_id)
        if not url:
            return jsonify({"error": "URL not found"}), 404
        
        history = db.get_url_history(url_id, days=7)
        return jsonify({
            "url": url.url,
            "history": history
        })

    return app