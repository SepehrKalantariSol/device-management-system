from flask import Flask, request, jsonify
import psycopg2
import psycopg2.extras
from datetime import datetime
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ---- DB CONFIG ----
DB_CONFIG = {
    "dbname": "device_mng",
    "user": "sepehr",
    "password": "",          # empty if you didn't set one
    "host": "localhost",
    "port": 5432,
}


def get_db_connection():
    conn = psycopg2.connect(**DB_CONFIG)
    return conn


# ========== HELPERS ==========

def json_error(message, status_code):
    response = jsonify({"error": message})
    response.status_code = status_code
    return response


# ========== ENDPOINTS ==========


# ======================================
# 1) GET /api/v1/devices  (list all devices)
# ======================================

@app.route("/api/v1/devices", methods=["GET"])
def get_devices():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    query = """
        SELECT d.id, d.type, d.serial_number, d.status,
               r.id AS room_id, r.name AS room_name,
               b.id AS building_id, b.name AS building_name
        FROM device d
        JOIN room r ON d.room_id = r.id
        JOIN building b ON r.building_id = b.id
        ORDER BY d.id;
    """
    cur.execute(query)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    devices = []
    for row in rows:
        devices.append({
            "id": row["id"],
            "type": row["type"],
            "serial_number": row["serial_number"],
            "status": row["status"],
            "room": {
                "id": row["room_id"],
                "name": row["room_name"],
            },
            "building": {
                "id": row["building_id"],
                "name": row["building_name"],
            }
        })

    return jsonify(devices), 200

# ======================================
# 2) GET /api/v1/devices/<id>  (single device)
# ======================================

