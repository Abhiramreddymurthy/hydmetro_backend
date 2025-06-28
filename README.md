# Hyderabad Metro Backend System

This project provides a comprehensive backend system for a "Hyderabad Metro Route Finder" application, enabling users to find optimal metro routes, fares, and estimated travel times, while also offering administrative tools for managing the metro network data.

## 🌟 Core Features

* **Network Management APIs:** RESTful endpoints to manage metro lines, stations, and their connections.

* **Route Finding:** Efficiently calculates the shortest (optimal) path between any two metro stations.

* **Fare Calculation:** Determines the total fare for the route based on the number of stations and line changes.

* **Estimated Time Calculation:** Calculates the estimated travel time for the determined route.

* **Comprehensive RESTful APIs:** Provides well-defined endpoints for both management and user-facing functionalities.

## 🚀 Technical Stack

* **Language:** Python 3.9+

* **Web Framework:** FastAPI

* **Database:** PostgreSQL

* **ORM (Object-Relational Mapper):** SQLAlchemy

* **Database Driver:** Psycopg2

* **Graph Algorithm:** Dijkstra's Algorithm (implemented in-memory for route finding)

* **API Standard:** RESTful services with JSON responses

## 📂 Project Structure

hydmetro/
├── init.py         # Makes 'hydmetro' a Python package
├── main.py             # FastAPI application entry point, defines routes and main logic
├── models.py           # SQLAlchemy ORM definitions for database tables (Line, Station)
├── schemas.py          # Pydantic models for API request/response validation and serialization
└── database.py         # Database connection setup (SQLAlchemy engine, session)


## ⚙️ Setup Instructions

Follow these steps to get the Hyderabad Metro Backend system up and running on your local machine.

### 1. Install Python

