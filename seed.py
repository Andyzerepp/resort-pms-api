"""
Seed script — populates the database with initial users, room types, rooms, and settings.
Run this once after a fresh migration: python seed.py

Account passwords are read from environment variables (SEED_ADMIN_PASSWORD,
SEED_FRONTDESK_PASSWORD, SEED_HOUSEKEEPING_PASSWORD) so real credentials
never sit hardcoded in source. Unset vars fall back to "changeme" — fine for
a throwaway local database, but change it before using the account for real.
"""
import os
from app.core.database import SessionLocal
from app.models.models import User, RoomType, Room, ResortSettings
import bcrypt

db = SessionLocal()

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# --- Users ---
users = [
    {"username": "admin", "full_name": "Admin", "password": os.getenv("SEED_ADMIN_PASSWORD", "changeme"), "role": "admin"},
    {"username": "frontdesk", "full_name": "Front Desk Staff", "password": os.getenv("SEED_FRONTDESK_PASSWORD", "changeme"), "role": "front_desk"},
    {"username": "housekeeping", "full_name": "Housekeeping Staff", "password": os.getenv("SEED_HOUSEKEEPING_PASSWORD", "changeme"), "role": "housekeeping"},
]

for u in users:
    existing = db.query(User).filter(User.username == u["username"]).first()
    if not existing:
        user = User(
            username=u["username"],
            full_name=u["full_name"],
            password=hash_password(u["password"]),
            role=u["role"],
            is_active=True,
        )
        db.add(user)
        print(f"Created user: {u['username']}")

# --- Room Types ---
room_types = [
    {"name": "Single Standard Room", "description": "Fan room with Private Bathroom", "capacity": 2, "base_rate": 1000},
    {"name": "Deluxe Double Room", "description": "Airconditioned Room with Private Bathroom", "capacity": 2, "base_rate": 2500},
]

room_type_ids = {}
for rt in room_types:
    existing = db.query(RoomType).filter(RoomType.name == rt["name"]).first()
    if not existing:
        room_type = RoomType(**rt)
        db.add(room_type)
        db.flush()
        room_type_ids[rt["name"]] = room_type.id
        print(f"Created room type: {rt['name']}")
    else:
        room_type_ids[rt["name"]] = existing.id

# --- Rooms ---
rooms = [
    {"room_number": "101", "room_type": "Single Standard Room"},
    {"room_number": "102", "room_type": "Single Standard Room"},
    {"room_number": "103", "room_type": "Single Standard Room"},
    {"room_number": "201", "room_type": "Deluxe Double Room"},
    {"room_number": "202", "room_type": "Deluxe Double Room"},
    {"room_number": "203", "room_type": "Deluxe Double Room"},
]

for r in rooms:
    existing = db.query(Room).filter(Room.room_number == r["room_number"]).first()
    if not existing:
        room = Room(
            room_number=r["room_number"],
            room_type_id=room_type_ids[r["room_type"]],
            status="available",
        )
        db.add(room)
        print(f"Created room: {r['room_number']}")

# --- Resort Settings ---
existing_settings = db.query(ResortSettings).first()
if not existing_settings:
    settings = ResortSettings(
        resort_name="Anilao Highland Farm Resort, Inc.",
        default_checkin_time="14:00",
        default_checkout_time="12:00",
    )
    db.add(settings)
    print("Created resort settings")

db.commit()
db.close()
print("\nSeed complete!")