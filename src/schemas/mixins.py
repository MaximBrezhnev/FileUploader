import re
from datetime import date
from typing import ClassVar, Optional

from pydantic import field_validator, model_validator


class UserValidationMixin:
    USERNAME_LETTER_MATCH_PATTERN: ClassVar[re.Pattern] = re.compile(r"^[0-9а-яА-Яa-zA-Z\-_ ]+$")
    MIN_USERNAME_LENGTH: ClassVar[int] = 1
    MAX_USERNAME_LENGTH: ClassVar[int] = 20
    MIN_PASSWORD_LENGTH: ClassVar[int] = 8
    PASSWORD_SPECIAL_SYMBOLS: ClassVar[str] = "!@#$%^&*()-_=+[{]};:'\",<.>/?\\|`~"

    @field_validator("username", check_fields=False)
    @classmethod
    def validate_username(cls, username: Optional[str]) -> Optional[str]:
        if username is not None:
            if (
                len(username) < cls.MIN_USERNAME_LENGTH
                or len(username) > cls.MAX_USERNAME_LENGTH
            ):
                raise ValueError("incorrect username length")

            if not cls.USERNAME_LETTER_MATCH_PATTERN.match(username):
                raise ValueError("username contains incorrect symbols")

            return username

    @classmethod
    def check_password_strength(cls, password: str) -> bool:
        if len(password) < cls.MIN_PASSWORD_LENGTH:
            return False

        has_upper = any(char.isupper() for char in password)
        has_lower = any(char.islower() for char in password)
        has_digit = any(char.isdigit() for char in password)
        has_special = any(char in cls.PASSWORD_SPECIAL_SYMBOLS for char in password)

        return has_upper and has_lower and has_digit and has_special

    @field_validator("password1", check_fields=False)
    @classmethod
    def validate_password(cls, password: str) -> str:
        if password is not None:
            if not cls.check_password_strength(password=password):
                raise ValueError("the password is weak")

            return password

    @model_validator(mode="before")
    @classmethod
    def check_password_match(cls, data: dict) -> dict:
        if data.get("password1", None) != data.get("password2", None):
            raise ValueError("the passwords do not match")

        return data

    @field_validator('birthdate', check_fields=False)
    @classmethod
    def validate_birth_date(cls, birthdate: date) -> date:
        current_date = date.today()

        if birthdate > current_date:
            raise ValueError('the date of birth cannot be in the future')
        return birthdate

    @field_validator('phone_number')
    @classmethod
    def validate_phone_number(cls, phone_number: str) -> str:
        phone_pattern = re.compile(r'^\+\d{1,3}\d{10}$')

        if not phone_pattern.match(phone_number):
            raise ValueError('incorrect phone number. Expected format: +<country code><10 digits>')

        return phone_number
