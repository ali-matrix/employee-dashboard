
from pathlib import Path
import sqlite3

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

DB_PATH = Path(__file__).resolve().parent / "employees.db"

VALID_STATUSES = {"Active", "On Leave", "Inactive"}


def get_db_connection():
    """Create a fresh database connection for each operation."""
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_api_tables():
    """Create the audit log table if it does not exist."""
    connection = get_db_connection()

    try:
        with connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    entity_id INTEGER NOT NULL,
                    details TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
    finally:
        connection.close()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "success",
        "message": "Dashboard API is running"
    }), 200


@app.route("/api/employees", methods=["GET"])
def get_employees():
    department = request.args.get("department")
    status = request.args.get("status")
    search = request.args.get("search", "").strip()

    query = """
        SELECT
            e.id,
            e.first_name,
            e.last_name,
            e.email,
            e.designation,
            e.salary,
            e.joining_date,
            e.status,
            d.id AS department_id,
            d.name AS department
        FROM employees AS e
        JOIN departments AS d
            ON d.id = e.department_id
        WHERE 1 = 1
    """
    params = []

    if department:
        query += " AND d.name = ?"
        params.append(department)

    if status:
        if status not in VALID_STATUSES:
            return jsonify({
                "error": "Invalid status",
                "allowed": sorted(VALID_STATUSES)
            }), 400

        query += " AND e.status = ?"
        params.append(status)

    
    if search:
        query += """
            AND (
                (e.first_name || ' ' || e.last_name) LIKE ?
                OR e.first_name LIKE ?
                OR e.last_name LIKE ?
                OR e.email LIKE ?
                OR e.designation LIKE ?
            )
        """
        term = f"%{search}%"
        params.extend([term, term, term, term, term])


    query += " ORDER BY e.id"

    connection = get_db_connection()

    try:
        rows = connection.execute(query, params).fetchall()
        employees = [dict(row) for row in rows]

        return jsonify({
            "count": len(employees),
            "employees": employees
        }), 200
    finally:
        connection.close()


@app.route("/api/stats", methods=["GET"])
def get_stats():
    connection = get_db_connection()

    try:
        totals = connection.execute("""
            SELECT
                COUNT(*) AS total_employees,
                COALESCE(
                    SUM(CASE WHEN status = 'Active'
                        THEN 1 ELSE 0 END), 0
                ) AS active_employees,
                COALESCE(AVG(salary), 0) AS average_salary
            FROM employees
        """).fetchone()

        departments = connection.execute("""
            SELECT
                d.name,
                COUNT(e.id) AS employee_count
            FROM departments AS d
            LEFT JOIN employees AS e
                ON e.department_id = d.id
            GROUP BY d.id, d.name
            ORDER BY d.name
        """).fetchall()

        return jsonify({
            "total_employees": totals["total_employees"],
            "active_employees": totals["active_employees"],
            "average_salary": round(totals["average_salary"], 2),
            "departments": [dict(row) for row in departments]
        }), 200
    finally:
        connection.close()


