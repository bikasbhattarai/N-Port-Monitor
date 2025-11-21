from flask import Flask, render_template, redirect, url_for, request, jsonify
from station import (
    add_station_to_db,
    delete_station_from_db,
    edit_station_in_db,
    get_station_data,
    get_platform_data,
    get_sensor_data
)

from station import get_station_data, edit_station_in_db, get_db_connection

import sqlite3
import json
import urllib.parse

app = Flask(__name__)
app.debug = True

@app.route('/')
def index():
    try:
        conn = get_db_connection()
        stations = conn.execute('SELECT name FROM stations').fetchall()
        conn.close()
        if not stations:
            return render_template('index.html', stations=[])
        return render_template('index.html', stations=[s['name'] for s in stations])
    except Exception as e:
        app.logger.error(f"Failed to load stations: {e}")
        return "Error loading stations", 500


@app.route('/station/<name>')
def station(name):
    station_info = get_station_data(name)
    if station_info:
        return render_template('station.html', station_name=name, platforms=station_info)
    else:
        return f"Station {name} not found", 404

@app.route('/add_station', methods=['GET', 'POST'])
def add_station_page():
    if request.method == 'POST':
        name = request.form['name']
        platform_names = request.form.getlist('platform-name[]')

        platforms = {}
        for i, platform_name in enumerate(platform_names):
            sensor_names = request.form.getlist(f'sensor-name-{i}[]')
            sensor_ips = request.form.getlist(f'sensor-ip-{i}[]')
            sensor_ports = request.form.getlist(f'sensor-port-{i}[]')

            sensors = [
                {"sensor_name": sensor_names[j], "ip": sensor_ips[j], "port": sensor_ports[j], "status": "unknown", "history": []}
                for j in range(len(sensor_names))
            ]

            platforms[platform_name] = sensors

        add_station_to_db(name, platforms)
        return redirect(url_for('index'))
    
    return render_template('add_station.html')

@app.route('/history/<platform_name>/<sensor_name>')
def get_history(platform_name, sensor_name):
    platform_name = urllib.parse.unquote(platform_name)
    sensor_name = urllib.parse.unquote(sensor_name)

    history = get_sensor_data(platform_name, sensor_name).get('history', [])
    return jsonify(history)

@app.route('/edit_station/<station_name>', methods=['GET', 'POST'])
def edit_station(station_name):
    if request.method == 'POST':
        new_name = request.form['new_name']
        platforms = request.form.getlist('platforms')  # Assuming this is a list of platforms
        edit_station_in_db(station_name, new_name, platforms)
        return redirect(url_for('index'))  # Redirect to the index or another page

    # On GET request, fetch the station data
    station_data = get_station_data(station_name)
    return render_template('edit_station.html', station_data=station_data)
    
    
    
@app.route('/delete_station/<name>', methods=['POST'])
def delete_station_view(name):
    delete_station_from_db(name)
    return redirect(url_for('index'))

@app.route('/remove_platform', methods=['POST'])
def remove_platform():
    station_name = request.form.get('station_name')
    platform_name = request.form.get('platform_name')
    
    if get_platform_data(station_name, platform_name):
        remove_platform_from_db(station_name, platform_name)
        return jsonify({"success": True})
    return jsonify({"success": False}), 404

@app.route('/remove_sensor', methods=['POST'])
def remove_sensor():
    station_name = request.form.get('station_name')
    platform_name = request.form.get('platform_name')
    sensor_index = int(request.form.get('sensor_index'))

    if get_sensor_data(station_name, platform_name, sensor_index):
        remove_sensor_from_db(station_name, platform_name, sensor_index)
        return jsonify({"success": True})
    return jsonify({"success": False}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

