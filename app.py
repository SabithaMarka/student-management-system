"""
College Student Management System
===================================
Admin manages ALL student information.
Students can only VIEW their own information — nothing is editable by them.

Roles
-----
  admin   : full CRUD + all academic / fee / attendance management
  student : read-only view of their own profile

Run:  python app.py
URL:  http://127.0.0.1:5000
"""

import re
from functools import wraps

import pymysql
from flask import (
    Flask, flash, redirect, render_template,
    request, session, url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

from config import Config
from db import execute, fetch_all, fetch_one

# ── App setup ───────────────────────────────────────────────────────────────
app = Flask(__name__)
app.config.from_object(Config)

# ── Constants ────────────────────────────────────────────────────────────────
DEPARTMENTS = [
    "Computer Science Engineering",
    "Information Technology",
    "Electronics & Communication",
    "Electrical Engineering",
    "Mechanical Engineering",
    "Civil Engineering",
    "AI & Data Science",
    "MBA", "MCA",
]
COURSES      = ["B.Tech", "B.E.", "M.Tech", "MCA", "MBA", "B.Sc", "M.Sc"]
YEARS        = [1, 2, 3, 4]
SEMESTERS    = [1, 2, 3, 4, 5, 6, 7, 8]
GENDERS      = ["Male", "Female", "Other", "Prefer not to say"]
FEE_STATUSES = ["Fully Paid", "Half Paid", "Partially Paid", "Due", "Pending"]

EMAIL_PATTERN      = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
STUDENT_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{3,30}$")
ROLL_PATTERN       = re.compile(r"^[A-Za-z0-9/_-]{2,30}$")


# ── Helpers ──────────────────────────────────────────────────────────────────
def dberr(e):
    return (
        "Database connection failed. Check that MySQL is running and your "
        f".env DB_* values are correct. (MySQL: {e})"
    )

def clean_phone(raw):
    digits = re.sub(r"\D", "", raw or "")
    return digits if 10 <= len(digits) <= 15 else None

def validate_password(pw):
    if not pw:            return False, "Password is required."
    if len(pw) < 8:       return False, "Password must be at least 8 characters."
    if not re.search(r"[A-Za-z]", pw): return False, "Password must contain a letter."
    if not re.search(r"\d", pw):       return False, "Password must contain a digit."
    return True, ""

def dup_msg(e):
    m = str(e).lower()
    if "roll_number" in m: return "That Roll Number is already used by another student."
    if "student_id"  in m: return "That Student ID is already taken."
    if "email"       in m: return "That email is already registered."
    return "A duplicate value was detected. Check Student ID, Roll Number and Email."

# ── Auth decorators ───────────────────────────────────────────────────────────
def login_required(view):
    @wraps(view)
    def wrapped(*a, **kw):
        if "uid" not in session:
            flash("Please log in first.", "warning")
            return redirect(url_for("login"))
        return view(*a, **kw)
    return wrapped

def admin_required(view):
    @wraps(view)
    def wrapped(*a, **kw):
        if "uid" not in session:
            flash("Admin login required.", "warning")
            return redirect(url_for("admin_login"))
        if session.get("role") != "admin":
            flash("You do not have admin access.", "danger")
            return redirect(url_for("student_dashboard"))
        return view(*a, **kw)
    return wrapped

def student_required(view):
    @wraps(view)
    def wrapped(*a, **kw):
        if "uid" not in session:
            flash("Please log in first.", "warning")
            return redirect(url_for("student_login"))
        if session.get("role") != "student":
            return redirect(url_for("admin_dashboard"))
        return view(*a, **kw)
    return wrapped

def get_current_user():
    if "uid" not in session:
        return None
    try:
        return fetch_one("SELECT * FROM students WHERE id=%s", (session["uid"],))
    except pymysql.MySQLError:
        return None

@app.context_processor
def _inject():
    u = get_current_user()
    return {"current_user": u}


# ══════════════════════════════════════════════════════════════════════════════
# PUBLIC ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    return render_template("index.html")


# ── Admin Login ───────────────────────────────────────────────────────────────
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if session.get("role") == "admin":
        return redirect(url_for("admin_dashboard"))
    errors = []
    identifier = ""
    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        password   = request.form.get("password", "")
        if not identifier or not password:
            errors.append("Enter both username/email and password.")
        else:
            try:
                user = fetch_one(
                    "SELECT * FROM students WHERE role='admin' AND "
                    "(LOWER(email)=%s OR LOWER(student_id)=%s)",
                    (identifier.lower(), identifier.lower()),
                )
            except pymysql.MySQLError as e:
                errors.append(dberr(e)); user = None
            if not errors:
                if user is None:
                    errors.append("No admin account found with those credentials.")
                elif not check_password_hash(user["password_hash"], password):
                    errors.append("Incorrect password.")
                else:
                    session.clear()
                    session["uid"]  = user["id"]
                    session["role"] = "admin"
                    flash(f"Welcome, {user['name']}!", "success")
                    return redirect(url_for("admin_dashboard"))
    return render_template("admin_login.html", errors=errors, identifier=identifier)


# ── Student Login ─────────────────────────────────────────────────────────────
@app.route("/student/login", methods=["GET", "POST"])
def student_login():
    if session.get("role") == "student":
        return redirect(url_for("student_dashboard"))
    errors = []
    identifier = ""
    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        password   = request.form.get("password", "")
        if not identifier or not password:
            errors.append("Enter both email/Student ID and password.")
        else:
            try:
                user = fetch_one(
                    "SELECT * FROM students WHERE role='student' AND "
                    "(LOWER(email)=%s OR LOWER(student_id)=%s)",
                    (identifier.lower(), identifier.lower()),
                )
            except pymysql.MySQLError as e:
                errors.append(dberr(e)); user = None
            if not errors:
                if user is None:
                    errors.append("No student account found with those credentials.")
                elif not check_password_hash(user["password_hash"], password):
                    errors.append("Incorrect password.")
                else:
                    session.clear()
                    session["uid"]  = user["id"]
                    session["role"] = "student"
                    flash(f"Welcome, {user['name']}!", "success")
                    return redirect(url_for("student_dashboard"))
    return render_template("student_login.html", errors=errors, identifier=identifier)


# ── Student Registration ──────────────────────────────────────────────────────
@app.route("/register", methods=["GET", "POST"])
def register():
    """Students register their LOGIN credentials here.
    After registration, admin fills in their full academic profile.
    """
    if session.get("role") == "student":
        return redirect(url_for("student_dashboard"))
    errors = []
    fd = {f: "" for f in ["student_id", "name", "email", "phone", "department", "year"]}
    if request.method == "POST":
        sid  = request.form.get("student_id", "").strip()
        name = request.form.get("name", "").strip()
        email= request.form.get("email", "").strip().lower()
        phone= request.form.get("phone", "").strip()
        dept = request.form.get("department", "").strip()
        year_raw = request.form.get("year", "").strip()
        pw   = request.form.get("password", "")
        pw2  = request.form.get("confirm_password", "")
        fd   = {"student_id": sid, "name": name, "email": email,
                "phone": phone, "department": dept, "year": year_raw}

        if not sid or not STUDENT_ID_PATTERN.match(sid):
            errors.append("Student ID must be 3-30 letters, digits, dots, _ or -.")
        if not name:
            errors.append("Full name is required.")
        if not email or not EMAIL_PATTERN.match(email):
            errors.append("A valid email is required.")
        ph = clean_phone(phone)
        if ph is None:
            errors.append("Phone must be 10-15 digits.")
        else:
            fd["phone"] = ph
        if not dept:
            errors.append("Department is required.")
        try:
            year = int(year_raw)
            if year not in YEARS:
                raise ValueError
            fd["year"] = year
        except (ValueError, TypeError):
            errors.append("Select a valid year (1-4).")
        ok, msg = validate_password(pw)
        if not ok: errors.append(msg)
        if pw != pw2: errors.append("Passwords do not match.")

        if not errors:
            try:
                execute(
                    "INSERT INTO students "
                    "(student_id,name,email,phone,department,year,password_hash,role) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,'student')",
                    (sid, name, email, ph, dept, year, generate_password_hash(pw)),
                )
                flash("Registration successful! Please log in.", "success")
                return redirect(url_for("student_login"))
            except pymysql.err.IntegrityError as e:
                errors.append(dup_msg(e))
            except pymysql.MySQLError as e:
                errors.append(dberr(e))

    return render_template("register.html", fd=fd, errors=errors,
                           departments=DEPARTMENTS, years=YEARS)


@app.route("/logout")
def logout():
    role = session.get("role", "student")
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("admin_login") if role == "admin" else url_for("student_login"))


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN ROUTES
# ══════════════════════════════════════════════════════════════════════════════

