from datetime import date
from typing import Optional
from uuid import UUID

from sqlalchemy import select, Result
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import User, File


class BaseDAL:
    """
    Базовый класс для всех DAL (Data Access Layer) классов в проекте
    (то есть классов, необходимых для работы с базой данных)
    """

    def __init__(self, db_session: AsyncSession) -> None:
        self.db_session: AsyncSession = db_session


class UserDAL(BaseDAL):
    """DAL класс для работы с пользовательскими данными"""

    async def get_user_by_email(self, email: str) -> Optional[User]:
        async with self.db_session.begin():
            result: Result = await self.db_session.execute(
                select(User).filter_by(email=email)
            )
            return result.scalars().first()

    async def create_user(
            self,
            email: str,
            username: str,
            password: str,
            phone_number: str,
            birthdate: date
    ) -> User:
        async with self.db_session.begin():
            new_user: User = User(
                email=email,
                username=username,
                hashed_password=password,
                phone_number=phone_number,
                birthdate=birthdate
            )
            self.db_session.add(new_user)
            await self.db_session.flush()

            return new_user


class FileDAL(BaseDAL):
    """DAL класс для работы с данными файлов"""

    async def add_file(self, filename: str, file_path: str, user_id: UUID) -> UUID:
        async with self.db_session.begin():
            new_file: File = File(
                filename=filename,
                file_path=file_path,
                user_id=user_id
            )
            self.db_session.add(new_file)
            await self.db_session.flush()

            return new_file.file_id

    async def get_list_of_files(self, user: User) -> list[File]:
        async with self.db_session.begin():
            result: Result = await self.db_session.execute(
                select(File).filter_by(user_id=user.user_id)
            )
            return result.scalars().all()

    async def get_file_by_id(self, file_id: UUID, user: User) -> Optional[File]:
        async with self.db_session.begin():
            result: Result = await self.db_session.execute(
                select(File).filter_by(file_id=file_id, user_id=user.user_id)
            )
            return result.scalars().first()

    async def delete_file(self, file: File) -> None:
        async with self.db_session.begin():
            await self.db_session.delete(file)

