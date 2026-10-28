# College Student Management System

A complete, containerized college portal built as a DevOps lab project.

**Admin** manages all student records.
**Students** securely view their own academic and administrative details — nothing is editable by them.

---

## Features

| Feature | Admin | Student |
|---|---|---|
| Login / Logout | ✅ | ✅ |
| Dashboard with statistics | ✅ (portal-wide) | ✅ (personal) |
| Add / Edit / Delete students | ✅ | ❌ |
| Search & filter students | ✅ | ❌ |
| View academic profile | ✅ | ✅ (own only) |
| Manage attendance | ✅ | View only |
| Manage CGPA & marks | ✅ | View only |
| Manage backlogs | ✅ | View only |
| Manage fee details | ✅ | View only |
| Role-based access control | ✅ | ✅ |
| Attendance shortage warning | — | ✅ |

---

## Technology Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, Flask 3 |
| Database | MySQL 8.0 |
| DB driver | PyMySQL + cryptography |
| Config | python-dotenv |
| Security | Werkzeug password hashing, Flask sessions |
| Frontend | Bootstrap 5, Bootstrap Icons, JavaScript |
| Container | Docker, Docker Compose |

---

## Project Structure

```
.
├── app.py                 # Flask application (all routes + logic)
├── config.py              # Reads configuration from env vars
├── db.py                  # MySQL connection + parameterized query helpers
├── requirements.txt
├── database.sql           # Complete schema + seed data (safe to re-run)
├── Dockerfile             # Flask application image
├── docker-compose.yml     # Flask + MySQL services
├── entrypoint.sh          # Waits for MySQL, applies schema, starts Flask
├── .dockerignore
├── .env.example           # Copy to .env and fill in values
├── .gitignore
├── README.md
├── migrations/
│   └── 001_upgrade_portal.sql
├── templates/             # Jinja2 HTML templates (23 files)
│   ├── base.html
│   ├── index.html
│   ├── admin_login.html
│   ├── student_login.html
│   ├── register.html
│   ├── admin_dashboard.html
│   ├── admin_students.html
│   ├── student_form.html  (add + edit)
│   ├── view_student.html
│   ├── student_dashboard.html
│   ├── student_profile.html
│   └── error.html
└── static/
    ├── css/style.css
    └── js/script.js
```

---

## Seed Accounts

All accounts use the password: **`password123`**

| Role | Login (Student ID or email) | Notes |
|---|---|---|
| Admin | `admin` / `admin@portal.local` | Full management access |
| Student | `STU001` / `alice@example.com` | CGPA 7.85, Att 84.5%, Half Paid |
| Student | `STU002` / `bob@example.com` | CGPA 8.20, Att 91%, Fully Paid |
| Student | `STU003` / `carol@example.com` | Att 68% ⚠️, 2 Backlogs, Pending fee |

---

## Option A — Run with Docker (Recommended)

### Prerequisites

- Docker Desktop installed and running
- `docker compose` command available

### Steps

```bash
# 1. Clone / download the project
cd "Student management System"

# 2. Copy the environment template
cp .env.example .env        # macOS / Linux
copy .env.example .env      # Windows

# 3. (Optional) Edit .env to set a strong SECRET_KEY and custom passwords
#    The defaults work out of the box for local testing.

# 4. Build and start both services
docker compose up --build

# 5. Open the application
#    http://localhost:5000
```

The first start takes ~60 seconds while:
1. MySQL initialises its data directory
2. The web container waits for MySQL to become healthy
3. `database.sql` is applied (schema + seed accounts)
4. Flask starts

### Useful Docker commands

```bash
# Start in background
docker compose up -d --build

# View logs
docker compose logs -f

# View only Flask logs
docker compose logs -f web

# View only MySQL logs
docker compose logs -f db

# Stop containers (data is preserved in the named volume)
docker compose down

# Stop and DELETE all data (full reset)
docker compose down -v

# Rebuild after code changes
docker compose up --build

# Open a MySQL shell inside the container
docker exec -it college_sms_db mysql -u sms_user -psms_password student_management

# Open a bash shell in the Flask container
docker exec -it college_sms_web bash
```

---

## Option B — Run Locally (Python + MySQL)

### Prerequisites

- Python 3.10+
- MySQL 8.0 running locally

### Steps

