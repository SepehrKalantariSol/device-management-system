DEVICE MANAGEMENT SYSTEM
========================

Overview
--------
The Device Management System is a full-stack web application designed to manage IT assets and support requests within an organisation (e.g., university or enterprise environment).

The system allows users (students/staff) to report device-related issues and enables IT technicians to manage, track, and resolve these requests through a structured workflow.

This project demonstrates end-to-end software engineering, including backend API development, database design, and frontend integration.


Features
--------

User Functionality:
- User login and authentication
- View available devices
- Submit support requests
- Track request status

Technician Functionality:
- View all support requests
- Assign requests
- Update request status (open → in_progress → resolved)
- Add resolution comments

System Features:
- Role-based access control (RBAC)
- Device tracking with location (Building → Room)
- Full request lifecycle management
- Input validation and error handling
- Secure backend API


System Architecture
-------------------

Frontend (HTML, CSS, JavaScript)
        ↓
Flask REST API (Python)
        ↓
PostgreSQL Database


Technologies Used
-----------------

Programming:
- Python
- JavaScript
- SQL

Backend:
- Flask (REST API)

Frontend:
- HTML
- CSS
- JavaScript

Database:
- PostgreSQL
- psycopg2

Tools:
- Git
- Linux
- Virtual environments (venv)
- DBeaver / pgAdmin


How to Run the Project
----------------------

1. Setup Database

psql -U <your_username> -h localhost device_mng

To exit:
\q


2. Start Backend (Flask API)

cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 app.py

Backend will run at:
http://127.0.0.1:5000


3. Start Frontend

Open a new terminal:

cd frontend
python3 -m http.server 8000

Frontend will run at:
http://127.0.0.1:8000

Open in browser:
http://127.0.0.1:8000/index.html


How to Stop the Project
-----------------------

- Press CTRL + C in each terminal
- To deactivate virtual environment:
deactivate


Ports Used
----------

Backend API:  http://127.0.0.1:5000
Frontend UI:  http://127.0.0.1:8000


Notes
-----

- Backend must be running before using the frontend
- Both backend and frontend must run at the same time
- This project is intended for local development


Skills Demonstrated
-------------------

- Full-stack development
- REST API design
- Database design (normalisation, relationships)
- Backend development with Flask
- Problem solving and system design
- Secure coding practices
