import uuid
from datetime import timedelta
from typing import Callable

from fastapi import status
from httpx import AsyncClient
from httpx import Response

from src.settings import project_settings
from src.services import security
from src.services.hashing import get_password_hash


async def test_login_when_user_exists(
        create_user_in_database: Callable,
        async_client: AsyncClient
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

    login_data: dict = {
        "grant_type": None,
        "username": "user@example.com",
        "password": "1234",
        "scope": None,
        "client_id": None,
        "client_secret": None,
    }
    response: Response = await async_client.post(
        "/api/auth/login",
        data=login_data
    )
    response_data: dict = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["access_token"] == security.create_jwt_token(
        user_data["email"],
        timedelta(minutes=project_settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    assert response_data["refresh_token"] == security.create_jwt_token(
        user_data["email"], timedelta(days=project_settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    assert response_data["token_type"] == "bearer"


async def test_login_when_user_does_not_exist(async_client: AsyncClient):
    login_data: dict = {
        "grant_type": None,
        "username": "user@example.com",
        "password": "1234",
        "scope": None,
        "client_id": None,
        "client_secret": None,
    }
    response: Response = await async_client.post(
        "/api/auth/login", data=login_data
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_login_when_password_is_incorrect(
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

    login_data: dict = {
        "grant_type": None,
        "username": "user@example.com",
        "password": "12345",
        "scope": None,
        "client_id": None,
        "client_secret": None,
    }
    response: Response = await async_client.post(
        "/api/auth/login", data=login_data
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
