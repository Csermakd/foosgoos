from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from migrations import run_migrations
from routers import users, matches, player_stats
import models  # noqa: F401  - registers every table with Base before create_all

# Create any missing tables, then add any missing columns to tables that
# already existed (create_all cannot do the second thing).
Base.metadata.create_all(bind=engine)
_applied = run_migrations(engine)
if _applied:
    print(f"[db] applied migrations: {', '.join(_applied)}")

app = FastAPI(title="Foosgoos API")

# --- CORS CONFIGURATION ---
# The tablet by the table hits this over the LAN, so localhost alone is
# not enough once you stop developing on the same machine. Add the camera
# PC's LAN address here (e.g. "http://192.168.1.42:5173") when you deploy.
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------ Routers ------------------------

app.include_router(users.router)
app.include_router(matches.router)
app.include_router(player_stats.router)

# ------------------------ Root ------------------------

@app.get("/")
def root():
    return {"status": "Goosfoos API is running"}


@app.get("/health")
def health():
    """Cheap liveness probe. The vision service pings this on startup so a
    misconfigured FOOSGOOS_API_URL fails loudly and immediately instead of
    silently dropping every goal it detects."""
    return {"ok": True}