# ── Dashboard ─────────────────────────────────────────────────────────────────
@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    stats = {}
    try:
        r = fetch_one("SELECT COUNT(*) AS c FROM students WHERE role='student'")
        stats["total_students"] = r["c"]
        r = fetch_one("SELECT COUNT(DISTINCT department) AS c FROM students WHERE role='student'")
        stats["total_departments"] = r["c"]
        r = fetch_one("SELECT COUNT(*) AS c FROM students WHERE role='student' AND backlogs > 0")
        stats["with_backlogs"] = r["c"]
        r = fetch_one("SELECT COUNT(*) AS c FROM students WHERE role='student' AND attendance_pct IS NOT NULL AND attendance_pct < 75")
        stats["att_shortage"] = r["c"]
        r = fetch_one("SELECT COUNT(*) AS c FROM students WHERE role='student' AND payment_status NOT IN ('Fully Paid')")
        stats["pending_fee"] = r["c"]
        r = fetch_one("SELECT COUNT(*) AS c FROM students WHERE role='student' AND payment_status='Fully Paid'")
        stats["fully_paid"] = r["c"]
    except pymysql.MySQLError as e:
        flash(dberr(e), "danger")
        stats = {k: "—" for k in ["total_students","total_departments","with_backlogs",
                                    "att_shortage","pending_fee","fully_paid"]}
    return render_template("admin_dashboard.html", **stats)


