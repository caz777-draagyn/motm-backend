from fastapi import FastAPI
from database import engine, Base

app = FastAPI()

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

@app.get("/")
def health():
    return {"status": "ok"}
