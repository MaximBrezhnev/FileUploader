from typing import Callable
from uuid import uuid4

from httpx import AsyncClient, Response
from fastapi import status

from src.services.hashing import get_password_hash
from tests.conftest import create_test_auth_headers_for_user


async def test_get_list_of_files_successfully(
        async_client: AsyncClient,
        create_user_in_database: Callable,
        create_file_in_database: Callable
):
    user_id: str = str(uuid4())
    file_id: str = str(uuid4())
    filename = "example.txt"

    user_data: dict = {
        "user_id": user_id,
        "username": "some_username",
        "email": "user@example.com",
        "hashed_password": get_password_hash("1234"),
        "phone_number": "+79208443222",
        "birthdate": "2020-02-11"
    }
    create_user_in_database(**user_data)

    file_data: dict = {
        "filename": "example.txt",
        "file_id": file_id,
        "user_id": user_id,
        "file_path": f"/some_way/uploads/{user_id}/{filename}"
    }
    create_file_in_database(**file_data)

    response: Response = await async_client.get(
        url=f"/api/file/list-of-files",
        headers=create_test_auth_headers_for_user(email=user_data["email"])
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [{"file_id": file_id, "filename": filename}, ]


async def test_get_list_of_files_no_files(
        async_client: AsyncClient,
        create_user_in_database: Callable
):
    user_data: dict = {
        "user_id": str(uuid4()),
        "username": "some_username",
        "email": "user@example.com",
        "hashed_password": get_password_hash("1234"),
        "phone_number": "+79208443222",
        "birthdate": "2020-02-11"
    }
    create_user_in_database(**user_data)
    response: Response = await async_client.get(
        url=f"/api/file/list-of-files",
        headers=create_test_auth_headers_for_user(email=user_data["email"])
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


