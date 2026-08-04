from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import engine, Base
from app.models import models
from app.routers import guests, rooms, reservations, folios, pos, housekeeping, auth, settings

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Resort PMS API",
    description="Property Management System for resorts",
    version="0.1.0",
)

# Allow frontend to talk to backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(guests.router)
app.include_router(rooms.router)
app.include_router(reservations.router)
app.include_router(folios.router)
app.include_router(pos.router)
app.include_router(housekeeping.router)
app.include_router(settings.router)


@app.get("/")
def root():
    return {"message": "Resort PMS API is running"}


@app.get("/health")
def health():
    return {"status": "ok"}