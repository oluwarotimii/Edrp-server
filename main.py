import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from contextlib import asynccontextmanager
import uvicorn

from database import engine, Base
from routers import (
    schools, users, students, teachers, academic, 
    attendance, assessments, fees, communication, 
    timetable, admissions, admin, happenings, auth, super_admin
)
from utils.exceptions import setup_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    # We are now using Alembic for migrations, so we don't need to create tables here.
    yield


app = FastAPI(
    title="Education ERP System",
    description="A comprehensive multi-tenant Education ERP system",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup exception handlers
setup_exception_handlers(app)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(schools.router, prefix="/api", tags=["schools"])
app.include_router(users.role_router, prefix="/api", tags=["roles"])
app.include_router(users.permission_router, prefix="/api", tags=["permissions"])
app.include_router(super_admin.router, prefix="/api/super-admin", tags=["super-admin"])
app.include_router(students.router, prefix="/api", tags=["students"])
app.include_router(teachers.router, prefix="/api", tags=["teachers"])
app.include_router(academic.router, prefix="/api", tags=["academic"])
app.include_router(attendance.router, prefix="/api", tags=["attendance"])
app.include_router(assessments.router, prefix="/api", tags=["assessments"])
app.include_router(fees.router, prefix="/api", tags=["fees"])
app.include_router(communication.router, prefix="/api", tags=["communication"])
app.include_router(timetable.router, prefix="/api", tags=["timetable"])
app.include_router(admissions.router, prefix="/api", tags=["admissions"])
app.include_router(admin.router, prefix="/api", tags=["admin"])
app.include_router(happenings.router, prefix="/api", tags=["happenings"])

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_root():
    return FileResponse("static/index.html")

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    favicon_path = "static/favicon.ico"
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path)
    return Response(status_code=404)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Education ERP System is running"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
    )
