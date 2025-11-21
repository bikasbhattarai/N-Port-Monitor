# **nport Monitor**

A lightweight Python tool designed to **monitor N-Port sensor connections in real time**. It checks whether each sensor, IP address, and port is sending data, and displays the status visually using an HTML dashboard.

---

## **Purpose**

The main goal of this project is to make it easy to verify:

* Whether sensors are **connected or disconnected**
* Whether each **IP/port is sending data**
* Whether the N-Port device is functioning correctly
* Whether data streams are **Live (green)** or **Down (red)**

The tool also generates graphs and displays everything in an HTML file.

---

## **Features**

* ✔️ Real-time monitoring of all N-Port ports
* ✔️ Detects if each IP/port is sending data
* ✔️ Green = sending, Red = not sending
* ✔️ Generates graphs for visual inspection
* ✔️ Produces an HTML dashboard
* ✔️ Simple to run and customize

---

## **Requirements**

* Python 3.x
* Required libraries (add more if you use others):

  * `pandas`
  * `matplotlib`
  * `json`
  * `time`

---

## **How to Run**

1. Clone or download the repository
2. Install required Python libraries
3. Run your main script, for example:

   ```bash
   python main.py
   ```
4. Open the generated HTML file (e.g., `monitor.html`) in your browser to view:

   * Sensor status (green/red)
   * Graphs
   * Port activity

---

## **Output**

The tool produces:

* **Green** → Data is being received
* **Red** → No data coming from that port
* Graphs for each monitored port
* An HTML dashboard summarizing everything

---

## **Example Folder Structure**

```
nport-monitor/
│
├── src/
│   └── main.py
│
├── output/
│   └── monitor.html
│
└── README.md
```

---

## **Contribution**

Feel free to open an issue or submit a pull request to improve the project.
