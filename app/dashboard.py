# FILE: app/dashboard.py (Updated)

"""
Flask Web Dashboard for URL Monitor
Provides a web interface and API to view monitoring status.
"""

import json
from flask import Flask, render_template, jsonify, url_for
from datetime import datetime

from app.config import get_config
from app.database import get_database

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    config = get_config()
    
    class CustomJSONEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            return super().default(obj)

    app.json_encoder = CustomJSONEncoder

    @app.template_filter('datetimeformat')
    def format_datetime(value, format="%Y-%m-%d %H:%M:%S"):
        if value is None:
            return ""
        if isinstance(value, str):
            value = datetime.fromisoformat(value)
        return value.strftime(format)
    
    @app.route('/')
    def index():
        """Dashboard homepage."""
        db = get_database()
        all_status = db.get_all_status()
        
        stats = {
            'total': len(all_status),
            'up': sum(1 for s in all_status if s.get('is_up')),
            'down': sum(1 for s in all_status if not s.get('is_up') and s.get('last_checked')),
            'pending': sum(1 for s in all_status if not s.get('last_checked'))
        }
        
        return render_template('index.html', statuses=all_status, stats=stats)

    @app.route('/history/<int:url_id>')
    def history(url_id):
        """Page to show detailed history for a single URL."""
        db = get_database()
        url_details = db.get_url(url_id)
        if not url_details:
            return "URL not found", 404
        
        check_history = db.get_url_history(url_id, days=7)
        return render_template('history.html', url_details=url_details, history=check_history)

    # --- API Routes ---
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
            "url_id": url.id,
            "url": url.url,
            "name": url.name,
            "history": history
        })

    return app