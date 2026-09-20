"""
CSC Integration Quest — Flask backend (SQLite storage)

This is a WSGI-native version, built specifically to deploy cleanly on
PythonAnywhere (which serves WSGI apps directly — no ASGI wrapper needed,
unlike the FastAPI version). Same API contract as the FastAPI version:
GET/POST /api/students, GET /api/stats — the frontend JS doesn't change.

Run locally:
    pip install -r requirements.txt
    python app.py
    (or: flask --app app run --debug --port 8000)

Then open http://127.0.0.1:8000/            (student quest)
and     http://127.0.0.1:8000/#admin        (admin dashboard)

Deploy on PythonAnywhere:
    WSGI file just needs:
        import sys
        path = '/home/<you>/<project-folder>'
        if path not in sys.path:
            sys.path.insert(0, path)
        from app import app as application
"""

import json
import io
import os
import sqlite3
from datetime import datetime, timezone

try:
    import qrcode
except ImportError:
    qrcode = None

from flask import Flask, abort, jsonify, render_template, request, send_file

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "csc.db")

app = Flask(__name__, template_folder=os.path.join(BASE_DIR, "templates"))


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_conn()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS students (
            id          TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            field       TEXT,
            year        TEXT,
            language    TEXT,
            levelIndex  INTEGER DEFAULT 0,
            xp          INTEGER DEFAULT 0,
            completed   INTEGER DEFAULT 0,
            character   TEXT,
            skills      TEXT,               -- JSON-encoded list of strings
            badge       TEXT,
            email       TEXT,
            phone       TEXT,
            filiere     TEXT,
            createdAt   TEXT NOT NULL
        )
        """
    )
    conn.commit()

    # Auto-migration: if this is an older csc.db created before email/phone/
    # filiere existed, add the missing columns instead of erroring out.
    existing_cols = {row["name"] for row in conn.execute("PRAGMA table_info(students)").fetchall()}
    for col in ("email", "phone", "filiere"):
        if col not in existing_cols:
            conn.execute(f"ALTER TABLE students ADD COLUMN {col} TEXT")
    conn.commit()
    conn.close()


init_db()


def row_to_student(row: sqlite3.Row) -> dict:
    keys = row.keys()
    return {
        "id": row["id"],
        "name": row["name"],
        "field": row["field"],
        "year": row["year"],
        "language": row["language"],
        "levelIndex": row["levelIndex"],
        "xp": row["xp"],
        "completed": bool(row["completed"]),
        "character": row["character"],
        "skills": json.loads(row["skills"]) if row["skills"] else [],
        "badge": row["badge"],
        "email": (row["email"] if "email" in keys else "") or "",
        "phone": (row["phone"] if "phone" in keys else "") or "",
        "filiere": (row["filiere"] if "filiere" in keys else "") or "",
        "createdAt": row["createdAt"],
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("csc-integration-quest.html")


@app.route("/api/students", methods=["GET"])
def list_students():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM students ORDER BY createdAt DESC").fetchall()
    conn.close()
    return jsonify([row_to_student(r) for r in rows])


@app.route("/api/students", methods=["POST"])
def upsert_student():
    data = request.get_json(force=True, silent=True) or {}
    student_id = data.get("id")
    if not student_id:
        abort(400, description="id is required")

    name = data.get("name") or "New Explorer"
    field = data.get("field") or "—"
    year = data.get("year") or "—"
    language = data.get("language") or "en"
    level_index = int(data.get("levelIndex") or 0)
    xp = int(data.get("xp") or 0)
    completed = 1 if data.get("completed") else 0
    character = data.get("character") or ""
    skills = data.get("skills") or []
    badge = data.get("badge") or ""
    email = data.get("email") or ""
    phone = data.get("phone") or ""
    filiere = data.get("filiere") or ""
    created_at = data.get("createdAt") or datetime.now(timezone.utc).isoformat()

    conn = get_conn()
    conn.execute(
        """
        INSERT INTO students
            (id, name, field, year, language, levelIndex, xp, completed, character, skills, badge, email, phone, filiere, createdAt)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            name        = excluded.name,
            field       = excluded.field,
            year        = excluded.year,
            language    = excluded.language,
            levelIndex  = excluded.levelIndex,
            xp          = excluded.xp,
            completed   = excluded.completed,
            character   = excluded.character,
            skills      = excluded.skills,
            badge       = excluded.badge,
            email       = excluded.email,
            phone       = excluded.phone,
            filiere     = excluded.filiere
            -- createdAt is intentionally NOT overwritten on update
        """,
        (
            student_id, name, field, year, language, level_index, xp,
            completed, character, json.dumps(skills), badge,
            email, phone, filiere, created_at,
        ),
    )
    conn.commit()

    row = conn.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    conn.close()
    return jsonify(row_to_student(row))


@app.route("/api/students/<student_id>", methods=["DELETE"])
def delete_student(student_id):
    conn = get_conn()
    cur = conn.execute("DELETE FROM students WHERE id = ?", (student_id,))
    conn.commit()
    conn.close()
    if cur.rowcount == 0:
        abort(404, description="Student not found")
    return jsonify({"status": "deleted", "id": student_id})


@app.route("/qr")
def qr_code():
    """
    Live QR code, generated on the fly.
    - /qr                         -> QR for this site's own homepage
    - /qr?url=https://example.com -> QR for any URL you pass in
    - /qr?admin=1                 -> QR straight to the #admin dashboard
    """
    if qrcode is None:
        abort(501, description="qrcode package is not installed on the server (pip install qrcode[pil])")

    if request.args.get("admin"):
        target = request.host_url.rstrip("/") + "/#admin"
    else:
        target = request.args.get("url") or request.host_url

    img = qrcode.make(target)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return send_file(buf, mimetype="image/png")


@app.route("/api/stats")
def get_stats():
    conn = get_conn()
    rows = conn.execute("SELECT completed, levelIndex FROM students").fetchall()
    conn.close()
    total = len(rows)
    completed = sum(1 for r in rows if r["completed"])
    in_progress = sum(1 for r in rows if not r["completed"] and r["levelIndex"] > 0)
    return jsonify({"total": total, "completed": completed, "in_progress": in_progress})


if __name__ == "__main__":
    # Local dev server. On PythonAnywhere, this block never runs —
    # the WSGI file imports `app` directly instead.
    app.run(debug=True, host="0.0.0.0", port=8000)