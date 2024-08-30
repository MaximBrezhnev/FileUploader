import uvicorn
from fastapi import APIRouter, FastAPI

from src.api.auth import auth_router
from src.api.file import file_router
from src.settings import project_settings

app: FastAPI = FastAPI(title=project_settings.APP_TITLE)

main_router: APIRouter = APIRouter(prefix="/api")
main_router.include_router(auth_router)
main_router.include_router(file_router)

app.include_router(main_router)

if __name__ == "__main__":
    uvicorn.run(app=app, host=project_settings.APP_HOST, port=project_settings.APP_PORT)
