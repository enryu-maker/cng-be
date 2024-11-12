from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
import base64


class UserBase(BaseModel):
    name: str
    phone_number: str = Field(..., max_length=10)
    otp: Optional[int] = None
    is_active: Optional[bool] = True


class UserCreate(UserBase):
    icon: Optional[bytes] = None


class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone_number: Optional[str] = Field(None, max_length=10)
    otp: Optional[int] = None
    is_active: Optional[bool] = None
    icon: Optional[bytes] = None


class UserResponse(UserBase):
    id: int
    created_at: datetime
    # Store the icon in a base64-encoded string format
    icon: Optional[str] = None

    @validator("icon", pre=True, always=True)
    def encode_icon(cls, v):
        if v is not None:
            return base64.b64encode(v).decode('utf-8')
        return None

    class Config:
        orm_mode = True


class OTPVerify(BaseModel):
    phone_number: str
    otp: int


class LoginRequest(BaseModel):
    phone_number: str

# Schema for creating a vehicle


class CreateVehicle(BaseModel):
    vehicle_number: str
    vehicle_make: str
    vehicle_model: str

    class Config:
        orm_mode = True  # Enables ORM compatibility for SQLAlchemy models


# Schema for displaying a vehicle (e.g., as a response model)
class VehicleResponse(BaseModel):
    id: int
    user_id: int
    vehicle_number: str
    vehicle_make: str
    vehicle_model: str

    class Config:
        orm_mode = True