# ── Student List ──────────────────────────────────────────────────────────────
@app.route("/admin/students")
@admin_required
def admin_students():
    q           = request.args.get("q", "").strip()
    dept_filter = request.args.get("department", "").strip()
    year_filter = request.args.get("year", "").strip()
    backlog_f   = request.args.get("backlogs", "").strip()
    fee_f       = request.args.get("fee_status", "").strip()

    sql = ("SELECT id, student_id, roll_number, name, department, year, "
           "cgpa, backlogs, attendance_pct, payment_status "
           "FROM students WHERE role='student'")
    params = []
    if q:
        sql += " AND (student_id LIKE %s OR name LIKE %s OR email LIKE %s OR roll_number LIKE %s)"
        like = f"%{q}%"
        params += [like, like, like, like]
    if dept_filter:
        sql += " AND department=%s"; params.append(dept_filter)
    if year_filter:
        try: sql += " AND year=%s"; params.append(int(year_filter))
        except ValueError: pass
    if backlog_f == "yes":
        sql += " AND backlogs > 0"
    elif backlog_f == "no":
        sql += " AND backlogs = 0"
    if fee_f:
        sql += " AND payment_status=%s"; params.append(fee_f)
    sql += " ORDER BY name"

    try:
        students = fetch_all(sql, tuple(params))
        depts = [r["department"] for r in
                 fetch_all("SELECT DISTINCT department FROM students WHERE role='student' ORDER BY department")]
        db_error = None
    except pymysql.MySQLError as e:
        students, depts, db_error = [], [], dberr(e)

    return render_template("admin_students.html",
        students=students, q=q, dept_filter=dept_filter,
        year_filter=year_filter, backlog_f=backlog_f, fee_f=fee_f,
        departments=depts, years=YEARS, fee_statuses=FEE_STATUSES,
        db_error=db_error)


