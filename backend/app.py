from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from routers import users, matches, player_stats 
import os

# This creates the tables (users, matches, stats) in the DB
Base.metadata.create_all(bind=engine)

app = FastAPI()

# --- CORS CONFIGURATION ---
# Allow requests from Frontend (port 5173)
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # explicit origins are safer/better than "*" for credentials
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