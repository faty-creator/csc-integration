# CSC Integration Quest 🚀

An interactive, gamified onboarding quest for new members of the **Computer Science Club (CSC)**. Students play through 5 short levels (who they are, their "character", their skills, an icebreaker, and a final badge), earning XP along the way — while club admins get a live dashboard of everyone who's joined.

Built with **Flask + SQLite** on the backend and a single self-contained **HTML/CSS/JS** frontend (no build step, no framework).

---

## ✨ Features

- 🎮 5-level onboarding quest with XP, progress tracking, and a celebration screen (confetti included)
- 🌍 Fully trilingual UI: **English / Français / العربية** (with RTL support for Arabic)
- 📊 Live admin dashboard (`/#admin`) — search, filter, and charts (by language, field, level, skills, character, completion rate)
- 🗄️ Shared SQLite database — every browser/device sees the **same** data (no more localStorage silos)
- 🪶 Zero frontend build step — one HTML file, vanilla JS, Chart.js from CDN

---

## 📁 Project structure

```
.
├── app.py                          # Flask app: routes + SQLite storage
├── requirements.txt
├── generate_qr.py                  # standalone script: printable QR PNG
├── templates/
│   └── csc-integration-quest.html  # the entire frontend (quest + admin dashboard)
└── csc.db                          # created automatically on first run
```

---

## 🚀 Quick start (local)

```bash
git clone https://github.com/<your-username>/csc-integration-quest.git
cd csc-integration-quest

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
python app.py
```

Then open:
- **http://127.0.0.1:8000/** — the quest itself
- **http://127.0.0.1:8000/#admin** — the live admin dashboard
- **http://127.0.0.1:8000/qr** — QR code pointing at the quest (great for posters)

`csc.db` is created automatically next to `app.py` on first run — no manual setup needed.

---

## 🔌 API reference

| Method | Path                   | Description                                  |
|--------|------------------------|-----------------------------------------------|
| GET    | `/`                    | Serves the quest / admin dashboard (same page, routed by `#hash`) |
| GET    | `/api/students`        | List all students, most recent first          |
| POST   | `/api/students`        | Create or update a student (upsert by `id`)    |
| DELETE | `/api/students/<id>`   | Remove a student                               |
| GET    | `/api/stats`           | Quick totals: total / completed / in-progress  |

Example student payload (`POST /api/students`):

```json
{
  "id": "p-abc123",
  "name": "Fatima Ezzahra",
  "field": "AI",
  "year": "2nd year",
  "language": "fr",
  "levelIndex": 4,
  "xp": 1000,
  "completed": true,
  "character": "strategist",
  "skills": ["dev", "ai", "data"],
  "badge": "CSC EXPLORER"
}
```




## 🛠️ Tech stack

- **Backend:** Flask 3, SQLite (stdlib `sqlite3`, no ORM)
- **Frontend:** Vanilla JS (no framework), Chart.js (via CDN) for the admin dashboard charts

---

## 📄 License

Add your license of choice here (MIT, GPL, etc.) — none specified yet.
