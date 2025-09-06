#!/usr/bin/env python3
"""
Main entry point for Render deployment
"""

import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set production environment
os.environ['FLASK_ENV'] = 'production'

from backend.app import create_app

# Configure logging for production
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask application
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)