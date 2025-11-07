"""
Database Schemas for Keto Tracker

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- KetoUser -> "ketouser" collection
- WeightEntry -> "weightentry" collection
- JournalEntry -> "journalentry" collection
- RewardClaim -> "rewardclaim" collection
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import date

class KetoUser(BaseModel):
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    password_hash: str = Field(..., description="SHA256 hash of password")
    starting_weight: float = Field(..., gt=0, description="Starting weight")
    current_weight: float = Field(..., gt=0, description="Current weight")
    units: Literal["lb", "kg"] = Field("lb", description="Weight units")

class WeightEntry(BaseModel):
    user_id: str = Field(..., description="User id as string")
    on_date: date = Field(..., description="Entry date (YYYY-MM-DD)")
    weight: float = Field(..., gt=0, description="Weight value in user's units")

class JournalEntry(BaseModel):
    user_id: str = Field(..., description="User id as string")
    on_date: date = Field(..., description="Entry date (YYYY-MM-DD)")
    mood: Optional[Literal["great", "good", "okay", "tough"]] = Field("good")
    text: str = Field(..., description="Journal text")

class RewardClaim(BaseModel):
    user_id: str = Field(..., description="User id as string")
    milestone: float = Field(..., gt=0, description="Milestone amount of weight lost in user's units")
    title: str = Field(..., description="Reward title/description")
