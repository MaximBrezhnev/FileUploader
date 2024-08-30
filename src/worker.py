import os
from typing import Optional

import requests
from asgiref.sync import async_to_sync
from celery import Celery
from requests import HTTPError
from sqlalchemy import select, Result, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.config import database_settings
from src.database.models import File
from src.settings import project_settings


celery: Celery = Celery("worker")
celery.conf.broker_url = project_settings.CELERY_BROKER_URL
celery.conf.result_backend = project_settings.CELERY_RESULT_BACKEND_URL


@celery.task(name="download_file_to_server")
def download_file_to_server(file_url: str, file_id: str, file_path: str) -> None:
    try:
        response = requests.get(file_url, stream=True)
        response.raise_for_status()

        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)

        file_size = os.path.getsize(file_path)
        session = async_to_sync(_get_db_session_for_task)()
        async_to_sync(_update_file_size)(session, file_id, file_size)
    except HTTPError:
        print(f"File with this url not found")
        session = async_to_sync(_get_db_session_for_task)()
        async_to_sync(_delete_nonexistent_file_from_db)(session, file_id)


async def _get_db_session_for_task() -> AsyncSession:
    session: AsyncSession = database_settings.async_session()
    return session


async def _update_file_size(session: AsyncSession, file_id: str, file_size: int) -> None:
    try:
        async with session.begin():
            result: Result = await session.execute(select(File).filter_by(file_id=file_id))
            file: Optional[File] = result.scalar_one_or_none()

            if file:
                file.size = file_size
                await session.commit()
    finally:
        await session.close()


async def _delete_nonexistent_file_from_db(session: AsyncSession, file_id: str) -> None:
    try:
        async with session.begin():
            await session.execute(delete(File).filter_by(file_id=file_id))
    finally:
        await session.close()



