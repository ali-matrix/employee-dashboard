# Employee Management Dashboard

A web-based Employee Management Dashboard built using **Python Flask, SQLite, HTML, CSS, and JavaScript**.

This project provides an interactive interface to manage employee records, monitor workforce statistics, and perform CRUD operations through RESTful APIs.

## Features

- Interactive workforce dashboard
- Employee statistics and department summaries
- View all employees
- Search employees by name, email, and designation
- Filter employees by department and employment status
- Add new employee records
- Update existing employee information
- Delete employee records
- Input validation and error handling
- Audit logging for employee changes
- Database transactions for atomic operations

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Backend programming |
| Flask | Web framework and REST API |
| SQLite | Relational database |
| HTML5 | Dashboard structure |
| CSS3 | Styling and responsive layout |
| JavaScript | Frontend functionality |

## Project Structure

```text
employee-dashboard/
│
├── app.py
├── init_db.py
├── employees.db
├── .gitignore
│
├── templates/
│   └── index.html
│
└── static/
    └── style.css
```

> Note: The database file is generated locally and is excluded from version control.

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/ali-matrix/employee-dashboard.git
cd employee-dashboard
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate the virtual environment

Windows CMD:

```cmd
.venv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install Flask
```

### 5. Initialize the database

```bash
python init_db.py
```

### 6. Run the application

```bash
python app.py
```

Open your browser and visit:

`http://127.0.0.1:5000`

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Check API status |
| GET | `/api/employees` | Retrieve employees |
| GET | `/api/stats` | Retrieve dashboard statistics |
| POST | `/api/employees` | Create an employee |
| PUT | `/api/employees/<id>` | Update an employee |
| DELETE | `/api/employees/<id>` | Delete an employee |

### Query Parameters

The employee listing API supports:

- `search` — Search employees
- `department` — Filter by department
- `status` — Filter by employment status

Example:

```text
/api/employees?search=Fatima&status=Active
```

## Database & Transaction Management

The application uses SQLite with relational constraints, including unique employee emails, foreign keys, and salary validation.

Employee operations and their corresponding audit log entries are performed within database transactions to maintain atomicity.

## Future Improvements

- Authentication and role-based access
- Pagination
- Advanced analytics and charts
- Export employee records to CSV or Excel

## Author

**Muhammad Ali**

GitHub: [@ali-matrix](https://github.com/ali-matrix)