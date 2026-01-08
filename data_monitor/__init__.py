"""
N-Port Monitor - Real-time sensor monitoring system.

A Flask-based web application for monitoring N-Port sensor connections
with live status indicators and historical data visualization.
"""

__version__ = '1.0.0'
__author__ = 'Norwegian Meteorological Institute'

from .app import app, create_app
from .config import get_config
from .database import init_db
from .monitor import start_monitoring, stop_monitoring

__all__ = [
    'app',
    'create_app',
    'get_config',
    'init_db',
    'start_monitoring',
    'stop_monitoring'
]
