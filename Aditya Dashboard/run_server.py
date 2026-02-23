#!/usr/bin/env python3
"""
Weelocal Dashboard Server
Professional Flask web server for serving analytics dashboard with data API.

Endpoints:
  GET /                - Dashboard HTML
  GET /dashboard.html  - Dashboard (explicit)
  GET /ping            - Health check
  GET /data.json       - Analytics data JSON

Author: Weelocal Engineering
License: Proprietary
"""

import json
import logging
from pathlib import Path
from flask import Flask, jsonify

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask app configuration
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
PORT = 8000
HOST = '0.0.0.0'

# Get script directory
SCRIPT_DIR = Path(__file__).resolve().parent
DASHBOARD_FILE = SCRIPT_DIR / 'dashboard.html'
DATA_FILE = SCRIPT_DIR / 'data.json'

@app.route('/')
def index():
    """Serve the dashboard at root path."""
    try:
        if not DASHBOARD_FILE.exists():
            logger.error(f"Dashboard file not found: {DASHBOARD_FILE}")
            return jsonify({"error": "Dashboard not found"}), 404
        
        with open(DASHBOARD_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return content, 200, {'Content-Type': 'text/html; charset=utf-8'}
    except Exception as e:
        logger.error(f"Error serving dashboard: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/dashboard.html')
def dashboard():
    """Serve the dashboard HTML explicitly."""
    return index()


@app.route('/ping')
def ping():
    """Health check endpoint. Returns server status."""
    return jsonify({
        "status": "ok",
        "message": "Server is running",
        "service": "Weelocal Dashboard"
    }), 200


@app.route('/data.json')
def get_data():
    """Serve analytics data as JSON."""
    try:
        if not DATA_FILE.exists():
            logger.error(f"Data file not found: {DATA_FILE}")
            return jsonify({"error": f"Data file not found"}), 404
        
        # Load JSON data
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"Data served: {len(data)} keys")
        return jsonify(data), 200
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in data file: {e}")
        return jsonify({"error": "Invalid JSON data"}), 500
    except Exception as e:
        logger.error(f"Error serving data: {e}")
        return jsonify({"error": str(e)}), 500

def main():
    """Main entry point. Start Flask development server."""
    print(f"\n{'='*70}")
    print("WEELOCAL DASHBOARD SERVER")
    print(f"{'='*70}\n")
    print(f"Starting server on http://localhost:{PORT}")
    print(f"Host: {HOST}")
    print(f"Port: {PORT}")
    print(f"Debug: False")
    print(f"\nEndpoints:")
    print(f"  Dashboard: http://localhost:{PORT}/")
    print(f"  Health:    http://localhost:{PORT}/ping")
    print(f"  Data API:  http://localhost:{PORT}/data.json")
    print(f"\n{'='*70}")
    print("Press Ctrl+C to stop server")
    print(f"{'='*70}\n")
    
    try:
        app.run(
            host=HOST,
            port=PORT,
            debug=False,
            use_reloader=False,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n\n" + "="*70)
        print("Server stopped by user")
        print("="*70 + "\n")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise


if __name__ == '__main__':
    main()
