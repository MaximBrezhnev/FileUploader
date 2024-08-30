import os

from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine


class DatabaseSettings(BaseSettings):
    """
    Класс, реализующий настройки соединения с базой данных
    """

    DB_HOST: str
    EXTERNAL_DB_PORT: int
    INTERNAL_DB_PORT: int
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    @property
    def ASYNC_DATABASE_URL(self):
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.DB_HOST}:{self.INTERNAL_DB_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def _async_engine(self):
        return create_async_engine(url=self.ASYNC_DATABASE_URL, future=True, echo=True)

    @property
    def async_session(self):
        return async_sessionmaker(self._async_engine, expire_on_commit=False)

    model_config = SettingsConfigDict(
        env_file=os.path.join(
            os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            ),
            ".env",
        ),
        extra="ignore",
    )


database_settings = DatabaseSettings()
