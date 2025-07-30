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
app.include_router(players_stats.router)

# Allow requests from frontend (needs to be fixed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------ models ------------------------


# class Tournament(BaseModel):
#     name: str
#     date: str  # ISO format or "YYYY-MM-DD" maybe???


# class Tip(BaseModel):
#     content: str

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


# @app.post("/tournaments")
# def create_tournament(tournament: Tournament):
#     return {"message": "Tournament created", "tournament": tournament}


# @app.get("/tournaments")
# def get_tournaments():
#     return [{"name": name, "date": date} for name, date in tournaments]


# @app.post("/tips")
# def submit_tip(tip: Tip):
#     return {"message": "Tip submitted", "tip": tip}


# @app.get("/tips")
# def get_tips():
#     return [{"content": content[0]} for content in tips]


# @app.post("/highlights")
# def upload_highlight(video: UploadFile = File(...)):
#     os.makedirs("videos", exist_ok=True)
#     file_location = f"videos/{uuid.uuid4()}_{video.filename}"
#     with open(file_location, "wb") as f:
#         f.write(video.file.read())
    
#     return {"message": "Video uploaded", "file_path": file_location}


# @app.get("/highlights")
# def list_highlights():
#     return [filepath[0] for filepath in highlights]

# ------------------------ Root ------------------------


@app.get("/")
def root():
    return {"status": "Goosfoos API with email verification is running"}
