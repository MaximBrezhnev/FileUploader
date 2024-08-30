from typing import Callable
from uuid import uuid4

from httpx import AsyncClient, Response
from fastapi import status

from src.services.hashing import get_password_hash
from tests.conftest import create_test_auth_headers_for_user


async def test_get_file_info_successfully(
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
        url=f"/api/file/file-info?file_id={file_id}",
        headers=create_test_auth_headers_for_user(email=user_data["email"])
    )
    assert response.status_code == status.HTTP_200_OK

    response_data: dict = response.json()
    assert response_data["file_id"] == file_id
    assert response_data["filename"] == filename
    assert response_data["size"] is not None
    assert response_data["uploaded_at"] is not None


async def test_get_file_info_wrong_id(
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
        url=f"/api/file/file-info?file_id={str(uuid4())}",
        headers=create_test_auth_headers_for_user(email=user_data["email"])
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_get_file_info_wrong_user(
        async_client: AsyncClient,
        create_file_in_database: Callable,
        create_user_in_database: Callable
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

    another_user_data: dict = {
        "user_id": str(uuid4()),
        "username": "some_usernamee",
        "email": "user2@example.com",
        "hashed_password": get_password_hash("1234"),
        "phone_number": "+79208443224",
        "birthdate": "2020-02-21"
    }
    create_user_in_database(**another_user_data)

    file_data: dict = {
        "filename": "example.txt",
        "file_id": file_id,
        "user_id": user_id,
        "file_path": f"/some_way/uploads/{user_id}/{filename}"
    }
    create_file_in_database(**file_data)
    response: Response = await async_client.get(
        url=f"/api/file/file-info?file_id={file_id}",
        headers=create_test_auth_headers_for_user(email=another_user_data["email"])
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