@app.route("/api/employees", methods=["POST"])
def create_employee():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "Request body must be valid JSON"
        }), 400

    required_fields = [
        "first_name",
        "last_name",
        "email",
        "department_id",
        "designation",
        "salary",
        "joining_date",
        "status"
    ]

    missing = [
        field for field in required_fields
        if field not in data
        or data[field] is None
        or data[field] == ""
    ]

    if missing:
        return jsonify({
            "error": "Missing required fields",
            "fields": missing
        }), 400

    # Validate before opening the transaction
    for field in ("first_name", "last_name", "email", "designation"):
        if not isinstance(data[field], str) or not data[field].strip():
            return jsonify({
                "error": f"{field} must be a non-empty string"
            }), 400

    try:
        department_id = int(data["department_id"])
        salary = float(data["salary"])
    except (ValueError, TypeError):
        return jsonify({
            "error": "department_id must be an integer and salary a number"
        }), 400

    if department_id <= 0 or salary < 0:
        return jsonify({
            "error": "Invalid department_id or salary"
        }), 400

    if data["status"] not in VALID_STATUSES:
        return jsonify({
            "error": "Invalid employee status"
        }), 400

    email = data["email"].strip().lower()

    connection = get_db_connection()

    try:
        # Atomicity: employee + audit log commit together.
        # If either insert fails, both changes roll back.
        with connection:
            employee_cursor = connection.execute("""
                INSERT INTO employees (
                    first_name, last_name, email,
                    department_id, designation, salary,
                    joining_date, status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data["first_name"].strip(),
                data["last_name"].strip(),
                email,
                department_id,
                data["designation"].strip(),
                salary,
                data["joining_date"],
                data["status"]
            ))

            employee_id = employee_cursor.lastrowid

            connection.execute("""
                INSERT INTO audit_logs (
                    action, entity_type, entity_id, details
                )
                VALUES (?, ?, ?, ?)
            """, (
                "CREATE",
                "employee",
                employee_id,
                f"Created employee with email {email}"
            ))

        # Reached here only after successful commit
        return jsonify({
            "message": "Employee created successfully",
            "employee_id": employee_id
        }), 201

    except sqlite3.IntegrityError as error:
        # The transaction has rolled back.
        if "UNIQUE constraint failed" in str(error):
            return jsonify({
                "error": "An employee with this email already exists"
            }), 409

        if "FOREIGN KEY constraint failed" in str(error):
            return jsonify({
                "error": "Department does not exist"
            }), 400

        return jsonify({
            "error": "Database constraint failed"
        }), 400

    except sqlite3.Error:
        app.logger.exception("Database error while creating employee")
        return jsonify({
            "error": "Database operation failed"
        }), 500

    finally:
        connection.close()


@app.route("/api/employees/<int:employee_id>", methods=["PUT"])
def update_employee(employee_id):
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Request body must be valid JSON"}), 400

    allowed_fields = {
        "first_name", "last_name", "email", "department_id",
        "designation", "salary", "joining_date", "status"
    }

    if not data or not set(data).issubset(allowed_fields):
        return jsonify({"error": "Invalid or empty fields"}), 400

    connection = get_db_connection()

    try:
        with connection:
            existing = connection.execute(
                "SELECT id FROM employees WHERE id = ?",
                (employee_id,)
            ).fetchone()

            if existing is None:
                return jsonify({"error": "Employee not found"}), 404

            # Validate the complete updated record.
            current = dict(connection.execute(
                "SELECT * FROM employees WHERE id = ?",
                (employee_id,)
            ).fetchone())

            updated = {**current, **data}

            for field in ("first_name", "last_name", "email", "designation", "joining_date", "status"):
                if not isinstance(updated[field], str) or not updated[field].strip():
                    return jsonify({"error": f"{field} must be non-empty text"}), 400

            if updated["status"] not in VALID_STATUSES:
                return jsonify({"error": "Invalid status"}), 400

            try:
                department_id = int(updated["department_id"])
                salary = float(updated["salary"])
            except (ValueError, TypeError):
                return jsonify({"error": "Invalid department_id or salary"}), 400

            if department_id <= 0 or salary < 0:
                return jsonify({"error": "Invalid department_id or salary"}), 400

            connection.execute("""
                UPDATE employees
                SET first_name = ?, last_name = ?, email = ?,
                    department_id = ?, designation = ?, salary = ?,
                    joining_date = ?, status = ?
                WHERE id = ?
            """, (
                updated["first_name"].strip(),
                updated["last_name"].strip(),
                updated["email"].strip().lower(),
                department_id,
                updated["designation"].strip(),
                salary,
                updated["joining_date"].strip(),
                updated["status"],
                employee_id
            ))

            connection.execute("""
                INSERT INTO audit_logs
                    (action, entity_type, entity_id, details)
                VALUES (?, ?, ?, ?)
            """, (
                "UPDATE", "employee", employee_id,
                "Updated employee record"
            ))

        return jsonify({"message": "Employee updated successfully"}), 200

    except sqlite3.IntegrityError:
        return jsonify({
            "error": "Duplicate email or invalid department"
        }), 409

    except sqlite3.Error:
        app.logger.exception("Database error while updating employee")
        return jsonify({"error": "Database operation failed"}), 500

    finally:
        connection.close()


@app.route("/api/employees/<int:employee_id>", methods=["DELETE"])
def delete_employee(employee_id):
    connection = get_db_connection()

    try:
        with connection:
            employee = connection.execute(
                "SELECT id, email FROM employees WHERE id = ?",
                (employee_id,)
            ).fetchone()

            if employee is None:
                return jsonify({"error": "Employee not found"}), 404

            connection.execute("""
                INSERT INTO audit_logs
                    (action, entity_type, entity_id, details)
                VALUES (?, ?, ?, ?)
            """, (
                "DELETE", "employee", employee_id,
                f"Deleted employee with email {employee['email']}"
            ))

            connection.execute(
                "DELETE FROM employees WHERE id = ?",
                (employee_id,)
            )

        return jsonify({"message": "Employee deleted successfully"}), 200

    except sqlite3.Error:
        app.logger.exception("Database error while deleting employee")
        return jsonify({"error": "Database operation failed"}), 500

    finally:
        connection.close()

if __name__ == "__main__":
    initialize_api_tables()
    app.run(debug=True)