```powershell
# 1. Create and activate a virtual environment
python -m venv venv
.\venv\Scripts\activate          # Windows
# source venv/bin/activate       # macOS / Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy and configure .env
copy .env.example .env
# Edit .env: set DB_HOST=127.0.0.1, DB_USER=root, DB_PASSWORD=<your password>

# 4. Create the database and seed data
mysql -u root -p < database.sql

# 5. Run the Flask application
python app.py
```

Open http://127.0.0.1:5000

---

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `SECRET_KEY` | Flask session signing key | `docker-secret-change-me` |
| `DB_HOST` | MySQL hostname | `db` (Docker) / `127.0.0.1` (local) |
| `DB_PORT` | MySQL port | `3306` |
| `DB_NAME` | Database name | `student_management` |
| `DB_USER` | MySQL username | `sms_user` |
| `DB_PASSWORD` | MySQL password | `sms_password` |
| `DB_ROOT_PASSWORD` | MySQL root password (Docker only) | `rootpassword` |
| `FLASK_RUN_HOST` | Flask bind address | `0.0.0.0` (Docker) / `127.0.0.1` |
| `FLASK_DEBUG` | Debug mode (`1`/`0`) | `0` in Docker |

---

## User Flows

### Admin

```
http://localhost:5000
  → Click "Admin Login"
  → Login (admin / password123)
  → Admin Dashboard (6 stat tiles)
  → Add Student (full form: personal + academic + attendance + fee)
  → All Students (search, filter, view, edit, delete)
  → Edit Student → Save → changes visible on student's login
  → Logout
```

### Student

```
http://localhost:5000
  → Click "Student Login"  (or "Student Registration" for new accounts)
  → Login (STU001 / password123)
  → Student Dashboard (CGPA, attendance %, backlogs, fee status cards)
  → My Profile (view-only: all personal + academic + attendance + fee sections)
  → Logout
```

Students **cannot** edit any information. There are no edit buttons on student pages. Backend routes enforce this — changing the URL does not bypass the restriction.

---

## Routes

| Method | Route | Auth | Description |
|---|---|---|---|
| GET | `/` | Public | Landing page |
| GET/POST | `/admin/login` | Public | Admin login |
| GET/POST | `/student/login` | Public | Student login |
| GET/POST | `/register` | Public | Student self-registration |
| GET | `/logout` | Any | Logout |
| GET | `/admin/dashboard` | Admin | Admin dashboard |
| GET | `/admin/students` | Admin | Student list + filters |
| GET/POST | `/admin/students/add` | Admin | Add student |
| GET | `/admin/students/<id>` | Admin | View student |
| GET/POST | `/admin/students/<id>/edit` | Admin | Edit student |
| POST | `/admin/students/<id>/delete` | Admin | Delete student |
| GET | `/student/dashboard` | Student | Student dashboard |
| GET | `/student/profile` | Student | Student profile (view-only) |

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `web` container exits immediately | Run `docker compose logs web`. Usually MySQL isn't ready yet — the entrypoint will retry. |
| Port 5000 already in use | Change `"5000:5000"` to `"5001:5000"` in `docker-compose.yml`. |
| Port 3307 already in use | Change `"3307:3306"` to `"3308:3306"` or remove the ports block from `db`. |
| Login fails for seed accounts | Passwords may not have been seeded. Run `docker compose down -v` then `docker compose up --build` for a clean start. |
| `ModuleNotFoundError` locally | Activate the venv and run `pip install -r requirements.txt`. |
| `Unknown database` locally | Run `mysql -u root -p < database.sql` first. |
| DB connection error in Flask | Check `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` in your `.env`. |
| Can't connect from host to MySQL | MySQL is exposed on port **3307** (not 3306) to avoid conflicts. Use `127.0.0.1:3307`. |

---

## Security

- Passwords hashed with Werkzeug (scrypt) — never stored as plain text
- Role-based access: admin routes reject students server-side, not just by hiding buttons
- Students can only access their own profile — other students' IDs in the URL are rejected
- Parameterized SQL queries throughout — no SQL injection risk
- Secrets in `.env` (gitignored, never baked into the Docker image via `.dockerignore`)
- Session cookies signed with `SECRET_KEY`

---

## Future Improvements

- Nginx reverse proxy in front of Flask (production hardening)
- Gunicorn WSGI server instead of Flask's development server
- HTTPS / TLS termination
- Email notifications for low attendance / fee reminders
- PDF report generation for student records
- CI/CD pipeline (GitHub Actions)
