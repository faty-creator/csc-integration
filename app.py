# """
# CSC Integration Quest — backend FastAPI

# Sert le jeu (templates/csc-integration-quest.html) et persiste la progression
# de chaque étudiant dans une base SQLite locale (csc.db), pour que le dashboard
# admin (intégré dans la même page, à #admin) lise les vraies données via une
# petite API JSON.

# Installation:
#     pip install fastapi uvicorn sqlalchemy jinja2 python-multipart

# Lancer:
#     python app.py

# Puis ouvrir:
#     http://127.0.0.1:8000/            -> le jeu
#     http://127.0.0.1:8000/#admin      -> le dashboard admin
# """

# import json
# import os
# from datetime import datetime
# from typing import List, Optional

# from fastapi import FastAPI, Depends, HTTPException, Request
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.responses import HTMLResponse
# from fastapi.templating import Jinja2Templates
# from pydantic import BaseModel
# from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, create_engine
# from sqlalchemy.orm import Session, declarative_base, sessionmaker

# # ---------------------------------------------------------------------------
# # Base de données
# # ---------------------------------------------------------------------------
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# DATABASE = os.path.join(BASE_DIR, "csc.db")
# DATABASE_URL = f"sqlite:///{DATABASE}"

# engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Base = declarative_base()


# class StudentDB(Base):
#     __tablename__ = "students"

#     id = Column(String, primary_key=True, index=True)
#     name = Column(String, nullable=False, default="New Explorer")
#     field = Column(String, default="")
#     year = Column(String, default="")
#     language = Column(String, default="en")
#     level_index = Column(Integer, default=0)
#     xp = Column(Integer, default=0)
#     completed = Column(Boolean, default=False)
#     character = Column(Text, default="[]")   # JSON array
#     skills = Column(Text, default="[]")      # JSON array
#     contribution = Column(Text, default="")
#     icebreaker_q = Column(Text, default="")
#     icebreaker_a = Column(Text, default="")
#     badge = Column(String, default="")
#     created_at = Column(DateTime, default=datetime.utcnow)
#     updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Base.metadata.create_all(bind=engine)


# # ---------------------------------------------------------------------------
# # Schémas Pydantic
# # ---------------------------------------------------------------------------
# class StudentSchema(BaseModel):
#     id: str
#     name: Optional[str] = "New Explorer"
#     field: Optional[str] = ""
#     year: Optional[str] = ""
#     language: Optional[str] = "en"
#     levelIndex: Optional[int] = 0
#     xp: Optional[int] = 0
#     completed: Optional[bool] = False
#     character: Optional[List[str]] = []
#     skills: Optional[List[str]] = []
#     contribution: Optional[str] = ""
#     icebreakerQ: Optional[str] = ""
#     icebreakerA: Optional[str] = ""
#     badge: Optional[str] = ""
#     createdAt: Optional[str] = None


# # ---------------------------------------------------------------------------
# # App FastAPI
# # ---------------------------------------------------------------------------
# app = FastAPI(title="CSC Integration Quest API")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()


# def row_to_student(row: StudentDB) -> dict:
#     """Convertit une ligne SQLAlchemy en JSON attendu par le frontend."""
#     return {
#         "id": row.id,
#         "name": row.name,
#         "field": row.field or "",
#         "year": row.year or "",
#         "language": row.language or "en",
#         "levelIndex": row.level_index or 0,
#         "xp": row.xp or 0,
#         "completed": bool(row.completed),
#         "character": json.loads(row.character) if row.character else [],
#         "skills": json.loads(row.skills) if row.skills else [],
#         "contribution": row.contribution or "",
#         "icebreakerQ": row.icebreaker_q or "",
#         "icebreakerA": row.icebreaker_a or "",
#         "badge": row.badge or "",
#         "createdAt": row.created_at.isoformat() if row.created_at else None,
#     }


# # ---------------------------------------------------------------------------
# # Pages
# # ---------------------------------------------------------------------------
# @app.get("/", response_class=HTMLResponse)
# def home(request: Request):
#     return templates.TemplateResponse(
#         request=request,
#         name="csc-integration-quest.html"
#     )

# # ---------------------------------------------------------------------------
# # API
# # ---------------------------------------------------------------------------
# @app.get("/api/students")
# def list_students(db: Session = Depends(get_db)):
#     rows = db.query(StudentDB).order_by(StudentDB.created_at.desc()).all()
#     return [row_to_student(r) for r in rows]


# @app.get("/api/students/{student_id}")
# def get_student(student_id: str, db: Session = Depends(get_db)):
#     row = db.query(StudentDB).filter(StudentDB.id == student_id).first()
#     if row is None:
#         raise HTTPException(status_code=404, detail="not_found")
#     return row_to_student(row)


# @app.post("/api/students")
# def upsert_student(data: StudentSchema, db: Session = Depends(get_db)):
#     existing = db.query(StudentDB).filter(StudentDB.id == data.id).first()

