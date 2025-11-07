import os
import hashlib
from datetime import datetime, date
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import KetoUser, WeightEntry, JournalEntry, RewardClaim

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Helper
def sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    starting_weight: float
    units: str = "lb"

class LoginRequest(BaseModel):
    email: str
    password: str

class WeightLogRequest(BaseModel):
    user_id: str
    on_date: date
    weight: float

class JournalLogRequest(BaseModel):
    user_id: str
    on_date: date
    mood: Optional[str] = "good"
    text: str

class RewardClaimRequest(BaseModel):
    user_id: str
    milestone: float
    title: str


@app.get("/")
def root():
    return {"message": "Keto Tracker API running"}


@app.post("/api/register")
def register(payload: RegisterRequest):
    # Check if email exists
    existing = list(db["ketouser"].find({"email": payload.email}))
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = KetoUser(
        name=payload.name,
        email=payload.email,
        password_hash=sha256(payload.password),
        starting_weight=payload.starting_weight,
        current_weight=payload.starting_weight,
        units=payload.units,
    )
    user_id = create_document("ketouser", user)
    return {"user_id": user_id}


@app.post("/api/login")
def login(payload: LoginRequest):
    hashed = sha256(payload.password)
    doc = db["ketouser"].find_one({"email": payload.email, "password_hash": hashed})
    if not doc:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    # Return minimal user profile
    doc["_id"] = str(doc["_id"])  # type: ignore
    return {
        "user": {
            "id": doc["_id"],
            "name": doc["name"],
            "email": doc["email"],
            "starting_weight": doc["starting_weight"],
            "current_weight": doc["current_weight"],
            "units": doc["units"],
        }
    }


@app.post("/api/weight")
def add_weight(payload: WeightLogRequest):
    # insert weight entry
    _ = create_document("weightentry", WeightEntry(**payload.model_dump()))
    # update user's current weight
    try:
        oid = ObjectId(payload.user_id)
        db["ketouser"].update_one({"_id": oid}, {"$set": {"current_weight": payload.weight}})
    except Exception:
        # Fallback in case id is not a valid ObjectId string
        db["ketouser"].update_one({"_id": payload.user_id}, {"$set": {"current_weight": payload.weight}})
    return {"status": "ok"}


@app.get("/api/weight/{user_id}")
def get_weight(user_id: str):
    entries = get_documents("weightentry", {"user_id": user_id})
    for e in entries:
        e["_id"] = str(e["_id"])  # type: ignore
        if isinstance(e.get("on_date"), (datetime, date)):
            e["on_date"] = str(e["on_date"])  # type: ignore
    return {"entries": entries}


@app.post("/api/journal")
def add_journal(payload: JournalLogRequest):
    _ = create_document("journalentry", JournalEntry(**payload.model_dump()))
    return {"status": "ok"}


@app.get("/api/journal/{user_id}")
def get_journal(user_id: str):
    entries = get_documents("journalentry", {"user_id": user_id})
    for e in entries:
        e["_id"] = str(e["_id"])  # type: ignore
        if isinstance(e.get("on_date"), (datetime, date)):
            e["on_date"] = str(e["on_date"])  # type: ignore
    return {"entries": entries}


@app.post("/api/reward")
def claim_reward(payload: RewardClaimRequest):
    _ = create_document("rewardclaim", RewardClaim(**payload.model_dump()))
    return {"status": "ok"}


@app.get("/api/reward/{user_id}")
def get_rewards(user_id: str):
    entries = get_documents("rewardclaim", {"user_id": user_id})
    for e in entries:
        e["_id"] = str(e["_id"])  # type: ignore
    return {"entries": entries}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        from database import db as _db
        if _db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = _db.name if hasattr(_db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = _db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    import os as _os
    response["database_url"] = "✅ Set" if _os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if _os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