# ── Add Student ───────────────────────────────────────────────────────────────
@app.route("/admin/students/add", methods=["GET", "POST"])
@admin_required
def admin_add_student():
    errors = []
    fd = {}

    if request.method == "POST":
        fd, errors = _parse_student_form(request.form, require_password=True)
        if not errors:
            try:
                execute(
                    """INSERT INTO students
                    (student_id, roll_number, name, email, phone, dob, gender,
                     address, department, course, year, semester, section,
                     cgpa, backlogs, backlog_details, attendance_pct,
                     total_fee, amount_paid, amount_due, payment_status,
                     password_hash, role)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                            %s,%s,%s,%s,%s,%s,%s,%s,%s,'student')""",
                    (fd["student_id"], fd["roll_number"] or None,
                     fd["name"], fd["email"], fd["phone"],
                     fd["dob"] or None, fd["gender"] or None,
                     fd["address"] or None,
                     fd["department"], fd["course"] or None,
                     fd["year"], fd["semester"] or None, fd["section"] or None,
                     fd["cgpa"] or None, fd["backlogs"],
                     fd["backlog_details"] or None,
                     fd["attendance_pct"] or None,
                     fd["total_fee"], fd["amount_paid"],
                     fd["amount_due"], fd["payment_status"],
                     generate_password_hash(fd["password"])),
                )
                flash(f"Student \"{fd['name']}\" added successfully.", "success")
                return redirect(url_for("admin_students"))
            except pymysql.err.IntegrityError as e:
                errors.append(dup_msg(e))
            except pymysql.MySQLError as e:
                errors.append(dberr(e))

    return render_template("student_form.html",
        heading="Add New Student", submit_label="Add Student",
        fd=fd, errors=errors,
        departments=DEPARTMENTS, courses=COURSES,
        years=YEARS, semesters=SEMESTERS, genders=GENDERS,
        fee_statuses=FEE_STATUSES,
        cancel_url=url_for("admin_students"))


# ── View Student (admin) ──────────────────────────────────────────────────────
@app.route("/admin/students/<int:sid>")
@admin_required
def admin_view_student(sid):
    try:
        student = fetch_one(
            "SELECT * FROM students WHERE id=%s AND role='student'", (sid,))
    except pymysql.MySQLError as e:
        flash(dberr(e), "danger"); return redirect(url_for("admin_students"))
    if not student:
        flash("Student not found.", "warning"); return redirect(url_for("admin_students"))
    return render_template("view_student.html", student=student, admin_view=True)


# ── Edit Student ──────────────────────────────────────────────────────────────
@app.route("/admin/students/<int:sid>/edit", methods=["GET", "POST"])
@admin_required
def admin_edit_student(sid):
    try:
        student = fetch_one(
            "SELECT * FROM students WHERE id=%s AND role='student'", (sid,))
    except pymysql.MySQLError as e:
        flash(dberr(e), "danger"); return redirect(url_for("admin_students"))
    if not student:
        flash("Student not found.", "warning"); return redirect(url_for("admin_students"))

    errors = []
    # Pre-fill form from DB on GET
    fd = _student_to_fd(student)

    if request.method == "POST":
        fd, errors = _parse_student_form(request.form, require_password=False)
        if not errors:
            try:
                execute(
                    """UPDATE students SET
                    roll_number=%s, name=%s, email=%s, phone=%s, dob=%s, gender=%s,
                    address=%s, department=%s, course=%s, year=%s, semester=%s,
                    section=%s, cgpa=%s, backlogs=%s, backlog_details=%s,
                    attendance_pct=%s, total_fee=%s, amount_paid=%s,
                    amount_due=%s, payment_status=%s
                    WHERE id=%s""",
                    (fd["roll_number"] or None, fd["name"], fd["email"], fd["phone"],
                     fd["dob"] or None, fd["gender"] or None,
                     fd["address"] or None, fd["department"], fd["course"] or None,
                     fd["year"], fd["semester"] or None, fd["section"] or None,
                     fd["cgpa"] or None, fd["backlogs"],
                     fd["backlog_details"] or None,
                     fd["attendance_pct"] or None,
                     fd["total_fee"], fd["amount_paid"],
                     fd["amount_due"], fd["payment_status"],
                     sid),
                )
                flash(f"Student \"{fd['name']}\" updated successfully.", "success")
                return redirect(url_for("admin_view_student", sid=sid))
            except pymysql.err.IntegrityError as e:
                errors.append(dup_msg(e))
            except pymysql.MySQLError as e:
                errors.append(dberr(e))

    # Keep student_id read-only on edit
    fd["student_id"] = student["student_id"]
    return render_template("student_form.html",
        heading=f"Edit Student — {student['name']}",
        submit_label="Save Changes",
        fd=fd, errors=errors,
        departments=DEPARTMENTS, courses=COURSES,
        years=YEARS, semesters=SEMESTERS, genders=GENDERS,
        fee_statuses=FEE_STATUSES,
        is_edit=True,
        cancel_url=url_for("admin_view_student", sid=sid))