Ensure you have Python 3.9 or higher installed. You can download it from [python.org](https://www.python.org/downloads/).

### 2. Install PostgreSQL

If you haven't already, install PostgreSQL.

* **Recommended (Windows/macOS):** Use the [official installer](https://www.postgresql.org/download/). This bundles PostgreSQL server, `pgAdmin 4` (GUI), and command-line tools.

* **Linux:** Use your distribution's package manager (e.g., `sudo apt install postgresql` on Ubuntu).

* **Docker (Advanced):** Refer to Docker's documentation to run a PostgreSQL container.

### 3. Create PostgreSQL Database and User

Once PostgreSQL is installed:

* **Connect as `postgres` superuser:**

    * **Using pgAdmin 4:** Launch pgAdmin 4, connect to your server, and use the GUI.

    * **Using `psql` (SQL Shell):** Open "SQL Shell (psql)" from your Start Menu, and connect as user `postgres` with its password.

* **Create the database `hyderabad_metro`:**

    ```sql
    CREATE DATABASE hyderabad_metro;
    ```

    (Ensure you are connected as a superuser like `postgres` to run this.)

* **Create a dedicated user `metro_user` and set a strong password:**

    ```sql
    CREATE ROLE metro_user WITH LOGIN PASSWORD 'your_strong_password_here';
    ```

    (Replace `'your_strong_password_here'` with a robust password. Remember this password!)

* **Grant ownership of the database to `metro_user`:**

    ```sql
    ALTER DATABASE hyderabad_metro OWNER TO metro_user;
    ```

    (Ensure you are connected to the `hyderabad_metro` database or use `\c hyderabad_metro` first if in `psql`).

### 4. Set up Python Environment

1.  **Navigate to your project directory:**
    Open your command prompt (or PowerShell) and go to the *parent directory* of `hydmetro`. For example, if `hydmetro` is in `C:\Users\Murthy Abhiram Reddy\Desktop\hydmetro`, you would `cd C:\Users\Murthy Abhiram Reddy\Desktop`.

2.  **Create a virtual environment (recommended):**

    ```bash
    python -m venv venv
    ```

3.  **Activate the virtual environment:**

    * **Windows:**

        ```bash
        .\venv\Scripts\activate
        ```

    * **macOS/Linux:**

        ```bash
        source venv/bin/activate
        ```

4.  **Install project dependencies:**

    ```bash
    pip install fastapi uvicorn "sqlalchemy[psycopg2]" pydantic
    ```

### 5. Configure Database Connection in `database.py`

Open `hydmetro/database.py` and update the `SQLALCHEMY_DATABASE_URL` with the credentials you set up for `metro_user`:

```python
# hydmetro/database.py

# ... (other imports) ...

# Update with your actual metro_user and password
SQLALCHEMY_DATABASE_URL = "postgresql://metro_user:your_strong_password_here@localhost:5432/hyderabad_metro"

# ... (rest of the file) ...
Remember to replace your_strong_password_here with the actual password for metro_user.

6. Run the FastAPI Application
From the parent directory of hydmetro (e.g., C:\Users\Murthy Abhiram Reddy\Desktop):

Bash

uvicorn hydmetro.main:app --reload
You should see output indicating the server is running on http://127.0.0.1:8000.

Crucially, look for the line Metro graph built successfully on startup. This confirms your tables (lines and stations) were created by SQLAlchemy and the application connected to the database.

📄 API Endpoints
The FastAPI application automatically generates interactive API documentation using Swagger UI.

Open your browser and go to: http://127.0.0.1:8000/docs

Here's a summary of the available endpoints:

Line Management
POST /api/lines: Create a new metro line.

GET /api/lines: List all metro lines.

GET /api/lines/{line_id}: Get details of a specific line.

PUT /api/lines/{line_id}: Update a line's details.

DELETE /api/lines/{line_id}: Delete a line.

Station Management
POST /api/lines/{line_id}/stations: Add a new station to a specific line.

GET /api/lines/{line_id}/stations: List all stations on a specific line.

GET /api/stations: List all stations across the entire network.

Route Finding
POST /api/route/find: Find the optimal route, fare, and time between two stations.

📊 Data Context, Fare, and Time Calculation Rules
The system is designed for the Hyderabad Metro Network.

Major Interchange Stations:
Ameerpet (Red-Blue)

Secunderabad (Red-Blue-Green)

Paradise (Red-Blue)

Begumpet (Red-Blue)

Fare Calculation Rules:
Base Fare: ₹10 for the first 2 stations.

Additional Fare: ₹5 per station after the first 2 stations.

Interchange Penalty: ₹2 per line change.

Estimated Travel Time Calculation:
Formula: Estimated Time = (number_of_stations_in_route - 1) × avg_time_per_station + (number_of_interchanges × interchange_time)

Default Assumptions:

Average Time per Station: 2.5 minutes per station (excluding the origin station).

Interchange Time: 5 minutes per interchange.

🚀 How to Use & Test
Ensure the FastAPI server is running. (See "Run the FastAPI Application" above).

Open http://127.0.0.1:8000/docs in your browser.

1. Add Metro Lines:
Go to the POST /api/lines endpoint.

Click "Try it out".

Use the "Request body" to add the lines. Click "Execute" after each.

Red Line: {"name": "Red Line", "color": "Red"} (Note down its id)

Blue Line: {"name": "Blue Line", "color": "Blue"} (Note down its id)

Green Line: {"name": "Green Line", "color": "Green"} (Note down its id)

2. Add Stations:
Go to the POST /api/lines/{line_id}/stations endpoint.

Click "Try it out".

Important:

For each station, provide the correct line_id (from step 1).

Ensure station_number_on_line is sequential for each line.

Set is_interchange: true for the major interchange stations when adding them to each line they belong to.

Example for Red Line (assuming ID 1):

Miyapur: {"name": "Miyapur", "distance_from_previous_station": 0.0, "station_number_on_line": 1, "is_interchange": false}

... (add other stations on Red Line in order) ...

Ameerpet: {"name": "Ameerpet", "distance_from_previous_station": X, "station_number_on_line": Y, "is_interchange": true} (where X and Y are correct for Red Line)

... (continue until LB Nagar) ...

Example for Blue Line (assuming ID 2):

Nagole: {"name": "Nagole", "distance_from_previous_station": 0.0, "station_number_on_line": 1, "is_interchange": false}

... (add other stations on Blue Line in order) ...

Ameerpet: {"name": "Ameerpet", "distance_from_previous_station": X, "station_number_on_line": Y, "is_interchange": true} (where X and Y are correct for Blue Line)

... (continue until Raidurg) ...

Example for Green Line (assuming ID 3):

JBS Parade Ground: {"name": "JBS Parade Ground", "distance_from_previous_station": 0.0, "station_number_on_line": 1, "is_interchange": false}

... (add other stations on Green Line in order) ...

Secunderabad: {"name": "Secunderabad", "distance_from_previous_station": X, "station_number_on_line": Y, "is_interchange": true} (where X and Y are correct for Green Line)

... (continue until MGBS) ...

(You will need to manually list all stations for each line from the Hyderabad Metro data to fully populate the system.)

3. Find a Route:
Go to the POST /api/route/find endpoint.

Click "Try it out".

Enter your source and destination stations in the "Request body":

JSON

{
  "source": "Miyapur",
  "destination": "Hitec City"
}
Click "Execute".

The "Response body" will show the calculated route, total stations, total fare, interchanges, estimated time, and line changes.

✨ Future Enhancements
Caching: Implement caching for frequently accessed data (e.g., the MetroGraph itself) to improve performance.

Authentication & Authorization: Secure management APIs with proper user authentication (e.g., JWT).

Error Handling: More granular error messages and a global exception handler.

Input Validation: Enhance validation for station/line names (e.g., case-insensitive search).

Dynamic Graph Updates: Implement a mechanism to update the in-memory graph more efficiently when line/station data changes, instead of a full rebuild on every management API call.

Unit & Integration Tests: Add comprehensive tests for all API endpoints and the core graph logic.

Dockerization: Provide a Dockerfile for easier deployment.

Frontend Integration: Develop a simple web or mobile frontend to consume these APIs.

Optimized Pathfinding: For more complex criteria, explore A* algorithm with a custom heuristic or multi-objective pathfinding.
