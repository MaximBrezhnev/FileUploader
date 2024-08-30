import os
from pathlib import Path
from typing import Callable
from uuid import uuid4

from httpx import AsyncClient, Response
from fastapi import status

from src.services.hashing import get_password_hash
from tests.conftest import create_test_auth_headers_for_user


async def test_download_file_successfully(
        async_client: AsyncClient,
        create_user_in_database: Callable,
        create_file_in_database: Callable
):
    user_id: str = str(uuid4())
    file_id: str = str(uuid4())
    filename = "example.txt"

    base_upload_dir = Path("/some_way/uploads")
    file_path = base_upload_dir / user_id / filename

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
        "filename": filename,
        "file_id": file_id,
        "user_id": user_id,
        "file_path": str(file_path)
    }
    create_file_in_database(**file_data)

    os.makedirs(file_path.parent, exist_ok=True)
    with open(file_path, "w") as f:
        f.write("This is a test file content.")

    response: Response = await async_client.get(
        url=f"/api/file/download?file_id={file_id}",
        headers=create_test_auth_headers_for_user(email=user_data["email"])
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.headers['content-disposition'] == f'attachment; filename="{filename}"'
    assert response.content == b'This is a test file content.'


async def test_download_file_not_found(
        async_client: AsyncClient,
        create_user_in_database: Callable
):
    user_id: str = str(uuid4())
    file_id: str = str(uuid4())

    user_data: dict = {
        "user_id": user_id,
        "username": "some_username",
        "email": "user@example.com",
        "hashed_password": get_password_hash("1234"),
        "phone_number": "+79208443222",
        "birthdate": "2020-02-11"
    }
    create_user_in_database(**user_data)

    response: Response = await async_client.get(
        url=f"/api/file/download?file_id={file_id}",
        headers=create_test_auth_headers_for_user(email=user_data["email"])
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_download_file_belongs_to_another_user(
        async_client: AsyncClient,
        create_user_in_database: Callable,
        create_file_in_database: Callable
):
    user_id_owner: str = str(uuid4())
    file_id: str = str(uuid4())
    filename = "example.txt"

    base_upload_dir = Path("/some_way/uploads")
    file_path = base_upload_dir / user_id_owner / filename

    user_id_other: str = str(uuid4())

    user_owner_data: dict = {
        "user_id": user_id_owner,
        "username": "owner_username",
        "email": "owner@example.com",
        "hashed_password": get_password_hash("1234"),
        "phone_number": "+79208443222",
        "birthdate": "2020-02-11"
    }
    create_user_in_database(**user_owner_data)

    user_other_data: dict = {
        "user_id": user_id_other,
        "username": "other_username",
        "email": "other@example.com",
        "hashed_password": get_password_hash("5678"),
        "phone_number": "+79201234567",
        "birthdate": "2021-01-01"
    }
    create_user_in_database(**user_other_data)

    file_data: dict = {
        "filename": filename,
        "file_id": file_id,
        "user_id": user_id_owner,
        "file_path": str(file_path)
    }
    create_file_in_database(**file_data)

    response: Response = await async_client.get(
        url=f"/api/file/download?file_id={file_id}",
        headers=create_test_auth_headers_for_user(email=user_other_data["email"])
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
