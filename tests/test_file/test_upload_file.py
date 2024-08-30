from pathlib import Path
from typing import Callable
from unittest.mock import patch
from uuid import uuid4

from httpx import AsyncClient, Response
from fastapi import status

from src.services.hashing import get_password_hash
from src.services.services import FileService
from tests.conftest import create_test_auth_headers_for_user


async def test_upload_file_successfully(
        async_client: AsyncClient,
        create_user_in_database: Callable,
        get_file_from_database: Callable
):
    with patch("src.services.services.download_file_to_server.apply_async") as mock_apply_async:
        user_data: dict = {
            "user_id": str(uuid4()),
            "username": "some_username",
            "email": "user@example.com",
            "hashed_password": get_password_hash("1234"),
            "phone_number": "+79208443222",
            "birthdate": "2020-02-11"
        }
        create_user_in_database(**user_data)

        response: Response = await async_client.post(
            url="/api/file/upload",
            json={"file_url": "https://example-files.online-convert.com/document/txt/example.txt", },
            headers=create_test_auth_headers_for_user(user_data["email"]),
        )
        assert response.status_code == status.HTTP_200_OK
        added_file_data: dict = get_file_from_database(filename="example.txt", user_id=user_data["user_id"])
        assert added_file_data["filename"] == "example.txt"
        path = Path(added_file_data["file_path"])
        assert list(path.parts[-3:]) == ["uploads", user_data["user_id"], "example.txt"]

        assert mock_apply_async.call_count == 1


async def test_upload_file_duplicate(
        async_client: AsyncClient,
        create_user_in_database: Callable,
        create_file_in_database: Callable
):
    file_id: str = str(uuid4())
    filename: str = "example.txt"
    user_id: str = str(uuid4())
    expected_path = f"/some_way/uploads/{user_id}/{filename}"

    with patch("src.services.services.download_file_to_server.apply_async"), \
            patch.object(FileService, 'generate_file_path', return_value=expected_path):

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

        response: Response = await async_client.post(
            url="/api/file/upload",
            json={"file_url": f"https://example-files.online-convert.com/document/txt/{filename}", },
            headers=create_test_auth_headers_for_user(user_data["email"]),
        )
        assert response.status_code == status.HTTP_409_CONFLICT










