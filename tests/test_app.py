"""
Tests for N-Port Monitor application.

Run tests with: pytest tests/ -v
"""

import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_monitor.config import Config, DevelopmentConfig, TestingConfig
from data_monitor.database import init_db, add_station, get_station_data, delete_station


class TestConfig:
    """Test configuration settings."""
    
    def test_default_config(self):
        """Test default configuration values."""
        assert Config.SENSOR_TIMEOUT == 60
        assert Config.CHECK_INTERVAL == 60
        assert Config.HISTORY_LIMIT == 100
    
    def test_development_config(self):
        """Test development configuration."""
        assert DevelopmentConfig.DEBUG is True
    
    def test_testing_config(self):
        """Test testing configuration."""
        assert TestingConfig.TESTING is True
        assert TestingConfig.DATABASE_PATH == ':memory:'


class TestDatabase:
    """Test database operations."""
    
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Set up test database."""
        # Use temporary database for testing
        import data_monitor.config as config_module
        config_module.config.DATABASE_PATH = str(tmp_path / 'test.db')
        init_db()
    
    def test_add_and_get_station(self):
        """Test adding and retrieving a station."""
        platforms = {
            'Platform1': [
                {
                    'sensor_name': 'Sensor1',
                    'ip': '192.168.1.1',
                    'port': 8080,
                    'status': 'unknown',
                    'history': []
                }
            ]
        }
        
        result = add_station('TestStation', platforms)
        assert result is True
        
        station_data = get_station_data('TestStation')
        assert station_data is not None
        assert 'Platform1' in station_data
        assert len(station_data['Platform1']) == 1
        assert station_data['Platform1'][0]['sensor_name'] == 'Sensor1'
    
    def test_delete_station(self):
        """Test deleting a station."""
        platforms = {
            'Platform1': [
                {
                    'sensor_name': 'Sensor1',
                    'ip': '192.168.1.1',
                    'port': 8080,
                    'status': 'unknown',
                    'history': []
                }
            ]
        }
        
        add_station('ToDelete', platforms)
        result = delete_station('ToDelete')
        assert result is True
        
        station_data = get_station_data('ToDelete')
        assert station_data is None
    
    def test_duplicate_station(self):
        """Test adding duplicate station fails."""
        platforms = {
            'Platform1': [
                {
                    'sensor_name': 'Sensor1',
                    'ip': '192.168.1.1',
                    'port': 8080,
                    'status': 'unknown',
                    'history': []
                }
            ]
        }
        
        add_station('DuplicateTest', platforms)
        result = add_station('DuplicateTest', platforms)
        assert result is False


class TestMonitor:
    """Test monitoring functionality."""
    
    def test_sensor_check_format(self):
        """Test sensor data format."""
        sensor = {
            'sensor_name': 'TestSensor',
            'ip': '127.0.0.1',
            'port': 9999,
            'status': 'unknown',
            'history': []
        }
        
        # Verify required fields
        assert 'sensor_name' in sensor
        assert 'ip' in sensor
        assert 'port' in sensor
        assert 'status' in sensor
        assert 'history' in sensor
        
        # Verify types
        assert isinstance(sensor['port'], int)
        assert isinstance(sensor['history'], list)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
