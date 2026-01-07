#!/usr/bin/env python3
"""
N-Port Monitor - Application Entry Point

Run this script to start the monitoring server:
    python run.py

For development with auto-reload:
    FLASK_ENV=development python run.py
"""

import os
import sys
import logging

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_monitor import create_app, start_monitoring, get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for the application."""
    # Load configuration
    config = get_config()
    
    # Create Flask application
    app = create_app()
    
    # Start background monitoring
    logger.info("Starting background sensor monitoring...")
    start_monitoring()
    
    # Run the Flask server
    logger.info(f"Starting N-Port Monitor on http://{config.HOST}:{config.PORT}")
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                    N-Port Monitor v1.0.0                     ║
║                                                              ║
║   Server running at: http://{config.HOST}:{config.PORT:<24}   ║
║   Press Ctrl+C to stop                                       ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    try:
        app.run(
            host=config.HOST,
            port=config.PORT,
            debug=config.DEBUG,
            use_reloader=config.DEBUG
        )
    except KeyboardInterrupt:
        logger.info("Shutting down...")


if __name__ == '__main__':
    main()
