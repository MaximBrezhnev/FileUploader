from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from starlette.responses import JSONResponse, FileResponse

from src.database.models import User, File
from src.dependencies import get_file_service, get_current_user
from src.schemas.schemas import UploadFileSchema, FileInfoSchema, BasicFileInfoSchema
from src.services.services import FileService

file_router: APIRouter = APIRouter(
    prefix="/file",
    tags=["file"],
)


@file_router.post("/upload")
async def upload_file(
    body: UploadFileSchema,
    user: User = Depends(get_current_user),
    service: FileService = Depends(get_file_service)
) -> JSONResponse:
    """
    Обработчик, отвечающий за загрузку файла в фоновом режиме.

    На вход подается url, с которого на сервер будет производиться скачивание файла
    (например, https://example-files.online-convert.com/document/txt/example.txt)

    В случае, если данный пользователь уже имеет файл с таким названием, возникает
    исключение с кодом 409
    """

    try:
        await service.upload_file(user=user, file_url=str(body.file_url))
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "File upload started"}
        )
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This file is already uploaded"
        )


@file_router.get("/download")
async def download_file(
        file_id: UUID,
        user: User = Depends(get_current_user),
        service: FileService = Depends(get_file_service)
) -> FileResponse:
    """
    Обработчик, отвечающий за скачивание пользователем файлов, которые были
    загружены им на сервер

    На вход подается id файла, который необходимо скачать

    В случае, если файла с таким id у пользователя нет, возникает исключение с кодом 404

    В противном случае файл возвращается пользователю в качестве ответа
    """

    try:
        file_path, filename = await service.download_file(file_id=file_id, user=user)
        return FileResponse(
            path=file_path,
            filename=filename
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc)
        )


@file_router.get("/list-of-files", response_model=list[BasicFileInfoSchema])
async def get_list_of_files(
    user: User = Depends(get_current_user),
    service: FileService = Depends(get_file_service)
) -> list[BasicFileInfoSchema]:
    """
    Обработчик, позволяющий получить список всех файлов, загруженных на сервер текущим пользователем

    В случае, если у пользователя нет ни одного скачанного файла, возникает исключение с кодом 404
    """

    files: list[File] = await service.get_list_of_files(user=user)

    if not files:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This user has not uploaded any files yet"
        )

    return files


@file_router.get("/file-info", response_model=FileInfoSchema)
async def get_file_info(
        file_id: UUID,
        user: User = Depends(get_current_user),
        service: FileService = Depends(get_file_service)
) -> FileInfoSchema:
    """
    Обработчик, позволяющий получить пользователю подробную информацию
    (название, id, дата и время загрузки, размер (в байтах)) о файле с указанным id

    В случае, если файла с таким id у пользователя нет, возникает исключение с кодом 404
    """

    file: Optional[File] = await service.get_file_info(file_id=file_id, user=user)

    if file is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File with this id does not exist or does not belong to the current user"
        )
    return file


@file_router.delete("/delete")
async def delete_file(
        file_id: UUID,
        user: User = Depends(get_current_user),
        service: FileService = Depends(get_file_service)
) -> JSONResponse:
    """
    Обработчик, позволяющий пользователю удалить файл с указанным id

    В случае, если файла с таким id у пользователя нет, возникает исключение с кодом 404
    """

    try:
        await service.delete_file(file_id=file_id, user=user)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": f"File with id {file_id} was deleted successfully"},
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File with this id does not exist or does not belong to the current user"
        )

