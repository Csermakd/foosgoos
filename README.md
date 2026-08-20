# foosgoos

Foosball stat tracking. A camera above the table watches the game, calls
the goals, and the app records who scored what.

- **`ROADMAP.md`** — where the project is and what to do next. Start here.
- **`ml/README_ML_PIPELINE.md`** — how the vision half works, and how to
  train it.
- **`backend/hardware_tests/ARCHITECTURE.md`** — the camera hardware and
  the original design.

## How the pieces fit

```
┌──────────────────────┐
│  vision service      │  camera machine: owns the camera + the models
│  ml/vision_service   │  polls "is a game running?", records video,
└──────────┬───────────┘  POSTs a goal when it sees one
           │  HTTP
           ▼
┌──────────────────────┐
│  backend (FastAPI)   │  match lifecycle, the goal log, stats rollups
│  backend/            │  the only thing that owns the database
└──────────┬───────────┘
           │  HTTP + websocket
           ▼
┌──────────────────────┐
│  frontend (React)    │  the tablet by the table: live score, and one
│  frontend/           │  tap to confirm or correct what the camera saw
└──────────────────────┘
```

`ml/` and `backend/` never import from each other. The whole vision stack
can be replaced without the API noticing, and vice versa.

The camera answers exactly one question — *where is the ball?* — and
everything about what counts as a goal is ordinary Python in
`ml/inference/`, with thresholds we measure. That is why the goal logic
has tests that run with no camera and no GPU.

## Running it

### Backend (FastAPI)

```bash
cd backend
pip install -r requirements.txt
uvicorn app:app --reload          # http://localhost:8000
pytest -q                         # 23 tests
```

The database migrates itself on startup (`migrations.py`) — additive
columns only, no Alembic.

### Frontend (React)

```bash
cd frontend
npm install
npm run dev                       # http://localhost:5173
```

Needs `frontend/.env` containing:

```
VITE_API_URL=http://127.0.0.1:8000
```

### Vision service (camera machine)

```bash
cd ml
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python -m pytest tests -q         # no camera needed

export FOOSGOOS_API_URL=http://<backend-host>:8000
python -m vision_service --preview
```

It idles until someone starts a game in the app. See
`ml/README_ML_PIPELINE.md` for calibration and training — it will not
detect anything until the Scout model has been trained.

## Playing a game

1. **Create Game** — pick four players. This creates the match on the
   server, which is what tells the camera to start recording.
2. **Game Play** — tap goals as usual. When the camera is running, goals
   it detects appear already counted, marked for review; tap who scored,
   or "not a goal".
3. **Finish Match** — the final score is derived from the goal log, and
   the per-player stats roll up once.

A browser refresh mid-game is safe: the match lives on the server, not in
the tab.
