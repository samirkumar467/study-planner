import os
import sqlite3
from functools import wraps

from flask import Flask, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "database.db")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "student-planner-dev-secret")


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    conn = sqlite3.connect(DATABASE_PATH)
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS study (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            topic TEXT NOT NULL,
            days INTEGER NOT NULL,
            completed INTEGER DEFAULT 0,
            user TEXT NOT NULL
        )
        """
    )

    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username ON users(username)")
    conn.commit()
    conn.close()


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped_view


def verify_password(stored_password, provided_password):
    if stored_password == provided_password:
        return True, generate_password_hash(provided_password)

    try:
        return check_password_hash(stored_password, provided_password), None
    except ValueError:
        return False, None


@app.context_processor
def inject_user():
    return {"current_user": session.get("user")}


@app.route("/", methods=["GET"])
def root():
    if "user" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if len(username) < 3:
            flash("Username must be at least 3 characters long.", "error")
            return render_template("signup.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "error")
            return render_template("signup.html")

        db = get_db()
        try:
            db.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, generate_password_hash(password)),
            )
            db.commit()
        except sqlite3.IntegrityError:
            flash("That username is already taken. Try another one.", "error")
            return render_template("signup.html")

        flash("Account created. Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
@app.route("/index", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,),
        ).fetchone()

        if user:
            password_ok, upgraded_hash = verify_password(user["password"], password)
            if password_ok:
                if upgraded_hash:
                    db.execute(
                        "UPDATE users SET password = ? WHERE id = ?",
                        (upgraded_hash, user["id"]),
                    )
                    db.commit()

                session["user"] = username
                flash("Welcome back. Your planner is ready.", "success")
                return redirect(url_for("dashboard"))

        flash("Invalid username or password.", "error")

    return render_template("index.html")


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    session.pop("user", None)
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


@app.route("/dashboard", methods=["GET"])
@login_required
def dashboard():
    db = get_db()
    tasks = db.execute(
        "SELECT * FROM study WHERE user = ? ORDER BY completed ASC, days ASC, id DESC",
        (session["user"],),
    ).fetchall()

    total = len(tasks)
    done = sum(1 for task in tasks if task["completed"])
    remaining = total - done
    progress = int((done / total) * 100) if total else 0
    upcoming = min((task["days"] for task in tasks if not task["completed"]), default=None)

    return render_template(
        "dashboard.html",
        tasks=tasks,
        progress=progress,
        done=done,
        remaining=remaining,
        total=total,
        upcoming=upcoming,
        user=session["user"],
    )


@app.route("/add", methods=["POST"])
@login_required
def add():
    subject = request.form.get("subject", "").strip()
    topic = request.form.get("topic", "").strip()
    days = request.form.get("days", "").strip()

    if not subject or not topic or not days:
        flash("All task fields are required.", "error")
        return redirect(url_for("dashboard"))

    try:
        days_value = int(days)
    except ValueError:
        flash("Days left must be a number.", "error")
        return redirect(url_for("dashboard"))

    if days_value < 0:
        flash("Days left cannot be negative.", "error")
        return redirect(url_for("dashboard"))

    db = get_db()
    db.execute(
        "INSERT INTO study (subject, topic, days, user) VALUES (?, ?, ?, ?)",
        (subject, topic, days_value, session["user"]),
    )
    db.commit()

    flash("Task added to your study plan.", "success")
    return redirect(url_for("dashboard"))


@app.route("/complete/<int:task_id>", methods=["POST"])
@login_required
def complete(task_id):
    db = get_db()
    result = db.execute(
        "UPDATE study SET completed = 1 WHERE id = ? AND user = ?",
        (task_id, session["user"]),
    )
    db.commit()

    if result.rowcount:
        flash("Task marked as complete.", "success")
    else:
        flash("Task not found.", "error")

    return redirect(url_for("dashboard"))


init_db()


if __name__ == "__main__":
    app.run(debug=True)
