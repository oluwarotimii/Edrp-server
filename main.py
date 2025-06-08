import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import uvicorn

from database import engine, Base
from routers import (
    schools, users, students, teachers, academic, 
    attendance, assessments, fees, communication, 
    timetable, admissions, admin, happenings
)
from utils.exceptions import setup_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create database tables
    Base.metadata.create_all(bind=engine)
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
app.include_router(schools.router, prefix="/api", tags=["schools"])
app.include_router(users.router, prefix="/api/auth", tags=["authentication"])
app.include_router(users.role_router, prefix="/api", tags=["roles"])
app.include_router(users.permission_router, prefix="/api", tags=["permissions"])
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

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Education ERP System is running"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5000,
        reload=True
    )
