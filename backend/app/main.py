import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.database.database import engine
from app.database.base import Base
from app.routers import (
    health, auth, admin, manufacturer, products, scans, verification, public, demo, issues
)

# Configure Logger
logging.basicConfig(level=logging.INFO if settings.DEBUG else logging.WARNING)
logger = logging.getLogger(__name__)

# Lifespan Context Manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.ENVIRONMENT.lower() == "production":
        insecure = [
            name for name, value, default in (
                ("SECRET_KEY", settings.SECRET_KEY, "super-secret-jwt-signing-key-authentiq-2026"),
                ("ADMIN_PASSWORD", settings.ADMIN_PASSWORD, "Admin@123456"),
            ) if not value or value == default
        ]
        if insecure:
            raise RuntimeError(f"Refusing to start in production with default {', '.join(insecure)}. Set them in .env.")
    logger.info("Initializing Database Schemas & Directories...")
    try:
        Base.metadata.create_all(bind=engine)
        from app.database.upgrade import ensure_new_columns
        ensure_new_columns(engine)
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        from app.services.blockchain_service import blockchain_service
        logger.info(f"Blockchain contract: {blockchain_service.ensure_contract()}")
        logger.info("Initialization completed successfully.")
    except Exception as e:
        logger.error(f"Startup initialization warning: {e}")
    yield
    logger.info("Shutting down Application Gateway...")

# Initialize FastAPI Application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    # Interactive API docs live under /api so they also work behind nginx (/api/docs).
    docs_url=None,   # served below with local Swagger UI files (works without internet)
    redoc_url=None,
    lifespan=lifespan
)

# CORS Middleware Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=(
        [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
        # development: allow any origin; production: only CORS_ORIGINS / CORS_ORIGIN_REGEX
        or ([] if settings.ENVIRONMENT.lower() == "production" else settings.ALLOWED_ORIGINS)
    ),
    allow_origin_regex=settings.CORS_ORIGIN_REGEX or None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Interactive API docs at /api/docs, using the Swagger UI files in app/static/swagger
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.staticfiles import StaticFiles

app.mount(
    f"{settings.API_V1_STR}/static",
    StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")),
    name="static",
)


@app.get(f"{settings.API_V1_STR}/docs", include_in_schema=False)
async def api_docs():
    return get_swagger_ui_html(
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        title=f"{settings.PROJECT_NAME} API",
        swagger_js_url=f"{settings.API_V1_STR}/static/swagger/swagger-ui-bundle.js",
        swagger_css_url=f"{settings.API_V1_STR}/static/swagger/swagger-ui.css",
        swagger_favicon_url="data:,",
    )


# Global Exception Handler for unexpected internal errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled server exception on {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal Server Error", "error": str(exc) if settings.DEBUG else "An unexpected error occurred."}
    )

# Include API Routers under /api prefix
app.include_router(health.router, prefix=settings.API_V1_STR)
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(admin.router, prefix=settings.API_V1_STR)
app.include_router(manufacturer.router, prefix=settings.API_V1_STR)
app.include_router(products.router, prefix=settings.API_V1_STR)
app.include_router(scans.router, prefix=settings.API_V1_STR)
app.include_router(verification.router, prefix=settings.API_V1_STR)
app.include_router(public.router, prefix=settings.API_V1_STR)
app.include_router(issues.router, prefix=settings.API_V1_STR)
app.include_router(demo.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
