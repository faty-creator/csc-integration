"""
CSC Integration Quest — backend FastAPI

Sert le jeu (templates/csc-integration-quest.html) et persiste la progression
de chaque étudiant dans une base SQLite locale (csc.db), pour que le dashboard
admin (intégré dans la même page, à #admin) lise les vraies données via une
petite API JSON.

Installation:
    pip install fastapi uvicorn sqlalchemy jinja2 python-multipart

Lancer:
    python app.py

Puis ouvrir:
    http://127.0.0.1:8000/            -> le jeu
    http://127.0.0.1:8000/#admin      -> le dashboard admin
"""

import json
import os
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

# ---------------------------------------------------------------------------
# Base de données
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "csc.db")
DATABASE_URL = f"sqlite:///{DATABASE}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class StudentDB(Base):
    __tablename__ = "students"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False, default="New Explorer")
    field = Column(String, default="")
    year = Column(String, default="")
    language = Column(String, default="en")
    level_index = Column(Integer, default=0)
    xp = Column(Integer, default=0)
    completed = Column(Boolean, default=False)
    character = Column(Text, default="[]")   # JSON array
    skills = Column(Text, default="[]")      # JSON array
    contribution = Column(Text, default="")
    icebreaker_q = Column(Text, default="")
    icebreaker_a = Column(Text, default="")
    badge = Column(String, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


Base.metadata.create_all(bind=engine)


# ---------------------------------------------------------------------------
# Schémas Pydantic
# ---------------------------------------------------------------------------
class StudentSchema(BaseModel):
    id: str
    name: Optional[str] = "New Explorer"
    field: Optional[str] = ""
    year: Optional[str] = ""
    language: Optional[str] = "en"
    levelIndex: Optional[int] = 0
    xp: Optional[int] = 0
    completed: Optional[bool] = False
    character: Optional[List[str]] = []
    skills: Optional[List[str]] = []
    contribution: Optional[str] = ""
    icebreakerQ: Optional[str] = ""
    icebreakerA: Optional[str] = ""
    badge: Optional[str] = ""
    createdAt: Optional[str] = None


# ---------------------------------------------------------------------------
# App FastAPI
# ---------------------------------------------------------------------------
app = FastAPI(title="CSC Integration Quest API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def row_to_student(row: StudentDB) -> dict:
    """Convertit une ligne SQLAlchemy en JSON attendu par le frontend."""
    return {
        "id": row.id,
        "name": row.name,
        "field": row.field or "",
        "year": row.year or "",
        "language": row.language or "en",
        "levelIndex": row.level_index or 0,
        "xp": row.xp or 0,
        "completed": bool(row.completed),
        "character": json.loads(row.character) if row.character else [],
        "skills": json.loads(row.skills) if row.skills else [],
        "contribution": row.contribution or "",
        "icebreakerQ": row.icebreaker_q or "",
        "icebreakerA": row.icebreaker_a or "",
        "badge": row.badge or "",
        "createdAt": row.created_at.isoformat() if row.created_at else None,
    }


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="csc-integration-quest.html"
    )

# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------
@app.get("/api/students")
def list_students(db: Session = Depends(get_db)):
    rows = db.query(StudentDB).order_by(StudentDB.created_at.desc()).all()
    return [row_to_student(r) for r in rows]


@app.get("/api/students/{student_id}")
def get_student(student_id: str, db: Session = Depends(get_db)):
    row = db.query(StudentDB).filter(StudentDB.id == student_id).first()
    if row is None:
        raise HTTPException(status_code=404, detail="not_found")
    return row_to_student(row)


@app.post("/api/students")
def upsert_student(data: StudentSchema, db: Session = Depends(get_db)):
    existing = db.query(StudentDB).filter(StudentDB.id == data.id).first()

    if existing:
        existing.name = data.name
        existing.field = data.field
        existing.year = data.year
        existing.language = data.language
        existing.level_index = data.levelIndex
        existing.xp = data.xp
        existing.completed = data.completed
        existing.character = json.dumps(data.character or [])
        existing.skills = json.dumps(data.skills or [])
        existing.contribution = data.contribution
        existing.icebreaker_q = data.icebreakerQ
        existing.icebreaker_a = data.icebreakerA
        existing.badge = data.badge
        existing.updated_at = datetime.utcnow()
    else:
        created = datetime.utcnow()
        if data.createdAt:
            try:
                created = datetime.fromisoformat(data.createdAt.replace("Z", "+00:00"))
            except Exception:
                pass
        db.add(
            StudentDB(
                id=data.id,
                name=data.name,
                field=data.field,
                year=data.year,
                language=data.language,
                level_index=data.levelIndex,
                xp=data.xp,
                completed=data.completed,
                character=json.dumps(data.character or []),
                skills=json.dumps(data.skills or []),
                contribution=data.contribution,
                icebreaker_q=data.icebreakerQ,
                icebreaker_a=data.icebreakerA,
                badge=data.badge,
                created_at=created,
                updated_at=created,
            )
        )
    db.commit()
    return {"success": True, "message": "Progress saved"}


@app.get("/api/stats")
def stats(db: Session = Depends(get_db)):
    total = db.query(StudentDB).count()
    completed = db.query(StudentDB).filter(StudentDB.completed == True).count()  # noqa: E712
    in_progress = (
        db.query(StudentDB)
        .filter(StudentDB.completed == False, StudentDB.level_index > 0)  # noqa: E712
        .count()
    )
    return {
        "total": total,
        "completed": completed,
        "inProgress": in_progress,
        "notStarted": total - completed - in_progress,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)