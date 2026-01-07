# 🌐 N-Port Monitor

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Maintenance](https://img.shields.io/badge/Maintained-Yes-brightgreen.svg)](https://github.com/yourusername/N-Port-Monitor/graphs/commit-activity)

A real-time **N-Port sensor monitoring system** built with Flask and SQLite. Monitor multiple sensors across different platforms and stations with an intuitive web dashboard featuring live status indicators and historical data visualization.

![Dashboard Preview](docs/images/dashboard-preview.png)

---

## ✨ Features

- **🔴🟢 Real-time Status Monitoring** — Live green/red indicators showing sensor connectivity
- **📊 Historical Data Visualization** — Interactive charts displaying sensor status history
- **🏢 Multi-Station Support** — Organize sensors into stations and platforms
- **➕ Easy Configuration** — Add, edit, and delete stations through the web interface
- **📱 Responsive Design** — Works on desktop and mobile devices
- **🔄 Auto-Refresh** — Dashboard updates automatically every 20 seconds
- **💾 Persistent Storage** — SQLite database for reliable data storage

---

## 🖥️ Screenshots

<details>
<summary>Click to view screenshots</summary>

### Home Dashboard
![Home Dashboard](docs/images/home.png)

### Station View
![Station View](docs/images/station.png)

### Add Station Form
![Add Station](docs/images/add-station.png)

</details>

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/N-Port-Monitor.git
   cd N-Port-Monitor
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the database**
   ```bash
   python -c "from data_monitor.database import init_db; init_db()"
   ```

5. **Run the application**
   ```bash
   python run.py
   ```

6. **Open your browser**
   Navigate to `http://localhost:5000`

---

## 📁 Project Structure

```
N-Port-Monitor/
├── data_monitor/
│   ├── __init__.py          # Package initialization
│   ├── app.py               # Flask application and routes
│   ├── database.py          # Database operations
│   ├── monitor.py           # Sensor monitoring logic
│   ├── config.py            # Configuration settings
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css    # Main stylesheet
│   │   └── images/
│   │       └── logo.png     # Application logo
│   └── templates/
│       ├── base.html        # Base template
│       ├── index.html       # Home page
│       ├── station.html     # Station detail view
│       ├── add_station.html # Add station form
│       └── edit_station.html# Edit station form
├── docs/
│   └── images/              # Documentation images
├── tests/
│   └── test_app.py          # Unit tests
├── .env.example             # Environment variables template
├── .gitignore               # Git ignore rules
├── LICENSE                  # MIT License
├── README.md                # This file
├── requirements.txt         # Python dependencies
└── run.py                   # Application entry point
```

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root (copy from `.env.example`):

```env
# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=1
SECRET_KEY=your-secret-key-here

# Server Configuration
HOST=0.0.0.0
PORT=5000

# Monitoring Configuration
SENSOR_TIMEOUT=60
CHECK_INTERVAL=60
HISTORY_LIMIT=100

# Database
DATABASE_PATH=data_monitor/stations.db
```

### Sensor Configuration

Sensors are configured through the web interface. Each sensor requires:
- **Sensor Name**: Descriptive name for the sensor
- **IP Address**: Network address of the sensor
- **Port**: TCP port number for data transmission

---

## 📖 Usage

### Adding a Station

1. Click "Add Station" on the home page
2. Enter a station name
3. Add one or more platforms
4. For each platform, add sensors with their IP and port
5. Click "Create Station"

### Monitoring Sensors

- **Green** 🟢 — Sensor is sending data normally
- **Red** 🔴 — No data received (connection timeout or error)
- **Gray** ⚫ — Status unknown (not yet checked)

### Viewing History

Click on any status indicator to view a historical chart of that sensor's connectivity over time.

---

## 🛠️ Development

### Running Tests

```bash
pytest tests/ -v
```

### Code Style

This project follows PEP 8 guidelines. Run linting with:

```bash
flake8 data_monitor/
```

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 🔧 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Home page with station list |
| GET | `/station/<name>` | View station details |
| GET | `/add_station` | Add station form |
| POST | `/add_station` | Create new station |
| GET | `/edit_station/<name>` | Edit station form |
| POST | `/edit_station/<name>` | Update station |
| POST | `/delete_station/<name>` | Delete station |
| GET | `/history/<platform>/<sensor>` | Get sensor history |

---

## 🐛 Troubleshooting

<details>
<summary>Common Issues</summary>

### Port already in use
```bash
# Find and kill the process using port 5000
lsof -i :5000
kill -9 <PID>
```

### Database locked
```bash
# Remove journal file if exists
rm data_monitor/stations.db-journal
```

### Sensors showing as red
- Verify the sensor IP and port are correct
- Check network connectivity to the sensor
- Ensure no firewall is blocking the connection

</details>

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👥 Authors

- **Your Name** - *Initial work* - [bikascb@met.no](mailto:bikascb@met.no)

---

## 🙏 Acknowledgments

- Norwegian Meteorological Institute
- Flask community
- Chart.js for visualization

---

<p align="center">
  Made with ❤️ for the Norwegian Meteorological Institute
</p>
