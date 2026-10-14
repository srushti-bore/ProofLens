"""
Pydantic schemas for User registration, login, and authentication tokens.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    email: EmailStr = Field(description="User email address")
    password: str = Field(min_length=8, description="Password (minimum 8 characters)")
    full_name: Optional[str] = Field(default=None, description="User full name")


class UserLogin(BaseModel):
    email: EmailStr = Field(description="User email address")
    password: str = Field(description="User password")


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenPayload(BaseModel):
    sub: Optional[str] = None
