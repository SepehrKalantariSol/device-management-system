# Device Management System

A full-stack web application for managing devices, users, and IT support requests within an organization.  
This system simulates a real-world IT asset management and support workflow, including device tracking, user roles, and request lifecycle management.

Demo video:
https://drive.google.com/file/d/1h-W3AQhQrTLvGjQEmpAHPV4lUeXLO4B6/view?usp=share_link

---

## Overview

The Device Management System allows organizations to:

- Track devices across buildings and rooms  
- Manage staff and IT technicians  
- Create and manage support requests  
- Assign and resolve issues through a structured workflow  
- Maintain a centralized relational database for all assets and users  

This project demonstrates backend API development, relational database design, and frontend integration.

---

## Key Features

### Device Management
- Create, view, and manage devices
- Track device location (building and room)
- Store device metadata (serial number, status, warranty, etc.)

### Request Workflow System
- Create support requests linked to devices
- Assign requests to IT technicians
- Track request status: open → in_progress → resolved
- Add comments and resolution details

### User and Role Management
- Create users (staff and IT technicians)
- Assign roles dynamically via relational mapping
- Retrieve user profiles and activity

### Relational Database Design
- Fully normalized PostgreSQL schema
- Use of foreign keys and junction tables (person_role)
- Structured entity relationships (device → room → building)

---

## System Architecture

Frontend (HTML, CSS, JavaScript)  
↓  
REST API (Flask)  
↓  
PostgreSQL Database  

- Frontend: Static pages with JavaScript handling API requests  
- Backend: Flask REST API with structured endpoints  
- Database: PostgreSQL with normalized schema and constraints  

---

## Tech Stack

- Backend: Python (Flask)
- Database: PostgreSQL
- Frontend: HTML, CSS, JavaScript
- Libraries:
  - psycopg2
  - Flask-CORS

---

## Project Structure

backend/  
    app.py  

database/  
    schema.sql  

docs/  
    D2_design_document.pdf  

frontend/  
    css/  
    js/  
    *.html  

.gitignore  
README.md  

---

## Setup and Installation

1. Clone the repository
```bash
git clone https://github.com/SepehrKalantariSol/device-management-system.git
cd device-management-system
```

2. Setup virtual environment
```bash
python -m venv venv  
source venv/bin/activate
```

3. Install dependencies
```bash
pip install flask psycopg2 flask-cors
```  

4. Configure environment variables
```bash
export DB_NAME=device_mng  
export DB_USER=postgres  
export DB_PASSWORD=your_password  
export DB_HOST=localhost  
export DB_PORT=5432  
```
5. Setup database
```bash
Create a PostgreSQL database, then run:

psql -U postgres -d device_mng -f database/schema.sql  
```
6. Run the backend
```bash
python backend/app.py
```
 
7. Open frontend
```bash
Open frontend/index.html in your browser.
```

---

## API Endpoints (Examples)
```bash
Devices  
GET /api/v1/devices  
POST /api/v1/devices  

Requests  
POST /api/v1/requests  
PATCH /api/v1/requests/{id}/accept  
PATCH /api/v1/requests/{id}/resolve  

Users  
POST /api/v1/persons  
GET /api/v1/persons/{id}
```

---

## Notes

- This project is a prototype system built for educational purposes  
- Authentication is simplified (plaintext password comparison)  
- In production, passwords should be hashed and secured properly  

---

## What This Project Demonstrates

- REST API design and implementation  
- Relational database modelling  
- Backend and frontend integration  
- Structured system design for real-world workflows  
- Clean project organization and version control practices  

---

## Contributors

- Sepehr Kalantari Soltanieh
- Seyed Atta Rahimi

---

## License

This project is for educational and portfolio purposes.
