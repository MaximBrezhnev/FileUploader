import uuid
from datetime import timedelta
from typing import Callable

from fastapi import status
from httpx import AsyncClient
from httpx import Response

from src.settings import project_settings
from src.services import security
from src.services.hashing import get_password_hash
from tests.conftest import create_test_auth_headers_for_user


async def test_refresh_token(
    async_client: AsyncClient, create_user_in_database: Callable
):
    user_data: dict = {
        "user_id": str(uuid.uuid4()),
        "username": "some_username",
        "email": "user@example.com",
        "hashed_password": get_password_hash("1234"),
        "phone_number": "+79208443222",
        "birthdate": "2020-02-11"
    }
    create_user_in_database(**user_data)

    response: Response = await async_client.post(
        "/api/auth/refresh-token",
        headers=create_test_auth_headers_for_user(user_data["email"]),
    )
    response_data: dict = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["access_token"] == security.create_jwt_token(
        user_data["email"],
        timedelta(minutes=project_settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    assert response_data["refresh_token"] is None
    assert response_data["token_type"] == "bearer"


async def test_refresh_token_when_token_is_incorrect(
    async_client: AsyncClient, create_user_in_database: Callable
):
    user_data: dict = {
        "user_id": str(uuid.uuid4()),
        "username": "some_username",
        "email": "user@example.com",
        "hashed_password": get_password_hash("1234"),
        "phone_number": "+79208443222",
        "birthdate": "2020-02-11"
    }
    create_user_in_database(**user_data)

    response: Response = await async_client.post(
        "/api/auth/refresh-token",
        headers=create_test_auth_headers_for_user(user_data["email"] + "1234"),
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
