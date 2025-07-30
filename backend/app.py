from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Optional
import uuid
import os
import sqlite3
import smtplib
from email.mime.text import MIMEText
from routers import users, matches

app = FastAPI()

# routers
app.include_router(users.router)
app.include_router(matches.router)

# Allow requests from frontend (needs to be fixed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------ Database connection ------------------------
DB_FILE = "foosgoos.db"

if not os.path.exists(DB_FILE):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE matches (id INTEGER PRIMARY KEY, team_a TEXT, team_b TEXT, score_a INTEGER, score_b INTEGER)''')
    c.execute('''CREATE TABLE tournaments (id INTEGER PRIMARY KEY, name TEXT, date TEXT)''')
    c.execute('''CREATE TABLE tips (id INTEGER PRIMARY KEY, content TEXT)''')
    c.execute('''CREATE TABLE highlights (id INTEGER PRIMARY KEY, filepath TEXT)''')
    c.execute('''CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT UNIQUE, is_verified INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

# ------------------------ models ------------------------


class Tournament(BaseModel):
    name: str
    date: str  # ISO format or "YYYY-MM-DD" maybe???


class Tip(BaseModel):
    content: str


class UserEmail(BaseModel):
    email: EmailStr

# ------------------------ Email functionality ------------------------


def send_verification_email(email: str):
    # just an idea, would replace with actual config
    sender = "example@email.com"
    password = "password"
    smtp_server = "smtp.gmail.com"
    smtp_port = 587

    # connects to Gmail’s mail server
    # port 587 to safely send emails using STARTTLS encryption

    verification_link = f"http://localhost:5000/verify?email={email}"
    body = f"Click the link to verify your account: {verification_link}"
    msg = MIMEText(body)
    msg["Subject"] = "Please Verify your Goosfoos Account"
    msg["From"] = sender
    msg["To"] = email

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender, password)
            server.send_message(msg)
    except Exception as e:
        print("Email sending failed:", e)

# ------------------------ Routes ------------------------


@app.post("/auth/register")
def register_user(user: UserEmail, background_tasks: BackgroundTasks):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (email) VALUES (?)", (user.email,))
        conn.commit()
    except sqlite3.IntegrityError:
        return {"message": "Email already registered"}
    finally:
        conn.close()

    background_tasks.add_task(send_verification_email, user.email)
    return {"message": "Verification email sent"}


@app.post("/tournaments")
def create_tournament(tournament: Tournament):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO tournaments (name, date) VALUES (?, ?)", (tournament.name, tournament.date))
    conn.commit()
    conn.close()
    return {"message": "Tournament created", "tournament": tournament}


@app.get("/tournaments")
def get_tournaments():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT name, date FROM tournaments")
    tournaments = c.fetchall()
    conn.close()
    return [{"name": name, "date": date} for name, date in tournaments]


@app.post("/tips")
def submit_tip(tip: Tip):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO tips (content) VALUES (?)", (tip.content,))
    conn.commit()
    conn.close()
    return {"message": "Tip submitted", "tip": tip}


@app.get("/tips")
def get_tips():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT content FROM tips")
    tips = c.fetchall()
    conn.close()
    return [{"content": content[0]} for content in tips]


@app.post("/highlights")
def upload_highlight(video: UploadFile = File(...)):
    os.makedirs("videos", exist_ok=True)
    file_location = f"videos/{uuid.uuid4()}_{video.filename}"
    with open(file_location, "wb") as f:
        f.write(video.file.read())
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO highlights (filepath) VALUES (?)", (file_location,))
    conn.commit()
    conn.close()
    return {"message": "Video uploaded", "file_path": file_location}


@app.get("/highlights")
def list_highlights():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT filepath FROM highlights")
    highlights = c.fetchall()
    conn.close()
    return [filepath[0] for filepath in highlights]

# ------------------------ Root ------------------------


@app.get("/")
def root():
    return {"status": "Goosfoos API with SQLite and email verification is running"}
