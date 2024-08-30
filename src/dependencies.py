from typing import Optional

from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError

from src.database.config import database_settings
from src.database.models import User
from src.services.services import AuthService, FileService
from src.services import security

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials"
)


async def get_db_session() -> AsyncSession:
    try:
        session: AsyncSession = database_settings.async_session()
        yield session
    finally:
        await session.close()


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db_session: AsyncSession = Depends(get_db_session),
) -> User:
    try:
        email: Optional[str] = security.get_email_from_jwt_token(token=token)
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user: Optional[User] = await _get_user_by_email_from_database(
        email=email, db_session=db_session
    )
    if user is None:
        raise credentials_exception

    return user


async def _get_user_by_email_from_database(
    email: str, db_session: AsyncSession
) -> Optional[User]:
    async with db_session.begin():
        result = await db_session.execute(select(User).filter_by(email=email))
        return result.scalars().first()


def get_auth_service(db_session: AsyncSession = Depends(get_db_session)) -> AuthService:
    return AuthService(db_session=db_session)


def get_file_service(db_session: AsyncSession = Depends(get_db_session)) -> FileService:
    return FileService(db_session=db_session)
