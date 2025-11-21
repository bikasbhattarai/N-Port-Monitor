import json
import os
import socket
import threading
import time
import concurrent.futures
import logging
import sqlite3

logging.basicConfig(level=logging.INFO)

# Reduce timeout to make the monitoring faster
TIMEOUT = 60  # 60-second timeout

# Define the path to the JSON file and the text file for default data
STATIONS_FILE = os.path.abspath('stations.json')
DEFAULT_STATIONS_FILE = os.path.abspath('station_data.txt')


def connect_db():
    """Create and return a connection to the SQLite database."""
    return sqlite3.connect('stations.db')

def get_db_connection():
    conn = sqlite3.connect('stations.db')
    conn.row_factory = sqlite3.Row
    return conn
  
def check_tables():
    conn = sqlite3.connect('stations.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    conn.close()
    return tables

print(check_tables())



def create_tables():
    conn = sqlite3.connect('stations.db')
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS stations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS platforms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        station_id INTEGER,
        name TEXT NOT NULL,
        FOREIGN KEY (station_id) REFERENCES stations (id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sensors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        platform_id INTEGER,
        sensor_name TEXT NOT NULL,
        ip TEXT NOT NULL,
        port INTEGER NOT NULL,
        status TEXT,
        history TEXT,
        FOREIGN KEY (platform_id) REFERENCES platforms (id)
    )
    ''')

    conn.commit()
    conn.close()

    
def load_default_stations():
    """Load default station data from a text file."""
    if os.path.exists(DEFAULT_STATIONS_FILE):
        logging.info(f"Default data file found at {DEFAULT_STATIONS_FILE}. Loading default stations.")
        try:
            with open(DEFAULT_STATIONS_FILE, 'r') as f:
                default_stations = json.load(f)
                logging.info(f"Default stations loaded from {DEFAULT_STATIONS_FILE}")
                return default_stations
        except Exception as e:
            logging.error(f"Failed to load default stations: {e}")
            return {}
    else:
        logging.warning(f"No default data file found at {DEFAULT_STATIONS_FILE}.")
        return {}


def load_stations():
    """Load station data from the SQLite database or return an empty dictionary if the database is empty or cannot be accessed."""
    conn = None
    try:
        conn = sqlite3.connect('stations.db')
        cursor = conn.cursor()

        # Query to get all stations
        cursor.execute("SELECT id, name FROM stations")
        stations_rows = cursor.fetchall()

        if not stations_rows:
            logging.warning("No stations found in the database.")

        stations = {}
        for station_id, station_name in stations_rows:
            # Query to get platforms for each station
            cursor.execute("SELECT id, name FROM platforms WHERE station_id = ?", (station_id,))
            platforms_rows = cursor.fetchall()

            platforms = {}
            for platform_id, platform_name in platforms_rows:
                # Query to get sensors for each platform
                cursor.execute("SELECT sensor_name, ip, port, status, history FROM sensors WHERE platform_id = ?", (platform_id,))
                sensors_rows = cursor.fetchall()

                sensors = []
                for sensor_name, ip, port, status, history in sensors_rows:
                    sensors.append({
                        'sensor_name': sensor_name,
                        'ip': ip,
                        'port': port,
                        'status': status,
                        'history': json.loads(history)  # Convert JSON string back to list
                    })

                platforms[platform_name] = sensors

            stations[station_name] = platforms

        logging.info(f"Loaded stations: {stations}")

        return stations

    except Exception as e:
        logging.error(f"Failed to load stations: {e}")
        return {}
    
    finally:
        if conn:
            conn.close()
            
            
def save_stations(stations):
    """Save the current station data to the SQLite database."""
    conn = None
    try:
        conn = sqlite3.connect('stations.db')
        cursor = conn.cursor()

        # Delete existing data
        cursor.execute("DELETE FROM sensors")
        cursor.execute("DELETE FROM platforms")
        cursor.execute("DELETE FROM stations")

        for station_name, platforms in stations.items():
            # Insert station
            cursor.execute("INSERT INTO stations (name) VALUES (?)", (station_name,))
            station_id = cursor.lastrowid

            for platform_name, sensors in platforms.items():
                # Insert platform
                cursor.execute("INSERT INTO platforms (station_id, name) VALUES (?, ?)", (station_id, platform_name))
                platform_id = cursor.lastrowid

                for sensor in sensors:
                    # Insert sensor
                    cursor.execute('''
                    INSERT OR REPLACE INTO sensors (platform_id, sensor_name, ip, port, status, history) 
                    VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        platform_id, 
                        sensor['sensor_name'], 
                        sensor['ip'], 
                        sensor['port'], 
                        sensor['status'], 
                        json.dumps(sensor['history'])  # Convert list to JSON string
                    ))

        conn.commit()
        logging.info("Stations successfully saved to the SQLite database")
        
    except Exception as e:
        logging.error(f"Failed to save stations: {e}")

    finally:
        if conn:
            conn.close()

