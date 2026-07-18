from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict

# Shared user fields
class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    bmi: Optional[float] = None
    activity_level: Optional[str] = None

# Schema for registration
class UserCreate(UserBase):
    email: EmailStr
    name: str
    password: str

# Schema for profile updates
class UserUpdate(UserBase):
    password: Optional[str] = None

# Schema for API responses (excludes password)
class UserOut(UserBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
