# Nutrition Deficiency Prediction System

A full-stack, AI-powered web application that predicts nutrition deficiencies based on user inputs (symptoms, diet details, blood markers) and explains the predictions using SHAP (SHapley Additive exPlanations).

## Tech Stack
- **Frontend**: React (Vite, TypeScript), Tailwind CSS, React Router, Axios
- **Backend**: FastAPI, SQLAlchemy (PostgreSQL), Uvicorn, JWT Authentication
- **Machine Learning**: Scikit-Learn, XGBoost, SHAP

---

## Directory Structure

```
d:\nutrients/
├── backend/                  # FastAPI Application
│   ├── app/
│   │   ├── api/              # Route endpoints (v1/endpoints: auth, predict, history)
│   │   ├── core/             # Configuration, Database sessions, JWT Security
│   │   ├── models/           # SQLAlchemy Models
│   │   ├── schemas/          # Pydantic Schemas
│   │   ├── ml/               # XGBoost Model & SHAP Explainer Skeletons
│   │   └── tests/            # Test suite
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
├── frontend/                 # React Frontend App
│   ├── src/
│   │   ├── components/       # Layout, Navbar, Guards
│   │   ├── context/          # JWT Auth Context
│   │   ├── pages/            # Dashboard, Prediction, Login, Register
│   │   ├── services/         # Axios api service
│   │   └── router.tsx        # React Router config
│   ├── Dockerfile
│   ├── tailwind.config.js
│   └── package.json
├── docker-compose.yml        # Orchestrates Postgres, FastAPI, and Frontend services
└── README.md                 # System overview & developer guide
```

---

## Local Development Setup

### Backend (FastAPI)
1. Navigate to backend:
   ```bash
   cd backend
   ```
2. Create and activate virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On Unix/macOS:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure environment:
   ```bash
   cp .env.example .env
   ```
   *Note: Edit `.env` to specify your PostgreSQL connection credentials.*
5. Run migrations/start server:
   ```bash
   uvicorn app.main:app --reload
   ```

### Frontend (React/Vite)
1. Navigate to frontend:
   ```bash
   cd frontend
   ```
2. Install npm packages:
   ```bash
   npm install
   ```
3. Set environment parameters:
   ```bash
   cp .env.example .env
   ```
4. Start dev server:
   ```bash
   npm run dev
   ```

---

## Run with Docker Compose
To build and spin up the complete full stack (PostgreSQL + Backend + Frontend):
```bash
docker-compose up --build
```
- API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Frontend client: [http://localhost](http://localhost)
