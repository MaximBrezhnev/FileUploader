from typing import Callable
from uuid import uuid4

from httpx import AsyncClient, Response
from fastapi import status
import pytest


async def test_register_new_user(
        async_client: AsyncClient,
        get_user_from_database: Callable
):
    user_data: dict = {
        "email": "user@example.com",
        "username": "username-example",
        "password1": "Some_password1234",
        "password2": "Some_password1234",
        "phone_number": "+79207710791",
        "birthdate": "2005-04-30"
    }
    response: Response = await async_client.post("/api/auth/register", json=user_data)
    assert response.status_code == status.HTTP_200_OK
    registered_user: dict = get_user_from_database(email=user_data["email"])
    response_data: dict = response.json()

    assert registered_user["email"] == user_data["email"]
    assert registered_user["username"] == user_data["username"]
    assert registered_user["phone_number"] == user_data["phone_number"]
    assert str(registered_user["birthdate"]) == user_data["birthdate"]

    assert response_data["email"] == user_data["email"]
    assert response_data["username"] == user_data["username"]
    assert response_data["phone_number"] == response_data["phone_number"]
    assert response_data["birthdate"] == user_data["birthdate"]


async def test_register_duplicate_email(
        async_client: AsyncClient,
        get_user_from_database: Callable,
        create_user_in_database: Callable,
):
    old_user_data: dict = {
        "user_id": str(uuid4()),
        "username": "some_username",
        "email": "user@example.com",
        "hashed_password": "1234",
        "phone_number": "+79207710791",
        "birthdate": "2005-04-30"
    }
    new_user_data: dict = {
        "email": "user@example.com",
        "username": "username-example",
        "password1": "Some_password1234",
        "password2": "Some_password1234",
        "phone_number": "+79207710792",
        "birthdate": "2004-04-30"
    }
    create_user_in_database(**old_user_data)
    response: Response = await async_client.post("/api/auth/register", json=new_user_data)

    assert response.status_code == status.HTTP_409_CONFLICT
    old_user_data_after_request: dict = get_user_from_database(old_user_data["email"])
    assert old_user_data_after_request["user_id"] == old_user_data["user_id"]
    assert old_user_data_after_request["username"] == old_user_data["username"]
    assert old_user_data_after_request["phone_number"] == old_user_data["phone_number"]
    assert str(old_user_data_after_request["birthdate"]) == old_user_data["birthdate"]


@pytest.mark.parametrize(
    "user_data_for_creation, expected_detail",
    [
        (
            None,
            {
                "detail": [
                    {
                        "type": "missing",
                        "loc": ["body"],
                        "msg": "Field required",
                        "input": None,
                    }
                ]
            },
        ),
        (
            {},
            {
                "detail": [
                    {
                        "type": "missing",
                        "loc": ["body", "email"],
                        "msg": "Field required",
                        "input": {},
                    },
                    {
                        "type": "missing",
                        "loc": ["body", "username"],
                        "msg": "Field required",
                        "input": {},
                    },
                    {
                        "type": "missing",
                        "loc": ["body", "password1"],
                        "msg": "Field required",
                        "input": {},
                    },
                    {
                        "type": "missing",
                        "loc": ["body", "password2"],
                        "msg": "Field required",
                        "input": {},
                    },
                    {
                        "type": "missing",
                        "loc": ["body", "phone_number"],
                        "msg": "Field required",
                        "input": {},
                    },
                    {
                        "type": "missing",
                        "loc": ["body", "birthdate"],
                        "msg": "Field required",
                        "input": {},
                    },
                ]
            },
        ),
        (
            {
                "username": "@username",
                "email": "user@example.com",
                "password1": "Some_password1234",
                "password2": "Some_password1234",
                "phone_number": "+79207410111",
                "birthdate": "2022-04-11"
            },
            {
                "detail": [
                    {
                        "type": "value_error",
                        "loc": ["body", "username"],
                        "msg": "Value error, username contains incorrect symbols",
                        "input": "@username",
                        "ctx": {"error": {}},
                    }
                ]
            },
        ),
        (
            {
                "username": "",
                "email": "user@example.com",
                "password1": "Some_password1234",
                "password2": "Some_password1234",
                "phone_number": "+79207410111",
                "birthdate": "2022-04-11"
            },
            {
                "detail": [
                    {
                        "type": "value_error",
                        "loc": ["body", "username"],
                        "msg": "Value error, incorrect username length",
                        "input": "",
                        "ctx": {"error": {}},
                    }
                ]
            },
        ),
        (
            {
                    "username": "123456789012345678901",
                    "email": "user@example.com",
                    "password1": "Some_password1234",
                    "password2": "Some_password1234",
                    "phone_number": "+79207410111",
                    "birthdate": "2022-04-11"
            },
            {
                "detail": [
                    {
                        "type": "value_error",
                        "loc": ["body", "username"],
                        "msg": "Value error, incorrect username length",
                        "input": "123456789012345678901",
                        "ctx": {"error": {}},
                    }
                ]
            },
        ),
        (
            {
                "email": "user@example.com",
                "username": "some-username",
                "password1": "134",
                "password2": "134",
                "phone_number": "+79207410111",
                "birthdate": "2022-04-11"
            },
            {
                "detail": [
                    {
                        "type": "value_error",
                        "loc": ["body", "password1"],
                        "msg": "Value error, the password is weak",
                        "input": "134",
                        "ctx": {"error": {}},
                    }
                ]
            },
        ),
        (
            {
                "email": "user@example.com",
                "username": "some-username",
                "password1": "12334",
                "password2": "1234",
                "phone_number": "+79207410111",
                "birthdate": "2022-04-11"
            },
            {
                "detail": [
                    {
                        "type": "value_error",
                        "loc": [
                            "body"
                        ],
                        "msg": "Value error, the passwords do not match",
                        "input": {
                            "email": "user@example.com",
                            "username": "some-username",
                            "password1": "12334",
                            "password2": "1234",
                            "phone_number": "+79207410111",
                            "birthdate": "2022-04-11"
                        },
                        "ctx": {
                            "error": {}
                        }
                    }
                ]
            }
        ),
        (
            {
                "username": "some-username",
                "email": "userexample.com",
                "password1": "Some_password1234",
                "password2": "Some_password1234",
                "phone_number": "+79207410111",
                "birthdate": "2022-04-11"
            },
            {
                "detail": [
                    {
                        "type": "value_error",
                        "loc": [
                            "body",
                            "email"
                        ],
                        "msg": "value is not a valid email address: An email address must have an @-sign.",
                        "input": "userexample.com",
                        "ctx": {
                            "reason": "An email address must have an @-sign."
                        }
                    }
                ]
            },
        )
    ],
)
async def test_register_new_user_negative(
    async_client: AsyncClient, user_data_for_creation: dict, expected_detail: dict
):
    response: Response = await async_client.post(
        "/api/auth/register",
        json=user_data_for_creation
    )
    assert response.status_code == 422
    assert response.json() == expected_detail
