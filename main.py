from fastapi import FastAPI
from database import engine
from models.base import Base
import models  # <-- THIS LINE IS THE FIX

app = FastAPI()

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

@app.get("/")
def health():
    return {"status": "ok"}


@app.get("/db-check")
def db_check():
    return {"db": "connected"}