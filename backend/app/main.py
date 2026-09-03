import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import connect_db, close_db
from app.auth.router import router as auth_router
from app.users.router import router as users_router
from app.interns.router import router as interns_router
from app.schedules.router import router as schedules_router
from app.leave_requests.router import router as leave_router
from app.onboardings.router import router as onboardings_router
from app.documents.router import router as documents_router
from app.learning.router import router as learning_router
from app.dashboard.router import router as dashboard_router

# Trigger Uvicorn live reload
app = FastAPI(
    title="DevOps Intern Management API",
    version="2.0.0",
    description="Multi-tenant DevOps intern onboarding, scheduling, document AI analysis & learning roadmap platform.",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_db():
    await connect_db()


@app.on_event("shutdown")
async def shutdown_db():
    await close_db()


# Register Routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(interns_router)
app.include_router(schedules_router)
app.include_router(leave_router)
app.include_router(onboardings_router)
app.include_router(documents_router)
app.include_router(learning_router)
app.include_router(dashboard_router)


@app.get("/")
@app.get("/health")
@app.get("/api/health")
async def root():
    return {"message": "DevOps Intern Platform API v2.0 is running", "status": "ok"}


@app.api_route("/api/schedules/public", methods=["GET", "POST"])
async def public_schedules_fallback():
    return {"status": "ok", "message": "Health probe OK"}
