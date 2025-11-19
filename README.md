# foosgoos
Foosball Stat Tracking App

# Running the Foosball Tracker App Locally

## Backend (FastAPI)
- Open a terminal and navigate to the `backend` directory.
- Install dependencies:
  ```bash
  pip install -r requirements.txt
- Start the backend server:
  ```bash
  uvicorn app:app --reload
- The backend API will be running at http://localhost:8000

## Frontend (React)
- Open a separate terminal and navigate to the `frontend` directory.
- Install dependencies:
  ```bash
  npm install
- Start the frontend development server:
  ```bash
  npm run dev
- The frontend will run on http://localhost:5173

## Setup .env
- You will need to add VITE_API_URL=http://127.0.0.1:8000 in your frontend/.env
