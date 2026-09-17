"""
CSC Integration Quest — backend

Serves the game (templates/csc-integration-quest.html) and persists each
student's progress to a local SQLite database (csc.db), so the admin
dashboard (built into the same page, at #admin) can read real data back
through a small JSON API.

Run:
    pip install flask
    python app.py

Then open:
    http://127.0.0.1:5000/            -> the quest
    http://127.0.0.1:5000/#admin      -> the admin dashboard
"""

import json
import os
import sqlite3
from datetime import datetime, timezone

from flask import Flask, g, jsonify, render_template, request

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "csc.db")
app.config["DATABASE"] = DATABASE

init_db()


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_db():
    """Return a SQLite connection cached on the request context."""
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Create the students table if it doesn't exist yet, and add any
    columns that are missing from an older version of the table (so an
    existing csc.db from a previous run never crashes the app)."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS students (
            id            TEXT PRIMARY KEY,
            name          TEXT NOT NULL,
            field         TEXT,
            year          TEXT,
            language      TEXT,
            level_index   INTEGER DEFAULT 0,
            xp            INTEGER DEFAULT 0,
            completed     INTEGER DEFAULT 0,
            character     TEXT,
            skills        TEXT,
            contribution  TEXT,
            icebreaker_q  TEXT,
            icebreaker_a  TEXT,
            badge         TEXT,
            created_at    TEXT,
            updated_at    TEXT
        )
        """
    )
    conn.commit()

    expected_columns = {
        "name": "TEXT",
        "field": "TEXT",
        "year": "TEXT",
        "language": "TEXT",
        "level_index": "INTEGER DEFAULT 0",
        "xp": "INTEGER DEFAULT 0",
        "completed": "INTEGER DEFAULT 0",
        "character": "TEXT",
        "skills": "TEXT",
        "contribution": "TEXT",
        "icebreaker_q": "TEXT",
        "icebreaker_a": "TEXT",
        "badge": "TEXT",
        "created_at": "TEXT",
        "updated_at": "TEXT",
    }
    existing_columns = {
        row[1] for row in cursor.execute("PRAGMA table_info(students)").fetchall()
    }
    for column, col_type in expected_columns.items():
        if column not in existing_columns:
            cursor.execute(f"ALTER TABLE students ADD COLUMN {column} {col_type}")
    conn.commit()
    conn.close()


def row_to_student(row):
    """Convert a sqlite3.Row into the JSON shape the frontend expects."""
    return {
        "id": row["id"],
        "name": row["name"],
        "field": row["field"],
        "year": row["year"],
        "language": row["language"],
        "levelIndex": row["level_index"],
        "xp": row["xp"],
        "completed": bool(row["completed"]),
        "character": row["character"],
        "skills": json.loads(row["skills"]) if row["skills"] else [],
        "contribution": row["contribution"],
        "icebreakerQ": row["icebreaker_q"],
        "icebreakerA": row["icebreaker_a"],
        "badge": row["badge"],
        "createdAt": row["created_at"],
    }


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

@app.route("/")
def home():
    return render_template("csc-integration-quest.html")


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

@app.route("/api/students", methods=["GET"])
def list_students():
    """Used by the admin dashboard to load every student's live progress."""
    db = get_db()
    rows = db.execute(
        "SELECT * FROM students ORDER BY created_at DESC"
    ).fetchall()
    return jsonify([row_to_student(r) for r in rows])


@app.route("/api/students/<student_id>", methods=["GET"])
def get_student(student_id):
    db = get_db()
    row = db.execute(
        "SELECT * FROM students WHERE id = ?", (student_id,)
    ).fetchone()
    if row is None:
        return jsonify({"error": "not_found"}), 404
    return jsonify(row_to_student(row))


@app.route("/api/students", methods=["POST"])
def upsert_student():
    """
    Called by the game every time a level is completed (an "upsert": insert
    the student on their first submission, then update the same row as
    they progress through the quest).
    """
    data = request.get_json(silent=True) or {}

    student_id = data.get("id")
    if not student_id:
        return jsonify({"error": "missing_id"}), 400

    name = data.get("name", "New Explorer")
    field = data.get("field", "")
    year = data.get("year", "")
    language = data.get("language", "en")
    level_index = int(data.get("levelIndex", 0))
    xp = int(data.get("xp", 0))
    completed = 1 if data.get("completed") else 0
    character = data.get("character", "")
    skills = json.dumps(data.get("skills", []))
    contribution = data.get("contribution", "")
    icebreaker_q = data.get("icebreakerQ", "")
    icebreaker_a = data.get("icebreakerA", "")
    badge = data.get("badge", "")
    created_at = data.get("createdAt") or datetime.now(timezone.utc).isoformat()
    updated_at = datetime.now(timezone.utc).isoformat()

    db = get_db()
    existing = db.execute(
        "SELECT id FROM students WHERE id = ?", (student_id,)
    ).fetchone()

    if existing:
        db.execute(
            """
            UPDATE students SET
                name = ?, field = ?, year = ?, language = ?, level_index = ?,
                xp = ?, completed = ?, character = ?, skills = ?,
                contribution = ?, icebreaker_q = ?, icebreaker_a = ?,
                badge = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                name, field, year, language, level_index, xp, completed,
                character, skills, contribution, icebreaker_q, icebreaker_a,
                badge, updated_at, student_id,
            ),
        )
    else:
        db.execute(
            """
            INSERT INTO students
                (id, name, field, year, language, level_index, xp, completed,
                 character, skills, contribution, icebreaker_q, icebreaker_a,
                 badge, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                student_id, name, field, year, language, level_index, xp,
                completed, character, skills, contribution, icebreaker_q,
                icebreaker_a, badge, created_at, updated_at,
            ),
        )
    db.commit()

    return jsonify({"success": True, "message": "Progress saved"})


@app.route("/api/stats", methods=["GET"])
def stats():
    """Small aggregate endpoint, handy if you build a separate admin client."""
    db = get_db()
    total = db.execute("SELECT COUNT(*) AS n FROM students").fetchone()["n"]
    completed = db.execute(
        "SELECT COUNT(*) AS n FROM students WHERE completed = 1"
    ).fetchone()["n"]
    in_progress = db.execute(
        "SELECT COUNT(*) AS n FROM students WHERE completed = 0 AND level_index > 0"
    ).fetchone()["n"]
    return jsonify({
        "total": total,
        "completed": completed,
        "inProgress": in_progress,
        "notStarted": total - completed - in_progress,
    })


if __name__ == "__main__":
    init_db()
    app.run(debug=True)