# ── Delete Student ────────────────────────────────────────────────────────────
@app.route("/admin/students/<int:sid>/delete", methods=["POST"])
@admin_required
def admin_delete_student(sid):
    try:
        r = fetch_one("SELECT name FROM students WHERE id=%s AND role='student'", (sid,))
        if r:
            execute("DELETE FROM students WHERE id=%s", (sid,))
            flash(f"Student \"{r['name']}\" deleted.", "success")
        else:
            flash("Student not found.", "warning")
    except pymysql.MySQLError as e:
        flash(dberr(e), "danger")
    return redirect(url_for("admin_students"))


# ── Form parse/fill helpers ────────────────────────────────────────────────────
def _parse_student_form(form, require_password=False):
    """Parse and validate the full student form. Returns (fd, errors)."""
    fd = {}
    errors = []

    fd["student_id"]   = form.get("student_id", "").strip()
    fd["roll_number"]  = form.get("roll_number", "").strip()
    fd["name"]         = form.get("name", "").strip()
    fd["email"]        = form.get("email", "").strip().lower()
    fd["phone"]        = form.get("phone", "").strip()
    fd["dob"]          = form.get("dob", "").strip() or None
    fd["gender"]       = form.get("gender", "").strip() or None
    fd["address"]      = form.get("address", "").strip() or None
    fd["department"]   = form.get("department", "").strip()
    fd["course"]       = form.get("course", "").strip() or None
    fd["section"]      = form.get("section", "").strip() or None
    fd["backlog_details"] = form.get("backlog_details", "").strip() or None
    fd["password"]     = form.get("password", "")
    fd["confirm"]      = form.get("confirm_password", "")

    # Student ID (required, immutable on edit — caller must override)
    if require_password:   # only new students need a fresh unique student_id check
        if not fd["student_id"] or not STUDENT_ID_PATTERN.match(fd["student_id"]):
            errors.append("Student ID must be 3-30 alphanumeric/._- characters.")
    # Roll number (optional unique)
    if fd["roll_number"] and not ROLL_PATTERN.match(fd["roll_number"]):
        errors.append("Roll Number must be 2-30 alphanumeric characters.")
    # Name
    if not fd["name"]:
        errors.append("Full name is required.")
    # Email
    if not fd["email"] or not EMAIL_PATTERN.match(fd["email"]):
        errors.append("A valid email address is required.")
    # Phone
    ph = clean_phone(fd["phone"])
    if ph is None:
        errors.append("Phone number must be 10-15 digits.")
    else:
        fd["phone"] = ph
    # Department
    if not fd["department"]:
        errors.append("Department is required.")
    # Year
    try:
        fd["year"] = int(form.get("year", ""))
        if fd["year"] not in YEARS: raise ValueError
    except (ValueError, TypeError):
        errors.append("Select a valid year (1-4)."); fd["year"] = ""
    # Semester (optional)
    sem_raw = form.get("semester", "").strip()
    fd["semester"] = int(sem_raw) if sem_raw.isdigit() and int(sem_raw) in SEMESTERS else None
    # CGPA (optional, 0.00 – 10.00)
    cgpa_raw = form.get("cgpa", "").strip()
    if cgpa_raw:
        try:
            fd["cgpa"] = float(cgpa_raw)
            if not (0 <= fd["cgpa"] <= 10): raise ValueError
        except ValueError:
            errors.append("CGPA must be a number between 0 and 10."); fd["cgpa"] = cgpa_raw
    else:
        fd["cgpa"] = None
    # Backlogs
    try:
        fd["backlogs"] = max(0, int(form.get("backlogs", "0")))
    except (ValueError, TypeError):
        fd["backlogs"] = 0
    # Attendance
    att_raw = form.get("attendance_pct", "").strip()
    if att_raw:
        try:
            fd["attendance_pct"] = float(att_raw)
            if not (0 <= fd["attendance_pct"] <= 100): raise ValueError
        except ValueError:
            errors.append("Attendance % must be 0-100."); fd["attendance_pct"] = att_raw
    else:
        fd["attendance_pct"] = None
    # Fee
    try:
        fd["total_fee"] = max(0.0, float(form.get("total_fee", "0") or 0))
    except (ValueError, TypeError):
        fd["total_fee"] = 0.0
    try:
        fd["amount_paid"] = max(0.0, float(form.get("amount_paid", "0") or 0))
    except (ValueError, TypeError):
        fd["amount_paid"] = 0.0
    # Auto-calculate amount_due
    fd["amount_due"] = max(0.0, fd["total_fee"] - fd["amount_paid"])
    fd["payment_status"] = form.get("payment_status", "Pending").strip()
    if fd["payment_status"] not in FEE_STATUSES:
        fd["payment_status"] = "Pending"

    # Password (only for new students)
    if require_password:
        ok, msg = validate_password(fd["password"])
        if not ok: errors.append(msg)
        if fd["password"] != fd["confirm"]:
            errors.append("Passwords do not match.")

    return fd, errors


