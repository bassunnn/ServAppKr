from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
import re


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    age: Optional[int] = Field(None, gt=0)
    is_subscribed: Optional[bool] = False


class LoginRequest(BaseModel):
    username: str
    password: str


class CommonHeaders(BaseModel):
    user_agent: str
    accept_language: str

    @validator('accept_language')
    def validate_accept_language(cls, v):
        if not v or not v.strip():
            raise ValueError('Accept-Language cannot be empty')
        pattern = r'^[a-zA-Z0-9\-_,;\s=qQ.*]+$'
        if not re.match(pattern, v):
            raise ValueError('Invalid Accept-Language format')
        return v
