from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from api.routers import auth, receipts, web
from utils.logger import setup_logging

# Initialize structured logging
setup_logging()

# Instantiate the FastAPI application
app = FastAPI(
    title="Financial Tracker Web API",
    description="Receipt processing pipeline with web UI, AI extraction, and caching.",
    version="1.0.0",
)

# Mount static files (CSS, JS, images)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Web UI routes (server-rendered HTML)
app.include_router(web.router, tags=["Web UI"])

# API routes
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(receipts.router, prefix="/api/v1/receipts", tags=["Receipts Core Pipeline"])


@app.get("/health")
async def health_check():
    """Liveness probe for load balancers and monitoring."""
    return {"status": "ok"}

