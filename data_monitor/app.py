"""
Flask application for N-Port Monitor.

This module defines all web routes and handles HTTP requests.
"""

import logging
import urllib.parse
from flask import Flask, render_template, redirect, url_for, request, jsonify

from .config import get_config
from .database import (
    init_db,
    get_all_stations,
    get_station_data,
    add_station,
    delete_station,
    update_station,
    get_sensor_history,
    get_platform_data
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get configuration
config = get_config()

# Create Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY


# =============================================================================
# Error Handlers
# =============================================================================

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors."""
    return render_template('error.html', 
                          error_code=404, 
                          error_message="Page not found"), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {error}")
    return render_template('error.html', 
                          error_code=500, 
                          error_message="Internal server error"), 500


# =============================================================================
# Main Routes
# =============================================================================

@app.route('/')
def index():
    """Home page displaying all stations."""
    try:
        stations = get_all_stations()
        return render_template('index.html', stations=stations)
    except Exception as e:
        logger.error(f"Failed to load stations: {e}")
        return render_template('error.html',
                              error_code=500,
                              error_message="Error loading stations"), 500


@app.route('/station/<name>')
def station(name):
    """Display monitoring data for a specific station."""
    try:
        station_data = get_station_data(name)
        
        if station_data is None:
            logger.warning(f"Station '{name}' not found")
            return render_template('error.html',
                                  error_code=404,
                                  error_message=f"Station '{name}' not found"), 404
        
        return render_template('station.html', 
                              station_name=name, 
                              platforms=station_data)
    except Exception as e:
        logger.error(f"Error loading station '{name}': {e}")
        return render_template('error.html',
                              error_code=500,
                              error_message="Error loading station"), 500


# =============================================================================
# Station Management Routes
# =============================================================================

@app.route('/add_station', methods=['GET', 'POST'])
def add_station_page():
    """Add a new station."""
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            
            if not name:
                return render_template('add_station.html', 
                                      error="Station name is required")
            
            platform_names = request.form.getlist('platform-name[]')
            
            platforms = {}
            for i, platform_name in enumerate(platform_names):
                if not platform_name.strip():
                    continue
                    
                sensor_names = request.form.getlist(f'sensor-name-{i}[]')
                sensor_ips = request.form.getlist(f'sensor-ip-{i}[]')
                sensor_ports = request.form.getlist(f'sensor-port-{i}[]')
                
                sensors = []
                for j in range(len(sensor_names)):
                    if sensor_names[j].strip() and sensor_ips[j].strip() and sensor_ports[j].strip():
                        sensors.append({
                            'sensor_name': sensor_names[j].strip(),
                            'ip': sensor_ips[j].strip(),
                            'port': sensor_ports[j].strip(),
                            'status': 'unknown',
                            'history': []
                        })
                
                if sensors:
                    platforms[platform_name.strip()] = sensors
            
            if not platforms:
                return render_template('add_station.html',
                                      error="At least one platform with sensors is required")
            
            if add_station(name, platforms):
                logger.info(f"Station '{name}' created successfully")
                return redirect(url_for('index'))
            else:
                return render_template('add_station.html',
                                      error=f"Failed to create station. Station '{name}' may already exist.")
                                      
        except Exception as e:
            logger.error(f"Error creating station: {e}")
            return render_template('add_station.html',
                                  error="An error occurred while creating the station")
    
    return render_template('add_station.html')


@app.route('/edit_station/<name>', methods=['GET', 'POST'])
def edit_station(name):
    """Edit an existing station."""
    if request.method == 'POST':
        try:
            new_name = request.form.get('name', '').strip()
            
            if not new_name:
                station_data = get_station_data(name)
                return render_template('edit_station.html',
                                      station_name=name,
                                      platforms=station_data,
                                      error="Station name is required")
            
            platform_names = request.form.getlist('platform-name[]')
            
            platforms = {}
            for i, platform_name in enumerate(platform_names):
                if not platform_name.strip():
                    continue
                    
                sensor_names = request.form.getlist(f'sensor-name-{i}[]')
                sensor_ips = request.form.getlist(f'sensor-ip-{i}[]')
                sensor_ports = request.form.getlist(f'sensor-port-{i}[]')
                
                sensors = []
                for j in range(len(sensor_names)):
                    if sensor_names[j].strip() and sensor_ips[j].strip() and sensor_ports[j].strip():
                        sensors.append({
                            'sensor_name': sensor_names[j].strip(),
                            'ip': sensor_ips[j].strip(),
                            'port': sensor_ports[j].strip(),
                            'status': 'unknown',
                            'history': []
                        })
                
                if sensors:
                    platforms[platform_name.strip()] = sensors
            
            if update_station(name, new_name, platforms):
                logger.info(f"Station '{name}' updated successfully")
                return redirect(url_for('index'))
            else:
                station_data = get_station_data(name)
                return render_template('edit_station.html',
                                      station_name=name,
                                      platforms=station_data,
                                      error="Failed to update station")
                                      
        except Exception as e:
            logger.error(f"Error updating station '{name}': {e}")
            station_data = get_station_data(name)
            return render_template('edit_station.html',
                                  station_name=name,
                                  platforms=station_data,
                                  error="An error occurred while updating the station")
    
    # GET request
    station_data = get_station_data(name)
    
    if station_data is None:
        return render_template('error.html',
                              error_code=404,
                              error_message=f"Station '{name}' not found"), 404
    
    return render_template('edit_station.html',
                          station_name=name,
                          platforms=station_data)


@app.route('/delete_station/<name>', methods=['POST'])
def delete_station_route(name):
    """Delete a station."""
    try:
        if delete_station(name):
            logger.info(f"Station '{name}' deleted successfully")
        else:
            logger.warning(f"Failed to delete station '{name}'")
    except Exception as e:
        logger.error(f"Error deleting station '{name}': {e}")
    
    return redirect(url_for('index'))


# =============================================================================
# API Routes
# =============================================================================

@app.route('/api/history/<platform_name>/<sensor_name>')
def get_history(platform_name, sensor_name):
    """Get sensor history data as JSON."""
    try:
        platform_name = urllib.parse.unquote(platform_name)
        sensor_name = urllib.parse.unquote(sensor_name)
        
        history = get_sensor_history(platform_name, sensor_name)
        return jsonify(history)
        
    except Exception as e:
        logger.error(f"Error getting history for {platform_name}/{sensor_name}: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/stations')
def api_stations():
    """Get all stations as JSON."""
    try:
        stations = get_all_stations()
        return jsonify(stations)
    except Exception as e:
        logger.error(f"Error getting stations: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/station/<name>')
def api_station(name):
    """Get station data as JSON."""
    try:
        station_data = get_station_data(name)
        
        if station_data is None:
            return jsonify({'error': 'Station not found'}), 404
        
        return jsonify(station_data)
        
    except Exception as e:
        logger.error(f"Error getting station '{name}': {e}")
        return jsonify({'error': str(e)}), 500


# =============================================================================
# Application Factory
# =============================================================================

def create_app():
    """
    Application factory for creating Flask app instance.
    
    Returns:
        Configured Flask application.
    """
    # Initialize database
    init_db()
    
    return app
