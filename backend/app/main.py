"""
CodeProof Backend - FastAPI Main Application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.ENVIRONMENT == "production" else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="CodeProof API",
    version="1.0.0",
    description="Bitcoin Online Judge - Educational Programming Platform",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info("🚀 CodeProof Backend starting...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Database: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'configured'}")
    logger.info(f"CORS Origins: {settings.CORS_ORIGINS}")

    # Start block mining scheduler
    from app.jobs.block_miner import start_block_mining_scheduler
    start_block_mining_scheduler()
    logger.info("⛏️  Block mining scheduler initialized")

    # Start score recalculation scheduler (retroactive scoring)
    from app.jobs.score_updater import start_score_update_scheduler
    start_score_update_scheduler()
    logger.info("📊 Score recalculation scheduler initialized")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info("👋 CodeProof Backend shutting down...")


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint
    Returns API status and version
    """
    return {
        "status": "ok",
        "service": "CodeProof Backend",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT
    }


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint with API information
    """
    return {
        "message": "CodeProof API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health"
    }


# Include routers
from app.routes import auth, problems, submissions, ranking, users, blocks, admin, categories, editorials, setup

app.include_router(setup.router, prefix="/api/setup", tags=["Setup"])
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(problems.router, prefix="/api/problems", tags=["Problems"])
app.include_router(editorials.router, prefix="/api/problems", tags=["Editorials & Reference Files"])
app.include_router(submissions.router, prefix="/api/submissions", tags=["Submissions"])
app.include_router(ranking.router, prefix="/api/ranking", tags=["Ranking"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(blocks.router, prefix="/api/blocks", tags=["Blocks"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(categories.router, prefix="/api/categories", tags=["Categories"])
