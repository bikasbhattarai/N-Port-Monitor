"""
Sensor monitoring module for N-Port Monitor.

This module handles:
- Real-time sensor connectivity checks
- Background monitoring threads
- Status updates and history tracking
"""

import logging
import socket
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any

from .config import get_config
from .database import get_all_sensors, update_sensor_status

logger = logging.getLogger(__name__)
config = get_config()

# Lock for thread-safe operations
_monitor_lock = threading.Lock()
_monitoring_active = False
_monitor_thread = None


def check_sensor(sensor: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check if a sensor is sending data on its IP and port.
    
    Args:
        sensor: Dictionary containing sensor info (ip, port, sensor_name, etc.)
        
    Returns:
        Updated sensor dictionary with new status.
    """
    ip = sensor['ip']
    port = int(sensor['port'])
    sensor_name = sensor['sensor_name']
    
    try:
        logger.debug(f"Checking {sensor_name} at {ip}:{port}")
        
        with socket.create_connection((ip, port), timeout=config.SENSOR_TIMEOUT) as sock:
            try:
                data = sock.recv(1024)
                if data:
                    status = 'green'
                    history_entry = 0  # OK
                    logger.info(f"✓ {sensor_name}: Data received from {ip}:{port}")
                else:
                    status = 'red'
                    history_entry = 1  # No data
                    logger.warning(f"✗ {sensor_name}: No data from {ip}:{port}")
            except socket.timeout:
                status = 'red'
                history_entry = 1
                logger.warning(f"✗ {sensor_name}: Timeout at {ip}:{port}")
                
    except socket.error as e:
        status = 'red'
        history_entry = 1
        logger.error(f"✗ {sensor_name}: Connection error at {ip}:{port} - {e}")
        
    except Exception as e:
        status = 'red'
        history_entry = 1
        logger.exception(f"✗ {sensor_name}: Unexpected error at {ip}:{port} - {e}")
    
    # Update database
    update_sensor_status(
        sensor['platform_name'],
        sensor_name,
        status,
        history_entry
    )
    
    return {**sensor, 'status': status}


def check_all_sensors() -> None:
    """
    Check all sensors in parallel using thread pool.
    """
    sensors = get_all_sensors()
    
    if not sensors:
        logger.debug("No sensors to check")
        return
    
    logger.info(f"Checking {len(sensors)} sensors...")
    
    with ThreadPoolExecutor(max_workers=config.MAX_WORKERS) as executor:
        futures = {executor.submit(check_sensor, sensor): sensor for sensor in sensors}
        
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                sensor = futures[future]
                logger.error(f"Error checking sensor {sensor['sensor_name']}: {e}")


def _monitoring_loop() -> None:
    """
    Main monitoring loop that runs in a background thread.
    """
    global _monitoring_active
    
    logger.info("Monitoring loop started")
    
    while _monitoring_active:
        try:
            check_all_sensors()
        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}")
        
        # Sleep in small intervals to allow quick shutdown
        for _ in range(config.CHECK_INTERVAL):
            if not _monitoring_active:
                break
            time.sleep(1)
    
    logger.info("Monitoring loop stopped")


def start_monitoring() -> None:
    """
    Start the background monitoring thread.
    """
    global _monitoring_active, _monitor_thread
    
    with _monitor_lock:
        if _monitoring_active:
            logger.warning("Monitoring is already running")
            return
        
        _monitoring_active = True
        _monitor_thread = threading.Thread(target=_monitoring_loop, daemon=True)
        _monitor_thread.start()
        logger.info("Background monitoring started")


def stop_monitoring() -> None:
    """
    Stop the background monitoring thread.
    """
    global _monitoring_active, _monitor_thread
    
    with _monitor_lock:
        if not _monitoring_active:
            logger.warning("Monitoring is not running")
            return
        
        _monitoring_active = False
        
        if _monitor_thread and _monitor_thread.is_alive():
            _monitor_thread.join(timeout=5)
        
        _monitor_thread = None
        logger.info("Background monitoring stopped")


def is_monitoring() -> bool:
    """
    Check if monitoring is currently active.
    
    Returns:
        True if monitoring is running, False otherwise.
    """
    return _monitoring_active
