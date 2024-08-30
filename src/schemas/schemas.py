from datetime import date, datetime
from typing import Optional
from uuid import UUID

from fastapi import Form
from pydantic import BaseModel, EmailStr, ConfigDict, HttpUrl

from src.schemas.mixins import UserValidationMixin


class OAuth2PasswordRequestFormEmail:
    def __init__(
        self,
        username: str = Form(...),
        password: str = Form(...),
    ):
        self.email = username
        self.password = password


class TokenSchema(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str


class UserCreationSchema(UserValidationMixin, BaseModel):
    email: EmailStr
    username: str
    password1: str
    password2: str
    phone_number: str
    birthdate: date


class ShowUserSchema(BaseModel):
    email: EmailStr
    username: str
    phone_number: str
    birthdate: date

    model_config = ConfigDict(from_attributes=True)


class UploadFileSchema(BaseModel):
    file_url: HttpUrl


class BasicFileInfoSchema(BaseModel):
    file_id: UUID
    filename: str

    model_config = ConfigDict(from_attributes=True)


class FileInfoSchema(BaseModel):
    file_id: UUID
    filename: str
    uploaded_at: datetime
    size: int

    model_config = ConfigDict(from_attributes=True)

