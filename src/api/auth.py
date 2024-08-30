from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError

from src.database.models import User
from src.dependencies import get_current_user, get_auth_service
from src.schemas.schemas import OAuth2PasswordRequestFormEmail, TokenSchema, UserCreationSchema, ShowUserSchema
from src.services.services import AuthService

auth_router: APIRouter = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


@auth_router.post(path="/register", response_model=ShowUserSchema)
async def register(
        body: UserCreationSchema,
        service: AuthService = Depends(get_auth_service)
) -> ShowUserSchema:
    """
    Обработчик, отвечающий за регистрацию пользователей

    В случае, если пользователь с таким номером, username или почтой уже существует, возникает
    исключение с кодом 409

    В противном случае происходит регистрация пользователя
    """

    try:
        new_user: User = await service.register(
            email=body.email,
            username=body.username,
            password=body.password1,
            birthdate=body.birthdate,
            phone_number=body.phone_number
        )
        return new_user

    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this credentials already exists",
        )


@auth_router.post(path="/login", response_model=TokenSchema)
async def login(
    body: OAuth2PasswordRequestFormEmail = Depends(),
    service: AuthService = Depends(get_auth_service),
) -> TokenSchema:
    """
    Обработчик, отвечающий за вход пользователя в систему. На вход поступает электронная почта и пароль (электронная
    почта обозначена в документации как username)

    В случае, если пользователь ввел неверные данные, возникает исключение с кодом 401

    В противном случае обработчик возвращает access token, который необходимо будет передавать с последующими запросами
    в заголовке вида Authorization: Bearer "значение токена", и refresh token, необходимый для обновления имеющего
    относительно короткий срок службы access token'а через обработчик refresh_token
    """

    try:
        token_data: dict[str, str] = await service.login(
            email=body.email, password=body.password
        )
        return TokenSchema(**token_data)

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )


@auth_router.post(path="/refresh-token", response_model=TokenSchema)
async def refresh_token(
    user: User = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
) -> TokenSchema:
    """
    Обработчик, возвращающий обновленный access token на основании refresh token'а. Refresh token берется
    из заголовка Authorization поступившего запроса
    """

    token_data: dict[str, str] = service.refresh_token(user=user)

    return TokenSchema(**token_data)
