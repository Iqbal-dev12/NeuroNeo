"""
app/main.py
FastAPI application entry point.

Start with:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger

from app.database.db import Base, check_db_connection, engine
from app.routes.pain_routes import router as pain_router
from app.routes.auth_routes import router as auth_router
from app.services.prediction_service import initialise_model
from app.utils.image_utils import UPLOAD_DIR, configure_logging

# ─── Logging (configure before anything else) ─────────────────────────────────
configure_logging()


# ─── Lifespan (startup / shutdown) ───────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──────────────────────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info("  Neonatal Pain Detection API  –  Starting up …")
    logger.info("=" * 60)

    # 1. Create all database tables
    logger.info("Creating database tables …")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables OK")
    except Exception as exc:
        logger.critical("Failed to create DB tables: {}", exc)
        raise

    # 2. Verify DB connectivity
    if check_db_connection():
        logger.info("MySQL connection verified ✓")
    else:
        logger.error("MySQL connection check FAILED — verify credentials in db.py")

    # 3. Warm-up the AI model
    logger.info("Initialising AI model (MobileNetV2) …")
    try:
        initialise_model()
        logger.info("AI model loaded ✓")
    except Exception as exc:
        logger.error("Model initialisation failed: {}. Predictions will error at runtime.", exc)

    logger.info("Startup complete – API is ready.")
    logger.info("Swagger UI → http://localhost:8000/docs")

    yield  # ── application runs here ─────────────────────────────────────────

    # ── Shutdown ─────────────────────────────────────────────────────────────
    logger.info("Shutting down Neonatal Pain Detection API …")


# ─── App factory ─────────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    application = FastAPI(
        title="Neonatal Facial Expression Recognition – Pain Detection API",
        description=(
            "Backend API for detecting pain levels in neonates using "
            "MobileNetV2 transfer learning, MediaPipe face detection, "
            "and Grad-CAM explainability.\n\n"
            "**Pain classes**: No Pain | Mild Pain | Moderate Pain | Severe Pain"
        ),
        version="1.0.0",
        contact={
            "name": "Infant Pain Detection Team",
            "email": "team@infantpain.dev",
        },
        license_info={"name": "MIT"},
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # ── CORS ─────────────────────────────────────────────────────────────────
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],          # tighten in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Static files (serve uploaded images + heatmaps) ──────────────────────
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    application.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

    # ── Routers ──────────────────────────────────────────────────────────────
    application.include_router(auth_router, prefix="/api")
    application.include_router(pain_router, prefix="/api/pain")

    return application


app = create_app()


# ─── Root endpoint ────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"], summary="API root / health check")
def root():
    return {
        "message": "Neonatal Pain Detection API is running 🚀",
        "docs": "/docs",
        "version": "1.0.0",
    }
