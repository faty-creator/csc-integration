# CSC Integration Quest 🚀

An interactive, gamified onboarding quest for new members of the **Computer Science Club (CSC)**. Students play through 5 short levels (who they are, their "character", their skills, an icebreaker, and a final badge), earning XP along the way — while club admins get a live dashboard of everyone who's joined.

Built with **Flask + SQLite** on the backend and a single self-contained **HTML/CSS/JS** frontend (no build step, no framework).

---

## ✨ Features

- 🎮 5-level onboarding quest with XP, progress tracking, and a celebration screen (confetti included)
- 🌍 Fully trilingual UI: **English / Français / العربية** (with RTL support for Arabic)
- 📊 Live admin dashboard (`/#admin`) — search, filter, and charts (by language, field, level, skills, character, completion rate)
- 🗄️ Shared SQLite database — every browser/device sees the **same** data (no more localStorage silos)
- 📱 QR code generation built in, so students can scan-and-join at an event
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
| GET    | `/qr`                  | Live QR code (PNG) → the site's own homepage   |
| GET    | `/qr?admin=1`          | Live QR code (PNG) → straight to `#admin`      |
| GET    | `/qr?url=<any-url>`    | Live QR code (PNG) → any URL you pass in       |

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

---

## 🖨️ Generating a printable QR code

```bash
python generate_qr.py "https://your-deployed-url.com/"
```

Saves `csc_quest_qr.png`. Bump `box_size` inside `generate_qr.py` for a higher-resolution version suitable for posters/flyers.

---

## ☁️ Deploying on PythonAnywhere

PythonAnywhere serves WSGI apps natively — Flask works out of the box, no extra wrapper needed.

1. Upload the project (via `git clone` in a PythonAnywhere Bash console, or the Files tab) to e.g. `/home/<you>/csc-integration/`.
2. In a console using your virtualenv:
   ```bash
   pip install -r requirements.txt
   ```
3. On the **Web** tab, open your **WSGI configuration file** and replace its contents with:
   ```python
   import sys

   path = '/home/<you>/csc-integration'
   if path not in sys.path:
       sys.path.insert(0, path)

   from app import app as application
   ```
4. Set **Source code** / **Working directory** to that same project folder.
5. Click the green **Reload** button.
6. Visit `https://<you>.pythonanywhere.com/` to confirm.

> ⚠️ Make sure there's no stale `csc.db` left over from an earlier attempt with a different schema — delete it and let the app recreate it fresh if you run into a `no such column` error.

---

## 🛠️ Tech stack

- **Backend:** Flask 3, SQLite (stdlib `sqlite3`, no ORM)
- **Frontend:** Vanilla JS (no framework), Chart.js (via CDN) for the admin dashboard charts
- **QR codes:** [`qrcode`](https://pypi.org/project/qrcode/) + Pillow

---

## 📄 License

Add your license of choice here (MIT, GPL, etc.) — none specified yet.