@app.route("/api/v1/devices/<int:device_id>", methods=["GET"])
def get_device(device_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    query = """
        SELECT d.id, d.type, d.serial_number, d.status,
               d.room_id,
               r.name AS room_name,
               b.id AS building_id,
               b.name AS building_name
        FROM device d
        JOIN room r ON d.room_id = r.id
        JOIN building b ON r.building_id = b.id
        WHERE d.id = %s;
    """
    cur.execute(query, (device_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return json_error("Device not found", 404)

    device = {
        "id": row["id"],
        "type": row["type"],
        "serial_number": row["serial_number"],
        "status": row["status"],
        "room": {
            "id": row["room_id"],
            "name": row["room_name"],
        },
        "building": {
            "id": row["building_id"],
            "name": row["building_name"],
        }
    }
    return jsonify(device), 200

# ======================================
# 3) POST /api/v1/devices  (create device)
# ======================================

@app.route("/api/v1/devices", methods=["POST"])
def create_device():
    if not request.is_json:
        return json_error("Content-Type must be application/json", 400)

    data = request.get_json(silent=True) or {}

    required_fields = ["type", "serial_number", "room_id"]
    missing = [f for f in required_fields if f not in data]

    if missing:
        return json_error(f"Missing required field(s): {', '.join(missing)}", 400)

    dev_type = data["type"]
    serial = data["serial_number"]
    room_id = data["room_id"]
    status = data.get("status", "in_use")
    warranty = data.get("warranty_expiry")  # "YYYY-MM-DD" or None
    purchase = data.get("purchase_date")    # "YYYY-MM-DD" or None

    conn = get_db_connection()
    cur = conn.cursor()

    # Check room exists (to give a nice error instead of raw FK error)
    cur.execute("SELECT id FROM room WHERE id = %s;", (room_id,))
    if not cur.fetchone():
        cur.close()
        conn.close()
        return json_error("Room not found", 404)

    try:
        cur.execute(
            """
            INSERT INTO device (type, serial_number, room_id, status, warranty_expiry, purchase_date)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id;
            """,
            (dev_type, serial, room_id, status, warranty, purchase)
        )
        new_id = cur.fetchone()[0]
        conn.commit()
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        cur.close()
        conn.close()
        return json_error("Device with this serial_number already exists", 400)
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return json_error(f"Database error: {str(e)}", 500)

    cur.close()
    conn.close()

    return jsonify({"message": "Device created", "device_id": new_id}), 201

# ======================================
# 4) POST /api/v1/requests  (create support request)
# ======================================

@app.route("/api/v1/requests", methods=["POST"])
def create_request():
    if not request.is_json:
        return json_error("Content-Type must be application/json", 400)

    data = request.get_json(silent=True) or {}

    required_fields = ["device_id", "created_by", "priority", "rq_type", "description"]
    missing = [f for f in required_fields if f not in data]

    if missing:
        return json_error(f"Missing required field(s): {', '.join(missing)}", 400)

    device_id = data["device_id"]
    created_by = data["created_by"]
    priority = data["priority"]
    rq_type = data["rq_type"]
    description = data["description"]

    conn = get_db_connection()
    cur = conn.cursor()

    # Check device exists
    cur.execute("SELECT id FROM device WHERE id = %s;", (device_id,))
    if not cur.fetchone():
        cur.close()
        conn.close()
        return json_error("Device not found", 404)

    # Check person exists
    cur.execute("SELECT person_id FROM person WHERE person_id = %s;", (created_by,))
    if not cur.fetchone():
        cur.close()
        conn.close()
        return json_error("Creator person not found", 404)

    try:
        cur.execute(
            """
            INSERT INTO request (device_id, created_by, priority, rq_type, status, description)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id;
            """,
            (device_id, created_by, priority, rq_type, "open", description)
        )
        req_id = cur.fetchone()[0]
        conn.commit()
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return json_error(f"Database error: {str(e)}", 500)

    cur.close()
    conn.close()

    return jsonify({"message": "Request created", "request_id": req_id, "status": "open"}), 201


# ======================================
# PATCH /api/v1/requests/<id>/accept  (accept / assign to technician)
# ======================================

@app.route("/api/v1/requests/<int:req_id>/accept", methods=["PATCH"])
def accept_request(req_id):
    if not request.is_json:
        return json_error("Content-Type must be application/json", 400)

    data = request.get_json(silent=True) or {}

    if "tech_id" not in data:
        return json_error("Missing required field: tech_id", 400)

    tech_id = data["tech_id"]

    conn = get_db_connection()
    cur = conn.cursor()

    # Check request exists + get current status
    cur.execute("SELECT id, status, resolved_by FROM request WHERE id = %s;", (req_id,))
    row = cur.fetchone()
    if not row:
        cur.close(); conn.close()
        return json_error("Request not found", 404)

    current_status = row[1]
    current_resolver = row[2]

    # Only allow accept if it's open and unassigned
    if current_status != "open" or current_resolver is not None:
        cur.close(); conn.close()
        return json_error("Request cannot be accepted (already assigned or not open)", 400)

    # Check technician exists
    cur.execute("SELECT person_id FROM it_technician WHERE person_id = %s;", (tech_id,))
    if not cur.fetchone():
        cur.close(); conn.close()
        return json_error("tech_id must be a valid IT technician", 400)

    try:
        cur.execute(
            """
            UPDATE request
            SET status = 'in_progress',
                resolved_by = %s
            WHERE id = %s;
            """,
            (tech_id, req_id)
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        cur.close(); conn.close()
        return json_error(f"Database error: {str(e)}", 500)

    cur.close(); conn.close()
    return jsonify({"message": "Request accepted", "request_id": req_id, "status": "in_progress"}), 200


# ======================================
# 5) PATCH /api/v1/requests/<id>/resolve  (resolve support request)
# ======================================

@app.route("/api/v1/requests/<int:req_id>/resolve", methods=["PATCH"])
def resolve_request(req_id):
    if not request.is_json:
        return json_error("Content-Type must be application/json", 400)

    data = request.get_json(silent=True) or {}

    if "resolved_by" not in data:
        return json_error("Missing required field: resolved_by", 400)

    resolved_by = data["resolved_by"]
    comments = data.get("comments", "")

    conn = get_db_connection()
    cur = conn.cursor()

    # Check request exists
    cur.execute("SELECT id FROM request WHERE id = %s;", (req_id,))
    if not cur.fetchone():
        cur.close()
        conn.close()
        return json_error("Request not found", 404)

    # Check resolved_by is an it_technician
    cur.execute("SELECT person_id FROM it_technician WHERE person_id = %s;", (resolved_by,))
    if not cur.fetchone():
        cur.close()
        conn.close()
        return json_error("Resolved_by must be a valid IT technician", 400)

    try:
        cur.execute(
            """
            UPDATE request
            SET status = 'resolved',
                resolved_by = %s,
                time_resolved = NOW(),
                comments = %s
            WHERE id = %s;
            """,
            (resolved_by, comments, req_id)
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return json_error(f"Database error: {str(e)}", 500)

    cur.close()
    conn.close()

    return jsonify({"message": "Request resolved", "request_id": req_id, "status": "resolved"}), 200

# ======================================
# 6) POST /api/v1/login  (simple login endpoint)
# ======================================

@app.route("/api/v1/login", methods=["POST"])
def login():
    if not request.is_json:
        return json_error("Content-Type must be application/json", 400)

    data = request.get_json(silent=True) or {}

    # required fields
    required_fields = ["email", "password"]
    missing = [f for f in required_fields if f not in data]

    if missing:
        return json_error(f"Missing required field(s): {', '.join(missing)}", 400)

    email = data["email"]
    password = data["password"]

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # find person by email
    cur.execute(
        """
        SELECT person_id, first_name, last_name, email, password
        FROM person
        WHERE email = %s;
        """,
        (email,)
    )
    person = cur.fetchone()

    if not person:
        cur.close()
        conn.close()
        # do not reveal whether email exists
        return json_error("Invalid email or password", 401)

    # NOTE: in real life we would store a hashed password and use a safe comparison.
    if password != person["password"]:
        cur.close()
        conn.close()
        return json_error("Invalid email or password", 401)

    # get roles for this person
    cur.execute(
        """
        SELECT r.role
        FROM role r
        JOIN person_role pr ON pr.role_id = r.role_id
        WHERE pr.person_id = %s;
        """,
        (person["person_id"],)
    )
    role_rows = cur.fetchall()
    cur.close()
    conn.close()

    roles = [r["role"] for r in role_rows]

    return jsonify({
        "message": "Login successful",
        "person_id": person["person_id"],
        "first_name": person["first_name"],
        "last_name": person["last_name"],
        "roles": roles
    }), 200

# ======================================
# GET /api/v1/requests  (list all support requests)
# ======================================

@app.route("/api/v1/requests", methods=["GET"])
def list_requests():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    query = """
        SELECT 
            rq.id,
            rq.priority,
            rq.rq_type,
            rq.status,
            rq.description,
            rq.time_resolved,
            rq.time_created,
            
            d.id AS device_id,
            d.type AS device_type,
            d.serial_number,
            
            r.id AS room_id,
            r.name AS room_name,
            
            b.id AS building_id,
            b.name AS building_name,

            p.person_id AS creator_id,
            p.first_name AS creator_first,
            p.last_name AS creator_last,

            tech.person_id AS resolver_id,
            tech_person.first_name AS resolver_first,
            tech_person.last_name AS resolver_last
            
        FROM request rq
        JOIN device d ON rq.device_id = d.id
        JOIN room r ON d.room_id = r.id
        JOIN building b ON r.building_id = b.id
        JOIN person p ON rq.created_by = p.person_id
        LEFT JOIN person tech_person ON rq.resolved_by = tech_person.person_id
        LEFT JOIN it_technician tech ON rq.resolved_by = tech.person_id
        ORDER BY rq.id;
    """

    cur.execute(query)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    requests = []
    for row in rows:
        requests.append({
            "request_id": row["id"],
            "priority": row["priority"],
            "type": row["rq_type"],
            "status": row["status"],
            "description": row["description"],
            "time_created": row["time_created"],
            "time_resolved": row["time_resolved"],

            "device": {
                "id": row["device_id"],
                "type": row["device_type"],
                "serial_number": row["serial_number"]
            },

            "location": {
                "building": {
                    "id": row["building_id"],
                    "name": row["building_name"]
                },
                "room": {
                    "id": row["room_id"],
                    "name": row["room_name"]
                }
            },

            "created_by": {
                "id": row["creator_id"],
                "first_name": row["creator_first"],
                "last_name": row["creator_last"]
            },

            "resolved_by": None if not row["resolver_id"] else {
                "id": row["resolver_id"],
                "first_name": row["resolver_first"],
                "last_name": row["resolver_last"]
            }
        })

    return jsonify(requests), 200

# ======================================
# GET /api/v1/requests/created-by/<person_id>
# ======================================

@app.route("/api/v1/requests/created-by/<int:person_id>", methods=["GET"])
def get_requests_created_by(person_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Check person exists
    cur.execute("SELECT person_id, first_name, last_name FROM person WHERE person_id = %s;", (person_id,))
    person = cur.fetchone()
    if not person:
        cur.close()
        conn.close()
        return json_error("Person not found", 404)

    query = """
        SELECT 
            r.id,
            r.device_id,
            r.priority,
            r.rq_type,
            r.status,
            r.description,
            r.time_created,
            r.time_resolved,
            d.serial_number,
            d.type AS device_type,
            rm.id AS room_id,
            rm.name AS room_name,
            b.id AS building_id,
            b.name AS building_name
        FROM request r
        JOIN device d ON r.device_id = d.id
        JOIN room rm ON d.room_id = rm.id
        JOIN building b ON rm.building_id = b.id
        WHERE r.created_by = %s
        ORDER BY r.time_created DESC;
    """

    cur.execute(query, (person_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    results = []
    for row in rows:
        results.append({
            "request_id": row["id"],
            "device": {
                "id": row["device_id"],
                "serial_number": row["serial_number"],
                "type": row["device_type"]
            },
            "location": {
                "room": {"id": row["room_id"], "name": row["room_name"]},
                "building": {"id": row["building_id"], "name": row["building_name"]}
            },
            "priority": row["priority"],
            "type": row["rq_type"],
            "status": row["status"],
            "description": row["description"],
            "time_created": row["time_created"],
            "resolved_at": row["time_resolved"]
        })

    return jsonify({
        "created_by": {
            "id": person["person_id"],
            "first_name": person["first_name"],
            "last_name": person["last_name"]
        },
        "requests": results
    }), 200

# ======================================
# GET /api/v1/requests/resolved-by/<tech_id>
# ======================================

@app.route("/api/v1/requests/resolved-by/<int:tech_id>", methods=["GET"])
def get_requests_resolved_by(tech_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Check technician exists in it_technician
    cur.execute("""
        SELECT it.person_id, p.first_name, p.last_name
        FROM it_technician it
        JOIN person p ON it.person_id = p.person_id
        WHERE it.person_id = %s;
    """, (tech_id,))
    tech = cur.fetchone()

    if not tech:
        cur.close()
        conn.close()
        return json_error("Technician not found", 404)

    query = """
        SELECT 
            r.id,
            r.device_id,
            r.priority,
            r.rq_type,
            r.status,
            r.description,
            r.time_created,
            r.time_resolved,
            d.serial_number,
            d.type AS device_type,
            rm.id AS room_id,
            rm.name AS room_name,
            b.id AS building_id,
            b.name AS building_name
        FROM request r
        JOIN device d ON r.device_id = d.id
        JOIN room rm ON d.room_id = rm.id
        JOIN building b ON rm.building_id = b.id
        WHERE r.resolved_by = %s
        ORDER BY r.time_resolved DESC;
    """

    cur.execute(query, (tech_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    results = []
    for row in rows:
        results.append({
            "request_id": row["id"],
            "device": {
                "id": row["device_id"],
                "serial_number": row["serial_number"],
                "type": row["device_type"]
            },
            "location": {
                "room": {"id": row["room_id"], "name": row["room_name"]},
                "building": {"id": row["building_id"], "name": row["building_name"]}
            },
            "priority": row["priority"],
            "type": row["rq_type"],
            "status": row["status"],
            "description": row["description"],
            "time_created": row["time_created"],
            "resolved_at": row["time_resolved"]
        })

    return jsonify({
        "technician": {
            "id": tech["person_id"],
            "first_name": tech["first_name"],
            "last_name": tech["last_name"]
        },
        "resolved_requests": results
    }), 200


# ======================================
# GET /api/v1/requests/<id>  (full details of one request)
# ======================================

@app.route("/api/v1/requests/<int:req_id>", methods=["GET"])
def get_request_by_id(req_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    query = """
        SELECT 
            r.id,
            r.device_id,
            r.priority,
            r.rq_type,
            r.status,
            r.description,
            r.comments,
            r.time_created,
            r.time_resolved,

            d.serial_number,
            d.type AS device_type,

            rm.id   AS room_id,
            rm.name AS room_name,

            b.id    AS building_id,
            b.name  AS building_name,

            creator.person_id   AS creator_id,
            creator.first_name  AS creator_first,
            creator.last_name   AS creator_last,

            tech_person.person_id   AS resolver_id,
            tech_person.first_name  AS resolver_first,
            tech_person.last_name   AS resolver_last

        FROM request r
        JOIN device d       ON r.device_id   = d.id
        JOIN room   rm      ON d.room_id     = rm.id
        JOIN building b     ON rm.building_id = b.id
        JOIN person creator ON r.created_by  = creator.person_id
        LEFT JOIN person tech_person ON r.resolved_by = tech_person.person_id
        WHERE r.id = %s;
    """

    cur.execute(query, (req_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return json_error("Request not found", 404)

    result = {
        "request_id": row["id"],
        "priority": row["priority"],
        "type": row["rq_type"],
        "status": row["status"],
        "description": row["description"],
        "comments": row["comments"],
        "time_created": row["time_created"],
        "resolved_at": row["time_resolved"],

        "device": {
            "id": row["device_id"],
            "serial_number": row["serial_number"],
            "type": row["device_type"],
        },

        "location": {
            "room": {
                "id": row["room_id"],
                "name": row["room_name"],
            },
            "building": {
                "id": row["building_id"],
                "name": row["building_name"],
            }
        },

        "created_by": {
            "id": row["creator_id"],
            "first_name": row["creator_first"],
            "last_name": row["creator_last"],
        },

        "resolved_by": None if row["resolver_id"] is None else {
            "id": row["resolver_id"],
            "first_name": row["resolver_first"],
            "last_name": row["resolver_last"],
        }
    }

    return jsonify(result), 200


# ======================================
# GET /api/v1/technicians  (list all IT technicians)
# ======================================

@app.route("/api/v1/technicians", methods=["GET"])
def get_technicians():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Basic version: technician + person info
    # If your it_technician table also has it_desk_id, you can LEFT JOIN it_desk too.
    query = """
        SELECT 
            it.person_id,
            p.first_name,
            p.last_name,
            p.email,
            p.phone
        FROM it_technician it
        JOIN person p ON it.person_id = p.person_id
        ORDER BY p.last_name, p.first_name;
    """

    cur.execute(query)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    technicians = []
    for row in rows:
        technicians.append({
            "person_id": row["person_id"],
            "first_name": row["first_name"],
            "last_name": row["last_name"],
            "email": row["email"],
            "phone": row["phone"]
        })

    return jsonify(technicians), 200

# ======================================
# POST /api/v1/persons  (create a new staff / IT technician)
# ======================================

@app.route("/api/v1/persons", methods=["POST"])
def create_person():
    if not request.is_json:
        return json_error("Content-Type must be application/json", 400)

    data = request.get_json(silent=True) or {}

    # Required basic staff fields
    required_fields = [
        "first_name",
        "last_name",
        "email",
        "password",
        "staff_type"   # "normal" or "it_technician"
    ]
    missing = [f for f in required_fields if f not in data]

    if missing:
        return json_error(f"Missing required field(s): {', '.join(missing)}", 400)

    first_name = data["first_name"]
    last_name  = data["last_name"]
    email      = data["email"]
    password   = data["password"]
    department = data.get("department", "General Department") # default department if not provided
    staff_type = data["staff_type"]  # expected: "normal" or "it_technician"

    if staff_type not in ("normal", "it_technician"):
        return json_error("staff_type must be 'normal' or 'it_technician'", 400)

    phone_number = data.get("phone_number")
    address      = data.get("address")
    status       = data.get("status", "active")
    date_joined  = data.get("date_joined")   # optional, else NOW()
    # this "person" field in your schema could be used as a label, e.g. "staff"
    person_label = data.get("person", "staff")

    # for now, only one organisation
    organization_id = 1

    # if IT technician, we expect a desk_id
    desk_id = data.get("desk_id", 1)


    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    try:
        # 1) ensure email is unique
        cur.execute("SELECT person_id FROM person WHERE email = %s;", (email,))
        if cur.fetchone():
            cur.close()
            conn.close()
            return json_error("A person with this email already exists", 400)

        # 2) if IT tech, check that the IT desk exists
        if staff_type == "it_technician":
            cur.execute("SELECT id FROM it_desk WHERE id = %s;", (desk_id,))
            if not cur.fetchone():
                cur.close()
                conn.close()
                return json_error("IT desk not found", 404)

        # 3) insert into person
        cur.execute(
            """
            INSERT INTO person
                (organization_id, first_name, last_name,
                 email, password, phone_number, address,
                 status, date_joined)
            VALUES
                (%s, %s, %s,
                 %s, %s, %s, %s,
                 %s, COALESCE(%s, NOW()))
            RETURNING person_id;
            """,
            (
                organization_id,
                first_name,
                last_name,
                email,
                password,
                phone_number,
                address,
                status,
                date_joined
            )
        )
        person_row = cur.fetchone()
        person_id = person_row["person_id"]

        # 4) insert into staff (all staff, normal and IT)
        cur.execute(
            """
            INSERT INTO staff (person_id, department)
            VALUES (%s, %s);
            """,
            (person_id, department)
        )

        # 5) find role_id values for 'staff' and 'it_technician'
        #    (we avoid hardcoding 2 and 3 in case they change)
        cur.execute("SELECT role_id, role FROM role WHERE role IN ('staff', 'it_technician');")
        role_rows = cur.fetchall()
        role_map = {row["role"]: row["role_id"] for row in role_rows}

        # we expect at least 'staff' to exist
        if "staff" not in role_map:
            conn.rollback()
            cur.close()
            conn.close()
            return json_error("Role 'staff' not configured in role table", 500)

        staff_role_id = role_map["staff"]
        # 'it_technician' might be needed if staff_type is IT
        it_role_id = role_map.get("it_technician")

        # 6) add staff role in person_role
        cur.execute(
            """
            INSERT INTO person_role (person_id, role_id)
            VALUES (%s, %s);
            """,
            (person_id, staff_role_id)
        )

        # 7) if IT technician → insert into it_technician and add IT role
        if staff_type == "it_technician":
            if it_role_id is None:
                conn.rollback()
                cur.close()
                conn.close()
                return json_error("Role 'it_technician' not configured in role table", 500)

            # insert into it_technician
            cur.execute(
                """
                INSERT INTO it_technician (person_id, desk_id, status, specialization)
                VALUES (%s, %s, %s, %s);
                """,
                (person_id, desk_id, "active", data.get("specialization"))
            )

            # add IT technician role tag
            cur.execute(
                """
                INSERT INTO person_role (person_id, role_id)
                VALUES (%s, %s);
                """,
                (person_id, it_role_id)
            )

        conn.commit()

    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return json_error(f"Database error: {str(e)}", 500)

    cur.close()
    conn.close()

    return jsonify({
        "message": "Person created",
        "person_id": person_id,
        "staff_type": staff_type
    }), 201

# ======================================
# GET /api/v1/persons/<person_id>  (get profile info)
# ======================================

@app.route("/api/v1/persons/<int:person_id>", methods=["GET"])
def get_person(person_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute(
        """
        SELECT person_id, organization_id, first_name, last_name, email,
               phone_number, address, status, date_joined
        FROM person
        WHERE person_id = %s;
        """,
        (person_id,)
    )
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return json_error("Person not found", 404)

    return jsonify({
        "person_id": row["person_id"],
        "organization_id": row["organization_id"],
        "first_name": row["first_name"],
        "last_name": row["last_name"],
        "email": row["email"],
        "phone_number": row["phone_number"],
        "address": row["address"],
        "status": row["status"],
        "date_joined": str(row["date_joined"]) if row["date_joined"] else None
    }), 200

# ======================================
# PATCH /api/v1/persons/<person_id>  (update profile info)
# ======================================

@app.route("/api/v1/persons/<int:person_id>", methods=["PATCH"])
def update_person(person_id):
    if not request.is_json:
        return json_error("Content-Type must be application/json", 400)

    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict) or len(data) == 0:
        return json_error("Request body must be a non-empty JSON object", 400)

    # Only allow these fields to be updated
    allowed_fields = {"first_name", "last_name", "phone_number", "address", "password"}
    unknown_fields = [k for k in data.keys() if k not in allowed_fields]

    if unknown_fields:
        return json_error(f"Unknown/unsupported field(s): {', '.join(unknown_fields)}", 400)

    # Must update at least one allowed field
    fields_to_update = {k: data[k] for k in data if k in allowed_fields}
    if len(fields_to_update) == 0:
        return json_error("No valid fields provided to update", 400)

    # Basic validation (keep simple for prototype)
    if "first_name" in fields_to_update:
        if not str(fields_to_update["first_name"]).strip():
            return json_error("first_name cannot be empty", 400)

    if "last_name" in fields_to_update:
        if not str(fields_to_update["last_name"]).strip():
            return json_error("last_name cannot be empty", 400)

    if "password" in fields_to_update:
        if not str(fields_to_update["password"]).strip():
            return json_error("password cannot be empty", 400)

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Check person exists
    cur.execute("SELECT person_id FROM person WHERE person_id = %s;", (person_id,))
    if not cur.fetchone():
        cur.close()
        conn.close()
        return json_error("Person not found", 404)

    # Build dynamic UPDATE safely
    set_clauses = []
    values = []
    for i, (field, value) in enumerate(fields_to_update.items(), start=1):
        set_clauses.append(f"{field} = %s")
        values.append(value)

    values.append(person_id)

    query = f"""
        UPDATE person
        SET {", ".join(set_clauses)}
        WHERE person_id = %s
        RETURNING person_id, first_name, last_name, email, phone_number, address, status, date_joined;
    """

    try:
        cur.execute(query, tuple(values))
        updated = cur.fetchone()
        conn.commit()
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return json_error(f"Database error: {str(e)}", 500)

    cur.close()
    conn.close()

    return jsonify({
        "message": "Profile updated",
        "person": {
            "person_id": updated["person_id"],
            "first_name": updated["first_name"],
            "last_name": updated["last_name"],
            "email": updated["email"],
            "phone_number": updated["phone_number"],
            "address": updated["address"],
            "status": updated["status"],
            "date_joined": str(updated["date_joined"]) if updated["date_joined"] else None
        }
    }), 200

if __name__ == "__main__":
    # For development only
    app.run(debug=True)