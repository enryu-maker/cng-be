from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime


class cngLogin(BaseModel):
    phone_number: str = Field(..., max_length=10)
    otp: Optional[int] = None


class StationSchema(BaseModel):
    id: int
    name: str
    price: str
    fuel_available: bool
    phone_number: str
