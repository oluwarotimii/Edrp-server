import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import traceback
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from contextlib import asynccontextmanager
import uvicorn

# Load config first to ensure all environment variables are set
import config

from database import engine, Base
from initialization import initialize_super_admin
from routers import (
    schools, users, students, teachers, academic,
    attendance, assessments, fees, communication,
    timetable, admissions, admin, happenings, auth, super_admin, roles, subdomains, subscriptions,
    email_templates, grading_profiles, report_templates, global_settings
)
from utils.exceptions import setup_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    # We are now using Alembic for migrations, so we don't need to create tables here.

    # Initialize super admin user if it doesn't exist
    from database import SessionLocal
    db = SessionLocal()
    try:
        initialize_super_admin(db)
    finally:
        db.close()

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
def setup_exception_handlers(app: FastAPI):
    @app.exception_handler(Exception)
    async def exception_handler(request: Request, exc: Exception):
        error_trace = traceback.format_exc()
        return JSONResponse(
            status_code=500,
            content={
                "detail": str(exc),
                "traceback": error_trace
            }
        )

setup_exception_handlers(app)

# --- Router Registration ---

# System-level management for Super Admins
app.include_router(roles.router, tags=["System Management (Super Admin)"]) # Prefix is /api/system
app.include_router(super_admin.router, prefix="/api/super-admin", tags=["System Management (Super Admin)"])
app.include_router(email_templates.router, prefix="/api/super-admin", tags=["Email Templates (Super Admin)"])
app.include_router(grading_profiles.router, prefix="/api/system", tags=["System Management (Super Admin)"])
app.include_router(report_templates.router, prefix="/api/system", tags=["System Management (Super Admin)"])
app.include_router(global_settings.router, prefix="/api/super-admin", tags=["System Management (Super Admin)"])

# School-level management for School Admins
app.include_router(users.role_router, prefix="/api/school", tags=["School Role Management (School Admin)"])
app.include_router(users.permission_router, prefix="/api/school", tags=["School Role Management (School Admin)"])
app.include_router(admin.router, prefix="/api/admin", tags=["School Management (School Admin)"]) # General school admin tasks

# Core application endpoints
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["User Management"])
app.include_router(subscriptions.router)  # No prefix as it's already set in the router
app.include_router(schools.router, prefix="/api", tags=["Schools"])
app.include_router(students.router, prefix="/api", tags=["Students"])
app.include_router(teachers.router, prefix="/api", tags=["Teachers"])
app.include_router(academic.router, prefix="/api", tags=["Academic"])
app.include_router(attendance.router, prefix="/api", tags=["Attendance"])
app.include_router(assessments.router, prefix="/api", tags=["Assessments"])
app.include_router(fees.router, prefix="/api", tags=["Fees"])
app.include_router(communication.router, prefix="/api", tags=["Communication"])
app.include_router(timetable.router, prefix="/api", tags=["Timetable"])
app.include_router(admissions.router, prefix="/api", tags=["Admissions"])
app.include_router(happenings.router, prefix="/api", tags=["Happenings"])

# Include subdomain router and middleware
app.include_router(subdomains.router)
subdomains.register_subdomain_routes(app)

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
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    is_production = os.environ.get("ENVIRONMENT", "development").lower() == "production"
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=not is_production,
        workers=4 if is_production else 1,
        log_level="info"
    )
