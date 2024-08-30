import os
from datetime import timedelta
from typing import Any, Optional
from typing import Callable
from typing import Generator

import pytest
from dotenv import load_dotenv
from httpx import ASGITransport
from httpx import AsyncClient
from psycopg2 import pool
from sqlalchemy import NullPool
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine

from src.dependencies import get_db_session
from src.main import app
from src.services.security import create_jwt_token
from src.settings import project_settings

load_dotenv()

TEST_DATABASE_URL: str = (
    f"postgresql+asyncpg://{os.getenv('TEST_DB_USER')}:{os.getenv('TEST_DB_PASSWORD')}@"
    f"{os.getenv('TEST_DB_HOST')}:{os.getenv('INTERNAL_DB_PORT')}/{os.getenv('TEST_DB_NAME')}"
)

TEST_SYNC_DATABASE_URL: str = (
    f"postgresql://{os.getenv('TEST_DB_USER')}:{os.getenv('TEST_DB_PASSWORD')}@"
    f"{os.getenv('TEST_DB_HOST')}:{os.getenv('INTERNAL_DB_PORT')}/{os.getenv('TEST_DB_NAME')}"
)

TABLES: list[str] = ["user", "file"]


@pytest.fixture(scope="session", autouse=True)
async def run_migrations() -> None:
    os.system("alembic upgrade heads")
    os.system('alembic revision --autogenerate -m "test running migrations"')
    os.system("alembic upgrade heads")


@pytest.fixture(scope="session")
async def configure_async_session() -> async_sessionmaker:
    async_engine: AsyncEngine = create_async_engine(
        url=TEST_DATABASE_URL, future=True, echo=True, poolclass=NullPool
    )
    async_session: async_sessionmaker = async_sessionmaker(
        async_engine, expire_on_commit=False
    )
    yield async_session


@pytest.fixture(scope="session")
async def get_async_session(
    configure_async_session: async_sessionmaker,
) -> AsyncSession:

    session = configure_async_session()
    yield session
    await session.close()


@pytest.fixture(scope="function", autouse=True)
async def clean_tables(get_async_session: AsyncSession) -> None:
    async with get_async_session.begin():
        for table_for_cleaning in TABLES:
            await get_async_session.execute(
                text(f'TRUNCATE TABLE "{table_for_cleaning}" CASCADE')
            )


@pytest.fixture(scope="function")
async def async_client() -> Generator[AsyncClient, Any, None]:
    """Fixture that creates testing client and overrides get_db_session dependence"""

    app.dependency_overrides[get_db_session]: Callable = _get_test_db_session
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


async def _get_test_db_session() -> Generator[AsyncSession, Any, None]:
    async_engine: AsyncEngine = create_async_engine(
        url=TEST_DATABASE_URL, future=True, echo=True
    )
    async_session: async_sessionmaker = async_sessionmaker(
        async_engine, expire_on_commit=False
    )

    try:
        session: AsyncSession = async_session()
        yield session
    finally:
        await session.close()


@pytest.fixture(scope="session")
def pg_pool() -> pool.SimpleConnectionPool:
    sync_pool: pool.SimpleConnectionPool = pool.SimpleConnectionPool(
        1, 10, "".join(TEST_DATABASE_URL.split("+asyncpg"))
    )
    yield sync_pool
    sync_pool.closeall()


@pytest.fixture
def get_user_from_database(pg_pool: pool.SimpleConnectionPool) -> Callable:
    def get_user_from_database_by_email(email: str) -> dict:
        connection = pg_pool.getconn()
        try:
            with connection.cursor() as cursor:
                cursor.execute("""SELECT * FROM "user" WHERE email = %s""", (email,))
                user: tuple = cursor.fetchone()
                return _get_user_data_dict(user)
        finally:
            pg_pool.putconn(connection)

    return get_user_from_database_by_email


def _get_user_data_dict(user: Optional[tuple]) -> Optional[dict]:
    user_data: dict = dict()

    if user is not None:
        for field_number in range(len(user)):
            if field_number == 0:
                user_data["user_id"] = user[field_number]
            elif field_number == 1:
                user_data["email"] = user[field_number]
            elif field_number == 2:
                user_data["username"] = user[field_number]
            elif field_number == 4:
                user_data["birthdate"] = user[field_number]
            elif field_number == 5:
                user_data["phone_number"] = user[field_number]

    return user_data


@pytest.fixture
def create_user_in_database(pg_pool: pool.SimpleConnectionPool) -> Callable:
    def create_user_in_database(
            user_id: str,
            username: str,
            email: str,
            hashed_password: str,
            phone_number: str,
            birthdate: str
    ) -> None:
        connection = pg_pool.getconn()
        with connection.cursor() as cursor:
            try:
                cursor.execute(
                    """
                    INSERT INTO "user" (user_id, username, email, hashed_password, phone_number, birthdate)
                    VALUES (%s, %s, %s, %s, %s, %s);
                    """,
                    (user_id, username, email, hashed_password, phone_number, birthdate),
                )
                connection.commit()
            finally:
                pg_pool.putconn(connection)

    return create_user_in_database


def create_test_auth_headers_for_user(email: str) -> dict:
    access_token: str = create_jwt_token(
        email=email,
        exp_timedelta=timedelta(minutes=project_settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def get_file_from_database(pg_pool: pool.SimpleConnectionPool) -> Callable:
    def get_file_from_database_by_file_path(filename: str, user_id: str) -> dict:
        connection = pg_pool.getconn()
        try:
            with connection.cursor() as cursor:
                cursor.execute("""SELECT * FROM "file" WHERE filename = %s AND user_id = %s""", (filename, user_id))
                file: tuple = cursor.fetchone()
                return _get_file_data_dict(file)
        finally:
            pg_pool.putconn(connection)

    return get_file_from_database_by_file_path


def _get_file_data_dict(file: Optional[tuple]) -> Optional[dict]:
    file_data: dict = dict()

    if file is not None:
        for field_number in range(len(file)):
            if field_number == 0:
                file_data["file_id"] = file[field_number]
            elif field_number == 1:
                file_data["filename"] = file[field_number]
            elif field_number == 2:
                file_data["size"] = file[field_number]
            elif field_number == 4:
                file_data["file_path"] = file[field_number]
            elif field_number == 5:
                file_data["user_id"] = file[field_number]

    return file_data


@pytest.fixture
def create_file_in_database(pg_pool: pool.SimpleConnectionPool) -> Callable:
    def create_file_in_database(
            file_id: str,
            filename: str,
            file_path: str,
            user_id: str,
    ) -> None:
        connection = pg_pool.getconn()
        with connection.cursor() as cursor:
            try:
                cursor.execute(
                    """
                    INSERT INTO "file" (user_id, file_id, filename, file_path, size)
                    VALUES (%s, %s, %s, %s, %s);
                    """,
                    (user_id, file_id, filename, file_path, 0),
                )
                connection.commit()
            finally:
                pg_pool.putconn(connection)

    return create_file_in_database
