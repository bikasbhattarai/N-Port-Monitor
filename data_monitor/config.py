"""
Configuration settings for N-Port Monitor.

This module centralizes all configuration settings, loading from
environment variables with sensible defaults.
"""

import os
from pathlib import Path

# Base directory of the application
BASE_DIR = Path(__file__).parent.absolute()


class Config:
    """Base configuration class."""
    
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = False
    TESTING = False
    
    # Server settings
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    
    # Database settings
    DATABASE_PATH = os.getenv('DATABASE_PATH', str(BASE_DIR / 'stations.db'))
    
    # Monitoring settings
    SENSOR_TIMEOUT = int(os.getenv('SENSOR_TIMEOUT', 60))
    CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', 60))
    HISTORY_LIMIT = int(os.getenv('HISTORY_LIMIT', 100))
    MAX_WORKERS = int(os.getenv('MAX_WORKERS', 10))


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    
    # In production, ensure SECRET_KEY is set
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY environment variable must be set in production")


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DATABASE_PATH = ':memory:'


# Configuration mapping
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config():
    """Get configuration based on FLASK_ENV environment variable."""
    env = os.getenv('FLASK_ENV', 'development')
    return config_by_name.get(env, DevelopmentConfig)