def _student_to_fd(s):
    """Convert a DB row dict to a form-data dict for pre-filling the edit form."""
    fd = {k: (s.get(k) or "") for k in [
        "student_id","roll_number","name","email","phone","gender",
        "address","department","course","section","backlog_details",
    ]}
    fd["dob"]            = s["dob"].strftime("%Y-%m-%d") if s.get("dob") else ""
    fd["year"]           = s.get("year") or ""
    fd["semester"]       = s.get("semester") or ""
    fd["cgpa"]           = s.get("cgpa") or ""
    fd["backlogs"]       = s.get("backlogs") or 0
    fd["attendance_pct"] = s.get("attendance_pct") or ""
    fd["total_fee"]      = s.get("total_fee") or 0
    fd["amount_paid"]    = s.get("amount_paid") or 0
    fd["amount_due"]     = s.get("amount_due") or 0
    fd["payment_status"] = s.get("payment_status") or "Pending"
    return fd


# ══════════════════════════════════════════════════════════════════════════════
# STUDENT ROUTES  (view-only)
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/student/dashboard")
@student_required
def student_dashboard():
    user = get_current_user()
    if user is None:
        session.clear(); return redirect(url_for("student_login"))
    return render_template("student_dashboard.html", s=user)


@app.route("/student/profile")
@student_required
def student_profile():
    user = get_current_user()
    if user is None:
        session.clear(); return redirect(url_for("student_login"))
    return render_template("student_profile.html", s=user)


# ══════════════════════════════════════════════════════════════════════════════
# LEGACY redirect  (old /login → student login; old /dashboard → student dash)
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/login")
def login():
    return redirect(url_for("student_login"))

@app.route("/dashboard")
def dashboard():
    if session.get("role") == "admin":
        return redirect(url_for("admin_dashboard"))
    return redirect(url_for("student_dashboard"))


# ══════════════════════════════════════════════════════════════════════════════
# ERROR HANDLERS
# ══════════════════════════════════════════════════════════════════════════════
@app.errorhandler(404)
def not_found(_):
    return render_template("error.html", code=404,
                           message="The page you're looking for doesn't exist."), 404

@app.errorhandler(500)
def server_error(_):
    return render_template("error.html", code=500,
                           message="Something went wrong. Please try again."), 500


if __name__ == "__main__":
    import os
    # In Docker, Flask must bind to 0.0.0.0 so the container port is reachable.
    # Locally it stays on 127.0.0.1.
    host  = os.getenv("FLASK_RUN_HOST", "127.0.0.1")
    port  = int(os.getenv("FLASK_RUN_PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "1") == "1"
    app.run(host=host, port=port, debug=debug)
