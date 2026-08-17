# University Database Management System (Flask)

A full-stack registrar system with three roles — admin, instructor, and student — for managing departments, instructors, students, courses, enrollments, attendance, and grades.

## Stack

- **Framework:** Flask 3
- **ORM:** SQLAlchemy (via Flask-SQLAlchemy)
- **Auth:** Flask-Login + Werkzeug password hashing (PBKDF2, no native compiled dependency)
- **CSRF protection:** Flask-WTF (`CSRFProtect`) — every form includes a token
- **Database:** SQLite by default (zero config), or PostgreSQL via `DATABASE_URL`
- **Production server:** Gunicorn
- **Templates:** Jinja2 + Bootstrap 5 (CDN)

This stack was chosen specifically for easy deployment: no native binary downloads at install time (unlike Prisma), no separate web server or PHP runtime to configure (unlike the XAMPP-style PHP version) — just `pip install -r requirements.txt` and `gunicorn app:app`.

## Features

- **Admin:** full CRUD on Departments, Instructors, Students, Courses, and Enrollments. Assign instructors to courses per semester. Dashboard with live counts.
- **Instructor:** view assigned courses, mark attendance per class date, enter assignment/midterm/final marks — grades and GPA points calculate automatically.
- **Student:** view profile, enrollments, attendance percentage per course, and grades with a computed CGPA.
- Role-based access control enforced server-side (not just hidden UI) — verified: a student or instructor hitting an admin URL directly gets a 403, not just a redirect.
- CSRF tokens on every state-changing form, including deletes (deletes are POST-only, not GET links).
- Self-service password change for all three roles (requires current password to confirm).
- Self-service "Forgot password" flow with time-limited, single-use reset links. Works with zero setup for local/demo use (the link is logged to the server console if no SMTP is configured) and sends real email once `MAIL_SERVER` etc. are set.

## Local Setup

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env            # edit if you want Postgres; SQLite works with no changes

python seed.py                  # creates tables + demo data + accounts
python app.py                   # dev server at http://localhost:5000
```

Demo accounts (all password `password123`):

| Role | Username |
|---|---|
| Admin | `admin` |
| Instructor | `jsmith` (also `akhan`, `smalik`, `utariq`) |
| Student | `sfarooq` (also `mnaeem`, `ali_r`, `mnoor`) |

## Deploying (Render — easiest option)

1. Push this project to a GitHub repo.
2. In Render: **New → Web Service**, connect the repo.
3. Build command: `pip install -r requirements.txt`
   Start command: `gunicorn app:app`
   (Render sets `$PORT` automatically; the Procfile handles this too if Render auto-detects it.)
4. Add a **PostgreSQL** instance from Render's dashboard (free tier available), copy its internal connection string.
5. Set environment variables on the web service:
   - `DATABASE_URL` — the Postgres connection string from step 4
   - `SECRET_KEY` — a long random string (`python -c "import secrets; print(secrets.token_hex(32))"`)
   - Optional: `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_DEFAULT_SENDER` — if you want "Forgot password" to send real emails instead of logging the reset link to the server console.
6. After the first deploy, run the seed script once against production. Render's dashboard has a Shell tab for the running service — run `python seed.py` there, or run it locally with `DATABASE_URL` set to the production string.
7. Visit the deployed URL — you should land on `/login`.

**Railway, Fly.io, or PythonAnywhere** work the same way — this is a standard WSGI app with no platform-specific code. The only two things any host needs are: `pip install -r requirements.txt` and `gunicorn app:app` (or equivalent), plus the two env vars above.

**Note on SQLite in production:** if you deploy without setting `DATABASE_URL`, the app falls back to a local SQLite file. This works, but most hosting platforms (Render, Railway, Heroku) use an ephemeral filesystem — the file resets on every redeploy. Set `DATABASE_URL` to a real Postgres instance for anything beyond a quick demo.

## Project Structure

```
app.py                  App factory, blueprint registration, error handlers
config.py               Config (DATABASE_URL, SECRET_KEY)
extensions.py           db, login_manager, csrf singletons
models.py                All 9 tables + grade calculation logic
seed.py                   Demo data + admin/instructor/student accounts
blueprints/
  auth.py                 Login/logout
  admin.py                 All admin CRUD routes
  teacher.py               Instructor dashboard, attendance, marks entry
  student.py               Student dashboard, profile, enrollments, attendance, grades
  utils.py                  role_required() decorator
templates/
  base.html                 Sidebar shell, role-aware nav
  auth/, admin/, teacher/, student/, errors/
static/css/style.css        Design system (navy/gold registrar theme)
```


