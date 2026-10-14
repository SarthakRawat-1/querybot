import re
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


def validate_password_strength(password: str) -> str:
    if not re.search(r'[A-Z]', password):
        raise ValueError('Password must contain at least one uppercase letter')
    if not re.search(r'[a-z]', password):
        raise ValueError('Password must contain at least one lowercase letter')
    if not re.search(r'\d', password):
        raise ValueError('Password must contain at least one number')
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        raise ValueError('Password must contain at least one special character')
    return password


class UserSignupRequest(BaseModel):
    fullname: str = Field(..., min_length=2, max_length=100)
    email: EmailStr = Field(..., max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str

    @field_validator('fullname')
    @classmethod
    def validate_fullname(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z\s\-\'\.]+$", v):
            raise ValueError("Fullname can only contain letters, spaces, hyphens, apostrophes, and periods")
        return v.strip()

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        return validate_password_strength(v)

    @model_validator(mode='after')
    def check_passwords_match(self) -> 'UserSignupRequest':
        if self.password != self.confirm_password:
            raise ValueError('Passwords do not match')
        return self


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    fullname: str
    email: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    is_active: bool = True