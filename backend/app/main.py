import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.api import auth, transactions, loans, plan, dashboard, imports, budget, reports
from app.seed.init_db import init_database

settings = get_settings()

app = FastAPI(
    title="Stop The Monkey",
    description="58-month financial freedom tracker",
    version="1.0.0",
)

# CORS
origins = [o.strip() for o in settings.CORS_ORIGINS.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(transactions.router)
app.include_router(loans.router)
app.include_router(plan.router)
app.include_router(imports.router)
app.include_router(budget.router)
app.include_router(reports.router)


@app.on_event("startup")
def startup():
    os.makedirs("data", exist_ok=True)
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    init_database()


@app.get("/api/health")
def health_check():
    return {"status": "ok", "app": "Stop The Monkey"}