# Load stations from the JSON file or use default data if the file doesn't exist
stations = load_stations()


def add_station(station_name, platform_data):
    """Add a new station with platforms and sensors."""
    conn = None
    try:
        conn = connect_db()
        cursor = conn.cursor()

        # Insert station
        cursor.execute("INSERT INTO stations (name) VALUES (?)", (station_name,))
        station_id = cursor.lastrowid

        for platform_name, sensors in platform_data.items():
            # Insert platform
            cursor.execute("INSERT INTO platforms (station_id, name) VALUES (?, ?)", (station_id, platform_name))
            platform_id = cursor.lastrowid

            for sensor in sensors:
                # Insert sensor
                cursor.execute('''
                INSERT INTO sensors (platform_id, sensor_name, ip, port, status, history) 
                VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    platform_id, 
                    sensor['sensor_name'], 
                    sensor['ip'], 
                    sensor['port'], 
                    sensor['status'], 
                    json.dumps(sensor['history'])
                ))

        conn.commit()
        logging.info(f"Station '{station_name}' added successfully")

    except Exception as e:
        logging.error(f"Failed to add station '{station_name}': {e}")

    finally:
        if conn:
            conn.close()

def delete_station(station_name):
    """Delete a station and all associated platforms and sensors."""
    conn = None
    try:
        conn = connect_db()
        cursor = conn.cursor()

        # Check if the station exists
        cursor.execute("SELECT id FROM stations WHERE name = ?", (station_name,))
        station_row = cursor.fetchone()
        if not station_row:
            raise ValueError(f"Station '{station_name}' does not exist")

        station_id = station_row[0]

        # Delete associated sensors and platforms
        cursor.execute("DELETE FROM sensors WHERE platform_id IN (SELECT id FROM platforms WHERE station_id = ?)", (station_id,))
        cursor.execute("DELETE FROM platforms WHERE station_id = ?", (station_id,))
        cursor.execute("DELETE FROM stations WHERE id = ?", (station_id,))

        conn.commit()
        logging.info(f"Station '{station_name}' deleted successfully")

    except Exception as e:
        logging.error(f"Failed to delete station '{station_name}': {e}")

    finally:
        if conn:
            conn.close()
            
            

def edit_station(station_name, new_name, new_platform_data):
    """Edit an existing station's name, platforms, and sensors."""
    conn = None
    try:
        conn = connect_db()
        cursor = conn.cursor()

        # Check if the station exists
        cursor.execute("SELECT id FROM stations WHERE name = ?", (station_name,))
        station_row = cursor.fetchone()
        if not station_row:
            raise ValueError(f"Station '{station_name}' does not exist")

        station_id = station_row[0]

        # Update station name if changed
        if station_name != new_name:
            cursor.execute("UPDATE stations SET name = ? WHERE id = ?", (new_name, station_id))

        # Delete existing platforms and sensors
        cursor.execute("DELETE FROM sensors WHERE platform_id IN (SELECT id FROM platforms WHERE station_id = ?)", (station_id,))
        cursor.execute("DELETE FROM platforms WHERE station_id = ?", (station_id,))

        # Insert new platforms and sensors
        for platform_name, sensors in new_platform_data.items():
            cursor.execute("INSERT INTO platforms (station_id, name) VALUES (?, ?)", (station_id, platform_name))
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
                    sensor['status'], 
                    json.dumps(sensor['history'])
                ))

        conn.commit()
        logging.info(f"Station '{station_name}' updated successfully")

    except Exception as e:
        logging.error(f"Failed to update station '{station_name}': {e}")

    finally:
        if conn:
            conn.close()
            
def get_station_data(station_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get station ID
    cursor.execute("SELECT id FROM stations WHERE name = ?", (station_name,))
    station_id = cursor.fetchone()
    if not station_id:
        conn.close()
        return {"error": "Station not found"}
    station_id = station_id[0]
    
    # Get platforms and sensors
    cursor.execute("SELECT id, name FROM platforms WHERE station_id = ?", (station_id,))
    platforms = cursor.fetchall()
    
    platform_data = []
    for platform in platforms:
        platform_id = platform[0]
        cursor.execute("SELECT sensor_name, ip, port, status, history FROM sensors WHERE platform_id = ?", (platform_id,))
        sensors = cursor.fetchall()
        sensors_list = [
            {
                "sensor_name": sensor[0],
                "ip": sensor[1],
                "port": sensor[2],
                "status": sensor[3],
                "history": json.loads(sensor[4])  # Convert JSON string back to list
            }
            for sensor in sensors
        ]
        platform_data.append({
            "id": platform_id,
            "name": platform[1],
            "sensors": sensors_list
        })
    
    conn.close()
    return {
        "station_name": station_name,
        "platforms": platform_data
    }

def add_station_to_db(name, platforms):
    conn = sqlite3.connect('stations.db')
    cursor = conn.cursor()

    cursor.execute("INSERT INTO stations (name) VALUES (?)", (name,))
    station_id = cursor.lastrowid

    for platform_name, sensors in platforms.items():
        cursor.execute("INSERT INTO platforms (station_id, name) VALUES (?, ?)", (station_id, platform_name))
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
                sensor['status'], 
                json.dumps(sensor['history'])  # Convert list to JSON string
            ))
    conn.commit()
    conn.close()

def delete_station_from_db(name):
    conn = sqlite3.connect('stations.db')
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM stations WHERE name = ?", (name,))
    station_id = cursor.fetchone()
    if not station_id:
        conn.close()
        return
    station_id = station_id[0]

    cursor.execute("DELETE FROM sensors WHERE platform_id IN (SELECT id FROM platforms WHERE station_id = ?)", (station_id,))
    cursor.execute("DELETE FROM platforms WHERE station_id = ?", (station_id,))
    cursor.execute("DELETE FROM stations WHERE id = ?", (station_id,))
    conn.commit()
    conn.close()

def edit_station_in_db(old_name, new_name, platforms):
    if old_name != new_name:
        # Update station name logic
        pass

    # Add or update platforms and sensors
    for platform_name, sensors in platforms.items():
        current_sensors = get_platform_data(old_name, platform_name)
        
        if not current_sensors:
            # Add new platform if not exists
            add_platform_to_db(new_name, platform_name)

        for sensor_index, sensor in enumerate(sensors):
            sensor_name = sensor["sensor_name"]
            current_sensor = get_sensor_data(new_name, platform_name, sensor_index)

            if not current_sensor:
                # Add new sensor
                add_sensor_to_db(new_name, platform_name, sensor)
            else:
                # Update existing sensor
                update_sensor_in_db(new_name, platform_name, sensor)

    # Logic to remove unused platforms and sensors
    current_platforms = get_all_platforms_for_station(new_name)
    for platform in current_platforms:
        if platform not in platforms:
            remove_platform_from_db(new_name, platform)

    for platform_name, sensors in platforms.items():
        current_sensors = get_all_sensors_for_platform(new_name, platform_name)
        for sensor in current_sensors:
            if sensor["sensor_name"] not in [s["sensor_name"] for s in sensors]:
                remove_sensor_from_db(new_name, platform_name, sensor["sensor_name"])


def remove_platform_from_db(station_name, platform_name):
    conn = None
    try:
        conn = connect_db()
        cursor = conn.cursor()

        # Get platform ID
        cursor.execute("SELECT id FROM platforms WHERE station_id = (SELECT id FROM stations WHERE name = ?) AND name = ?", (station_name, platform_name))
        platform_row = cursor.fetchone()
        if not platform_row:
            raise ValueError(f"Platform '{platform_name}' does not exist")

        platform_id = platform_row[0]

        # Delete associated sensors
        cursor.execute("DELETE FROM sensors WHERE platform_id = ?", (platform_id,))
        # Delete platform
        cursor.execute("DELETE FROM platforms WHERE id = ?", (platform_id,))

        conn.commit()
        logging.info(f"Platform '{platform_name}' removed from station '{station_name}'")

    except Exception as e:
        logging.error(f"Failed to remove platform '{platform_name}' from station '{station_name}': {e}")

    finally:
        if conn:
            conn.close()

def remove_sensor_from_db(station_name, platform_name, sensor_index):
    conn = None
    try:
        conn = connect_db()
        cursor = conn.cursor()

        # Get platform ID
        cursor.execute("SELECT id FROM platforms WHERE station_id = (SELECT id FROM stations WHERE name = ?) AND name = ?", (station_name, platform_name))
        platform_row = cursor.fetchone()
        if not platform_row:
            raise ValueError(f"Platform '{platform_name}' does not exist")

        platform_id = platform_row[0]

        # Get sensor ID
        cursor.execute("SELECT id FROM sensors WHERE platform_id = ? LIMIT 1 OFFSET ?", (platform_id, sensor_index))
        sensor_row = cursor.fetchone()
        if not sensor_row:
            raise ValueError("Sensor does not exist")

        sensor_id = sensor_row[0]

        # Delete sensor
        cursor.execute("DELETE FROM sensors WHERE id = ?", (sensor_id,))

        conn.commit()
        logging.info(f"Sensor removed from platform '{platform_name}' in station '{station_name}'")

    except Exception as e:
        logging.error(f"Failed to remove sensor from platform '{platform_name}' in station '{station_name}': {e}")

    finally:
        if conn:
            conn.close()


def get_platform_data(station_name, platform_name):
    conn = sqlite3.connect('stations.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM stations WHERE name = ?", (station_name,))
    station_id = cursor.fetchone()
    if not station_id:
        conn.close()
        return None
    station_id = station_id[0]

    cursor.execute("SELECT id FROM platforms WHERE station_id = ? AND name = ?", (station_id, platform_name))
    platform_id = cursor.fetchone()
    if not platform_id:
        conn.close()
        return None
    platform_id = platform_id[0]

    cursor.execute("SELECT sensor_name, ip, port, status, history FROM sensors WHERE platform_id = ?", (platform_id,))
    sensors = cursor.fetchall()
    sensor_list = [
        {
            "sensor_name": sensor[0],
            "ip": sensor[1],
            "port": sensor[2],
            "status": sensor[3],
            "history": json.loads(sensor[4])  # Convert JSON string back to list
        }
        for sensor in sensors
    ]
    conn.close()
    return sensor_list

def get_sensor_data(station_name, platform_name, sensor_index):
    sensor_index = int(sensor_index)  # Ensure sensor_index is an integer

    # Retrieve the platform data (which is a list of sensors)
    sensors = get_platform_data(station_name, platform_name)
    if sensors and 0 <= sensor_index < len(sensors):
        return sensors[sensor_index]
    return None   
    
    
def update_sensor_in_db(station_name, platform_name, sensor_data):
    """
    Updates an existing sensor's data in the database.

    Args:
        station_name (str): The name of the station.
        platform_name (str): The name of the platform.
        sensor_data (dict): A dictionary containing sensor details like sensor_name, ip, and port.

    Returns:
        None
    """
    # Retrieve the existing platform data
    platforms = get_station_data(station_name)["platforms"]
    
    for platform in platforms:
        if platform["platform_name"] == platform_name:
            for sensor in platform["sensors"]:
                if sensor["sensor_name"] == sensor_data["sensor_name"]:
                    # Update the sensor's details
                    sensor["ip"] = sensor_data["ip"]
                    sensor["port"] = sensor_data["port"]
                    break

    # Save the updated station data
    save_station_data(station_name, platforms)    
    
def get_db_connection():
    conn = sqlite3.connect('stations.db')  # Update this path as necessary
    conn.row_factory = sqlite3.Row
    return conn
    
    
    
def get_station_data(station_name):
    # Example function body, replace with your actual logic
    data = {
        # "platforms" should be a key here if platforms are part of the data
    }
    print("DEBUG: Station Data:", data)  # Add this line for debugging
    return data
#---------------------------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------------------V
#---------------------------------------------------------------------------------------------------------------------------
###################################### Data Monitoring Part ##############################################################
#---------------------------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------------------


# Lock for synchronizing access to sensor data
sensor_lock = threading.Lock()

def check_port(sensor):
    """Check if data is flowing on the specified IP and port."""
    ip = sensor["ip"]
    port = sensor["port"]

    try:
        logging.info(f"Checking {sensor['sensor_name']} at {ip}:{port}")
        with socket.create_connection((ip, port), timeout=TIMEOUT) as sock:
            try:
                data = sock.recv(1024)
                if data:
                    status = "green"  # Data received, sensor is functioning properly
                    history_entry = 0  # Status OK (0)
                else:
                    status = "red"  # No data received
                    history_entry = 1  # Status not OK (1)
            except socket.timeout:
                logging.warning(f"Timeout on {sensor['sensor_name']} at {ip}:{port}")
                status = "red"  # Timeout without receiving data
                history_entry = 1  # Status not OK (1)
    except socket.error as e:
        logging.error(f"Connection error for {sensor['sensor_name']} at {ip}:{port}: {e}")
        status = "red"  # Connection error
        history_entry = 1  # Status not OK (1)
    except Exception as e:
        logging.exception(f"Unexpected error for {sensor['sensor_name']} at {ip}:{port}: {e}")
        status = "red"  # Connection error
        history_entry = 1  # Status not OK (1)

    with sensor_lock:
        # Ensure history and status are updated safely
        sensor["status"] = status
        sensor["history"].append(history_entry)
        # Keep history limited to last 100 entries
        if len(sensor["history"]) > 100:
            sensor["history"] = sensor["history"][-100:]

def monitor_station(station_name, platforms):
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        while True:
            futures = []
            for platform_name, sensors in platforms.items():
                for sensor in sensors:
                    futures.append(executor.submit(check_port, sensor))
            
            for future in concurrent.futures.as_completed(futures):
                pass  # All results are processed inside `check_port`
            
            time.sleep(60)  # Sleep before the next check cycle

def start_monitoring():
    for station_name, platforms in stations.items():
        t = threading.Thread(target=monitor_station, args=(station_name, platforms))
        t.daemon = True
        t.start()

if __name__ == "__main__":
    start_monitoring()
    app.run(debug=True)



