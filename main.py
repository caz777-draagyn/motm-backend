from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from database import engine
from api import match_engine, test_bench, youth_workbench, youth_academy

app = FastAPI()

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

# Serve static files for test bench UI
app.mount("/static", StaticFiles(directory="static"), name="static")
# Serve graphics files (player profile pictures)
app.mount("/gfx", StaticFiles(directory="gfx"), name="gfx")