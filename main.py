import os

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from database import engine
from api import match_engine, test_bench, youth_workbench, youth_academy, kit_designer, sponsor_workbench

app = FastAPI()

_PROTECTED_PREFIXES = (
    "/kit-designer",
    "/api/test-bench",
    "/api/youth-workbench",
    "/api/youth-academy",
    "/api/sponsor-workbench",
)
_OPEN_PATHS = {
    "/",
    "/db-check",
    "/openapi.json",
    "/docs",
    "/redoc",
    "/favicon.ico",
}


@app.middleware("http")
async def workbench_token_guard(request: Request, call_next):
    """Protect workbench routes when WORKBENCH_ACCESS_TOKEN is configured."""
    path = request.url.path

    if path in _OPEN_PATHS:
        return await call_next(request)

    if path.startswith("/docs") or path.startswith("/redoc") or path.startswith("/openapi"):
        return await call_next(request)

    if any(path.startswith(prefix) for prefix in _PROTECTED_PREFIXES):
        expected = os.getenv("WORKBENCH_ACCESS_TOKEN", "").strip()
        if expected:
            provided = (
                request.headers.get("X-Workbench-Token")
                or request.query_params.get("token")
                or request.query_params.get("workbench_token")
                or ""
            ).strip()
            if provided != expected:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Unauthorized: invalid or missing workbench token"},
                )

    return await call_next(request)

@app.on_event("startup")
def startup():
    # Only initialize database if engine is available
    if engine is not None:
        from models.base import Base
        import models  # Import models only if database is available
        Base.metadata.create_all(bind=engine)

@app.get("/")
def health():
    return {"status": "ok"}


@app.get("/db-check")
def db_check():
    if engine is not None:
        return {"db": "connected"}
    else:
        return {"db": "not configured (match engine mode)"}

# Include routers
app.include_router(match_engine.router)
app.include_router(test_bench.router)
app.include_router(youth_workbench.router)
app.include_router(youth_academy.router)
app.include_router(kit_designer.router)
app.include_router(sponsor_workbench.router)

# Serve static files for test bench UI (directory must exist — use static/.gitkeep in git)
_static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(_static_dir):
    app.mount("/static", StaticFiles(directory=_static_dir), name="static")

# Serve graphics files (player profile pictures, kit assets, etc.)
_gfx_dir = os.path.join(os.path.dirname(__file__), "gfx")
if os.path.isdir(_gfx_dir):
    app.mount("/gfx", StaticFiles(directory=_gfx_dir), name="gfx")