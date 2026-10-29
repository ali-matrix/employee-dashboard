
import sqlite3
import random
from datetime import date, timedelta
from pathlib import Path

# Database project folder mein hi create hogi
DB_PATH = Path(__file__).resolve().parent / "employees.db"

random.seed(42)

departments = [
    ("Engineering", "Software and product development"),
    ("Human Resources", "Recruitment and employee relations"),
    ("Marketing", "Brand and digital marketing"),
    ("Finance", "Accounting and financial planning"),
    ("Sales", "Customer acquisition and sales"),
    ("Operations", "Daily business operations"),
]

first_names = [
    "Ali", "Ahmed", "Usman", "Hamza", "Bilal",
    "Hassan", "Ayesha", "Fatima", "Zainab", "Sara",
    "Hira", "Maryam", "Saad", "Umar", "Zoya",
    "Danish", "Haris", "Amna", "Noor", "Farhan"
]

last_names = [
    "Khan", "Malik", "Ahmed", "Sheikh", "Butt",
    "Raza", "Iqbal", "Shah", "Ali", "Hussain"
]

roles = {
    "Engineering": [
        "Software Engineer", "Senior Developer",
        "QA Engineer", "Backend Developer"
    ],
    "Human Resources": [
        "HR Executive", "Recruiter", "HR Manager"
    ],
    "Marketing": [
        "Marketing Executive", "SEO Specialist",
        "Content Strategist"
    ],
    "Finance": [
        "Accountant", "Financial Analyst", "Finance Manager"
    ],
    "Sales": [
        "Sales Executive", "Account Manager", "Sales Manager"
    ],
    "Operations": [
        "Operations Officer", "Operations Analyst",
        "Operations Manager"
    ],
}


def initialize_database():
    connection = sqlite3.connect(DB_PATH)

    try:
        connection.execute("PRAGMA foreign_keys = ON")

        # Dono tables ko ek transaction mein create/seed karein
        with connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS departments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT
                )
            """)

            connection.execute("""
                CREATE TABLE IF NOT EXISTS employees (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    department_id INTEGER NOT NULL,
                    designation TEXT NOT NULL,
                    salary REAL NOT NULL CHECK (salary >= 0),
                    joining_date TEXT NOT NULL,
                    status TEXT NOT NULL
                        CHECK (status IN ('Active', 'On Leave', 'Inactive')),
                    FOREIGN KEY (department_id)
                        REFERENCES departments(id)
                )
            """)

            connection.executemany("""
                INSERT OR IGNORE INTO departments (name, description)
                VALUES (?, ?)
            """, departments)

            # Existing employees ko duplicate nahi karna
            existing = connection.execute(
                "SELECT COUNT(*) FROM employees"
            ).fetchone()[0]

            if existing == 0:
                department_rows = connection.execute(
                    "SELECT id, name FROM departments"
                ).fetchall()

                department_ids = {
                    name: department_id
                    for department_id, name in department_rows
                }

                employees = []

                for number in range(1, 101):
                    first = random.choice(first_names)
                    last = random.choice(last_names)
                    department = random.choice(departments)[0]
                    role = random.choice(roles[department])

                    email = (
                        f"{first.lower()}.{last.lower()}"
                        f"{number}@example.com"
                    )

                    joining_date = (
                        date.today()
                        - timedelta(days=random.randint(30, 2200))
                    ).isoformat()

                    status = random.choices(
                        ["Active", "On Leave", "Inactive"],
                        weights=[80, 10, 10],
                        k=1
                    )[0]

                    salary = random.randrange(35000, 180001, 5000)

                    employees.append((
                        first,
                        last,
                        email,
                        department_ids[department],
                        role,
                        salary,
                        joining_date,
                        status
                    ))

                connection.executemany("""
                    INSERT INTO employees (
                        first_name, last_name, email,
                        department_id, designation, salary,
                        joining_date, status
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, employees)

        print("Database initialized successfully!")
        print(f"Database location: {DB_PATH}")

        total = connection.execute(
            "SELECT COUNT(*) FROM employees"
        ).fetchone()[0]

        print(f"Employees: {total}")

        department_count = connection.execute(
            "SELECT COUNT(*) FROM departments"
        ).fetchone()[0]

        print(f"Departments: {department_count}")

    finally:
        connection.close()


if __name__ == "__main__":
    initialize_database()