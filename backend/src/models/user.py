from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class UserCreate(BaseModel):
    """Model for user registration"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    display_name: str = Field(..., min_length=2)

class UserLogin(BaseModel):
    """Model for user login"""
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    """Model for user response"""
    uid: str
    email: str
    displayName: str
    token: Optional[str] = None

class PasswordReset(BaseModel):
    """Model for password reset"""
    email: EmailStr