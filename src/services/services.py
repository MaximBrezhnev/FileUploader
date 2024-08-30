import os
from datetime import timedelta, date
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.worker import download_file_to_server
from src.database.models import User, File
from src.services import security, hashing
from src.services.dals import UserDAL, FileDAL
from src.settings import project_settings


class BaseService:
    """
    Базовый класс для всех сервисов в проекте (то есть классов,
    реализующих бизнес-логику для соответствующих обработчиков)
    """

    def __init__(self, db_session: AsyncSession) -> None:
        self.user_dal: UserDAL = UserDAL(db_session=db_session)


class AuthService(BaseService):
    """
    Сервис для работы с авторизацией, регистрацией и
    аутентификацией пользователя
    """

    async def register(
            self,
            email: str,
            username: str,
            password: str,
            phone_number: str,
            birthdate: date
    ) -> User:
        new_user: User = await self.user_dal.create_user(
            email=email,
            username=username,
            password=hashing.get_password_hash(password),
            phone_number=phone_number,
            birthdate=birthdate
        )

        return new_user

    async def login(self, email: str, password: str) -> dict[str, str]:
        user: Optional[User] = await self.user_dal.get_user_by_email(email=email)

        if user is None:
            raise ValueError("User does not exist")

        if not hashing.verify_password(
                hashed_password=user.hashed_password, plain_password=password
        ):
            raise ValueError("Passwords do not match")

        access_token: str = security.create_jwt_token(
            email=user.email,
            exp_timedelta=timedelta(
                minutes=project_settings.ACCESS_TOKEN_EXPIRE_MINUTES
            ),
        )
        refresh_token: str = security.create_jwt_token(
            email=user.email,
            exp_timedelta=timedelta(days=project_settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    @staticmethod
    def refresh_token(user: User) -> dict[str, str]:
        new_access_token: str = security.create_jwt_token(
            email=user.email,
            exp_timedelta=timedelta(
                minutes=project_settings.ACCESS_TOKEN_EXPIRE_MINUTES
            ),
        )
        return {"access_token": new_access_token, "token_type": "bearer"}


class FileService(BaseService):
    """
    Сервис, реализующий бизнес логику для обработчиков, связанных с файлами
    """

    def __init__(self, db_session: AsyncSession) -> None:
        super().__init__(db_session=db_session)
        self.file_dal: FileDAL = FileDAL(db_session=db_session)

    async def upload_file(self, user: User, file_url: str) -> None:
        user_id: UUID = user.user_id
        filename: str = self.extract_filename_from_url(file_url=file_url)
        file_path: str = self.generate_file_path(str(user_id), filename)

        file_id: UUID = await self.file_dal.add_file(
            filename=filename,
            file_path=file_path,
            user_id=user_id,
        )

        download_file_to_server.apply_async(kwargs={
            "file_url": file_url,
            "file_id": str(file_id),
            "file_path": file_path
        })

    @staticmethod
    def extract_filename_from_url(file_url: str) -> str:
        parsed_url = urlparse(file_url)
        filename = os.path.basename(parsed_url.path)
        return filename

    @staticmethod
    def generate_file_path(user_id: str, filename: str) -> str:
        base_dir = Path(__file__).resolve().parent.parent.parent / "uploads"
        user_dir = base_dir / user_id
        file_path = user_dir / filename
        os.makedirs(user_dir, exist_ok=True)

        return str(file_path)

    async def get_list_of_files(self, user: User) -> list[File]:
        files: list[File] = await self.file_dal.get_list_of_files(user=user)
        return files

    async def get_file_info(self, file_id: UUID, user: User) -> Optional[File]:
        file: Optional[File] = await self.file_dal.get_file_by_id(user=user, file_id=file_id)
        return file

    async def delete_file(self, file_id: UUID, user: User) -> None:
        file: Optional[File] = await self.file_dal.get_file_by_id(file_id=file_id, user=user)
        if file is None:
            raise ValueError("File does not exist")
        file_path: Path = Path(file.file_path)
        await self.file_dal.delete_file(file=file)

        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            else:
                raise ValueError("File was not found on the server")
        except OSError:
            print("Error when deleting the file")

    async def download_file(self, file_id: UUID, user: User) -> tuple[str, str]:
        file: Optional[File] = await self.file_dal.get_file_by_id(file_id=file_id, user=user)
        if file is None:
            raise ValueError("File with this id does not exist or does not belong to the current user")

        file_path: Path = Path(file.file_path)
        if not file_path.exists() or not file_path.is_file():
            raise ValueError("File not found on server")

        return str(file_path), file.filename
