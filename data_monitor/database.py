"""
Database operations for N-Port Monitor.

This module handles all database interactions including:
- Connection management
- Table creation and initialization
- CRUD operations for stations, platforms, and sensors
"""

import json
import logging
import sqlite3
from contextlib import contextmanager
from typing import Any, Dict, List, Optional

from .config import get_config

logger = logging.getLogger(__name__)
config = get_config()


@contextmanager
def get_db_connection():
    """
    Context manager for database connections.
    
    Yields:
        sqlite3.Connection: Database connection with Row factory enabled.
    
    Example:
        with get_db_connection() as conn:
            cursor = conn.execute("SELECT * FROM stations")
            stations = cursor.fetchall()
    """
    conn = None
    try:
        conn = sqlite3.connect(config.DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        yield conn
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {e}")
        raise
    finally:
        if conn:
            conn.close()


def init_db():
    """Initialize the database with required tables."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Create stations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create platforms table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS platforms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                station_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (station_id) REFERENCES stations (id) ON DELETE CASCADE
            )
        ''')
        
        # Create sensors table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sensors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform_id INTEGER NOT NULL,
                sensor_name TEXT NOT NULL,
                ip TEXT NOT NULL,
                port INTEGER NOT NULL,
                status TEXT DEFAULT 'unknown',
                history TEXT DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (platform_id) REFERENCES platforms (id) ON DELETE CASCADE
            )
        ''')
        
        # Create indexes for better query performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_platforms_station ON platforms(station_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sensors_platform ON sensors(platform_id)')
        
        conn.commit()
        logger.info("Database initialized successfully")


# =============================================================================
# Station Operations
# =============================================================================

def get_all_stations() -> List[str]:
    """
    Get names of all stations.
    
    Returns:
        List of station names.
    """
    with get_db_connection() as conn:
        cursor = conn.execute('SELECT name FROM stations ORDER BY name')
        return [row['name'] for row in cursor.fetchall()]


def get_station_data(station_name: str) -> Optional[Dict[str, Any]]:
    """
    Get complete data for a station including platforms and sensors.
    
    Args:
        station_name: Name of the station to retrieve.
        
    Returns:
        Dictionary with station data or None if not found.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Get station
        cursor.execute("SELECT id, name FROM stations WHERE name = ?", (station_name,))
        station = cursor.fetchone()
        
        if not station:
            return None
        
        station_id = station['id']
        
        # Get platforms
        cursor.execute(
            "SELECT id, name FROM platforms WHERE station_id = ? ORDER BY name",
            (station_id,)
        )
        platforms = cursor.fetchall()
        
        # Build platform data with sensors
        platforms_data = {}
        for platform in platforms:
            cursor.execute(
                """SELECT sensor_name, ip, port, status, history 
                   FROM sensors WHERE platform_id = ? ORDER BY sensor_name""",
                (platform['id'],)
            )
            sensors = cursor.fetchall()
            
            platforms_data[platform['name']] = [
                {
                    'sensor_name': s['sensor_name'],
                    'ip': s['ip'],
                    'port': s['port'],
                    'status': s['status'],
                    'history': json.loads(s['history'])
                }
                for s in sensors
            ]
        
        return platforms_data


def add_station(name: str, platforms: Dict[str, List[Dict]]) -> bool:
    """
    Add a new station with platforms and sensors.
    
    Args:
        name: Station name.
        platforms: Dictionary mapping platform names to list of sensors.
        
    Returns:
        True if successful, False otherwise.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Insert station
            cursor.execute("INSERT INTO stations (name) VALUES (?)", (name,))
            station_id = cursor.lastrowid
            
            # Insert platforms and sensors
            for platform_name, sensors in platforms.items():
                cursor.execute(
                    "INSERT INTO platforms (station_id, name) VALUES (?, ?)",
                    (station_id, platform_name)
                )
                platform_id = cursor.lastrowid
                
                for sensor in sensors:
                    cursor.execute('''
                        INSERT INTO sensors (platform_id, sensor_name, ip, port, status, history)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        platform_id,
                        sensor['sensor_name'],
                        sensor['ip'],
                        sensor['port'],
                        sensor.get('status', 'unknown'),
                        json.dumps(sensor.get('history', []))
                    ))
            
            conn.commit()
            logger.info(f"Station '{name}' added successfully")
            return True
            
    except sqlite3.IntegrityError:
        logger.error(f"Station '{name}' already exists")
        return False
    except Exception as e:
        logger.error(f"Failed to add station '{name}': {e}")
        return False


def delete_station(name: str) -> bool:
    """
    Delete a station and all associated platforms and sensors.
    
    Args:
        name: Station name to delete.
        
    Returns:
        True if successful, False otherwise.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get station ID
            cursor.execute("SELECT id FROM stations WHERE name = ?", (name,))
            station = cursor.fetchone()
            
            if not station:
                logger.warning(f"Station '{name}' not found")
                return False
            
            station_id = station['id']
            
            # Delete in order: sensors -> platforms -> station
            cursor.execute(
                "DELETE FROM sensors WHERE platform_id IN (SELECT id FROM platforms WHERE station_id = ?)",
                (station_id,)
            )
            cursor.execute("DELETE FROM platforms WHERE station_id = ?", (station_id,))
            cursor.execute("DELETE FROM stations WHERE id = ?", (station_id,))
            
            conn.commit()
            logger.info(f"Station '{name}' deleted successfully")
            return True
            
    except Exception as e:
        logger.error(f"Failed to delete station '{name}': {e}")
        return False


def update_station(old_name: str, new_name: str, platforms: Dict[str, List[Dict]]) -> bool:
    """
    Update a station's name, platforms, and sensors.
    
    Args:
        old_name: Current station name.
        new_name: New station name.
        platforms: Updated platform and sensor data.
        
    Returns:
        True if successful, False otherwise.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get station ID
            cursor.execute("SELECT id FROM stations WHERE name = ?", (old_name,))
            station = cursor.fetchone()
            
            if not station:
                logger.error(f"Station '{old_name}' not found")
                return False
            
            station_id = station['id']
            
            # Update station name
            if old_name != new_name:
                cursor.execute(
                    "UPDATE stations SET name = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (new_name, station_id)
                )
            
            # Delete existing platforms and sensors
            cursor.execute(
                "DELETE FROM sensors WHERE platform_id IN (SELECT id FROM platforms WHERE station_id = ?)",
                (station_id,)
            )
            cursor.execute("DELETE FROM platforms WHERE station_id = ?", (station_id,))
            
            # Insert updated platforms and sensors
            for platform_name, sensors in platforms.items():
                cursor.execute(
                    "INSERT INTO platforms (station_id, name) VALUES (?, ?)",
                    (station_id, platform_name)
                )
                platform_id = cursor.lastrowid
                
                for sensor in sensors:
                    cursor.execute('''
                        INSERT INTO sensors (platform_id, sensor_name, ip, port, status, history)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        platform_id,
                        sensor['sensor_name'],
                        sensor['ip'],
                        sensor['port'],
                        sensor.get('status', 'unknown'),
                        json.dumps(sensor.get('history', []))
                    ))
            
            conn.commit()
            logger.info(f"Station '{old_name}' updated successfully")
            return True
            
    except Exception as e:
        logger.error(f"Failed to update station '{old_name}': {e}")
        return False


# =============================================================================
# Platform Operations
# =============================================================================

def get_platform_data(station_name: str, platform_name: str) -> Optional[List[Dict]]:
    """
    Get all sensors for a specific platform.
    
    Args:
        station_name: Name of the station.
        platform_name: Name of the platform.
        
    Returns:
        List of sensor dictionaries or None if not found.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT s.sensor_name, s.ip, s.port, s.status, s.history
            FROM sensors s
            JOIN platforms p ON s.platform_id = p.id
            JOIN stations st ON p.station_id = st.id
            WHERE st.name = ? AND p.name = ?
            ORDER BY s.sensor_name
        """, (station_name, platform_name))
        
        sensors = cursor.fetchall()
        
        if not sensors:
            return None
        
        return [
            {
                'sensor_name': s['sensor_name'],
                'ip': s['ip'],
                'port': s['port'],
                'status': s['status'],
                'history': json.loads(s['history'])
            }
            for s in sensors
        ]


# =============================================================================
# Sensor Operations
# =============================================================================

def get_sensor_history(platform_name: str, sensor_name: str) -> List[int]:
    """
    Get history data for a specific sensor.
    
    Args:
        platform_name: Name of the platform.
        sensor_name: Name of the sensor.
        
    Returns:
        List of history values (0 = OK, 1 = Failed).
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT s.history
            FROM sensors s
            JOIN platforms p ON s.platform_id = p.id
            WHERE p.name = ? AND s.sensor_name = ?
        """, (platform_name, sensor_name))
        
        result = cursor.fetchone()
        
        if result:
            return json.loads(result['history'])
        return []


def update_sensor_status(platform_name: str, sensor_name: str, status: str, history_entry: int):
    """
    Update a sensor's status and history.
    
    Args:
        platform_name: Name of the platform.
        sensor_name: Name of the sensor.
        status: New status ('green', 'red', 'unknown').
        history_entry: History value to append (0 = OK, 1 = Failed).
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Get current history
        cursor.execute("""
            SELECT s.id, s.history
            FROM sensors s
            JOIN platforms p ON s.platform_id = p.id
            WHERE p.name = ? AND s.sensor_name = ?
        """, (platform_name, sensor_name))
        
        result = cursor.fetchone()
        
        if result:
            history = json.loads(result['history'])
            history.append(history_entry)
            
            # Keep history limited
            if len(history) > config.HISTORY_LIMIT:
                history = history[-config.HISTORY_LIMIT:]
            
            cursor.execute("""
                UPDATE sensors 
                SET status = ?, history = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (status, json.dumps(history), result['id']))
            
            conn.commit()


def get_all_sensors() -> List[Dict[str, Any]]:
    """
    Get all sensors from all platforms for monitoring.
    
    Returns:
        List of sensor dictionaries with platform and station info.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                st.name as station_name,
                p.name as platform_name,
                s.sensor_name,
                s.ip,
                s.port,
                s.status,
                s.history
            FROM sensors s
            JOIN platforms p ON s.platform_id = p.id
            JOIN stations st ON p.station_id = st.id
            ORDER BY st.name, p.name, s.sensor_name
        """)
        
        return [
            {
                'station_name': row['station_name'],
                'platform_name': row['platform_name'],
                'sensor_name': row['sensor_name'],
                'ip': row['ip'],
                'port': row['port'],
                'status': row['status'],
                'history': json.loads(row['history'])
            }
            for row in cursor.fetchall()
        ]