#     if existing:
#         existing.name = data.name
#         existing.field = data.field
#         existing.year = data.year
#         existing.language = data.language
#         existing.level_index = data.levelIndex
#         existing.xp = data.xp
#         existing.completed = data.completed
#         existing.character = json.dumps(data.character or [])
#         existing.skills = json.dumps(data.skills or [])
#         existing.contribution = data.contribution
#         existing.icebreaker_q = data.icebreakerQ
#         existing.icebreaker_a = data.icebreakerA
#         existing.badge = data.badge
#         existing.updated_at = datetime.utcnow()
#     else:
#         created = datetime.utcnow()
#         if data.createdAt:
#             try:
#                 created = datetime.fromisoformat(data.createdAt.replace("Z", "+00:00"))
#             except Exception:
#                 pass
#         db.add(
#             StudentDB(
#                 id=data.id,
#                 name=data.name,
#                 field=data.field,
#                 year=data.year,
#                 language=data.language,
#                 level_index=data.levelIndex,
#                 xp=data.xp,
#                 completed=data.completed,
#                 character=json.dumps(data.character or []),
#                 skills=json.dumps(data.skills or []),
#                 contribution=data.contribution,
#                 icebreaker_q=data.icebreakerQ,
#                 icebreaker_a=data.icebreakerA,
#                 badge=data.badge,
#                 created_at=created,
#                 updated_at=created,
#             )
#         )
#     db.commit()
#     return {"success": True, "message": "Progress saved"}


# @app.get("/api/stats")
# def stats(db: Session = Depends(get_db)):
#     total = db.query(StudentDB).count()
#     completed = db.query(StudentDB).filter(StudentDB.completed == True).count()  # noqa: E712
#     in_progress = (
#         db.query(StudentDB)
#         .filter(StudentDB.completed == False, StudentDB.level_index > 0)  # noqa: E712
#         .count()
#     )
#     return {
#         "total": total,
#         "completed": completed,
#         "inProgress": in_progress,
#         "notStarted": total - completed - in_progress,
#     }


# if __name__ == "__main__":
#     import uvicorn

#     uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)





"""
CSC Integration Quest — FastAPI backend

Replaces the old localStorage-based "database" with a real shared store:
FastAPI + SQLite. Every browser/device now reads and writes the SAME
data through /api/students, so the admin dashboard is actually shared.

Run locally:
    pip install -r requirements.txt
    uvicorn app:app --reload --host 0.0.0.0 --port 8000

Then open http://127.0.0.1:8000/  (student quest)
and     http://127.0.0.1:8000/#admin (admin dashboard)
"""

import json
import os
import sqlite3
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Paths / DB setup — BASE_DIR-relative so csc.db always resolves to the same
# file regardless of the working directory the server was launched from.
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "csc.db")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

app = FastAPI(title="CSC Integration Quest API")

# CORS is wide-open here since the quest page and API are served from the
# same origin in normal use; tighten this if you split frontend/backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory=TEMPLATES_DIR)


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
            createdAt   TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


init_db()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class StudentIn(BaseModel):
    id: str
    name: str = Field(default="New Explorer")
    field: Optional[str] = "—"
    year: Optional[str] = "—"
    language: Optional[str] = "en"
    levelIndex: int = 0
    xp: int = 0
    completed: bool = False
    character: Optional[str] = ""
    skills: Optional[List[str]] = []
    badge: Optional[str] = ""
    createdAt: Optional[str] = None


class StudentOut(StudentIn):
    createdAt: str


def row_to_student(row: sqlite3.Row) -> dict:
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
        "createdAt": row["createdAt"],
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request=request, name="csc-integration-quest.html")


@app.get("/api/students", response_model=List[StudentOut])
def list_students():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM students ORDER BY createdAt DESC").fetchall()
    conn.close()
    return [row_to_student(r) for r in rows]


@app.post("/api/students", response_model=StudentOut)
def upsert_student(student: StudentIn):
    if not student.id:
        raise HTTPException(status_code=400, detail="id is required")

    created_at = student.createdAt or datetime.now(timezone.utc).isoformat()

    conn = get_conn()
    conn.execute(
        """
        INSERT INTO students
            (id, name, field, year, language, levelIndex, xp, completed, character, skills, badge, createdAt)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            badge       = excluded.badge
            -- createdAt is intentionally NOT overwritten on update
        """,
        (
            student.id,
            student.name,
            student.field,
            student.year,
            student.language,
            student.levelIndex,
            student.xp,
            int(student.completed),
            student.character,
            json.dumps(student.skills or []),
            student.badge,
            created_at,
        ),
    )
    conn.commit()

    row = conn.execute("SELECT * FROM students WHERE id = ?", (student.id,)).fetchone()
    conn.close()
    return row_to_student(row)


@app.delete("/api/students/{student_id}")
def delete_student(student_id: str):
    conn = get_conn()
    cur = conn.execute("DELETE FROM students WHERE id = ?", (student_id,))
    conn.commit()
    conn.close()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Student not found")
    return {"status": "deleted", "id": student_id}


@app.get("/api/stats")
def get_stats():
    conn = get_conn()
    rows = conn.execute("SELECT completed, levelIndex FROM students").fetchall()
    conn.close()
    total = len(rows)
    completed = sum(1 for r in rows if r["completed"])
    in_progress = sum(1 for r in rows if not r["completed"] and r["levelIndex"] > 0)
    return {"total": total, "completed": completed, "in_progress": in_progress}


# Optional: serve a /static folder if you add one later (favicon, extra assets, etc.)
static_dir = os.path.join(BASE_DIR, "static")
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")