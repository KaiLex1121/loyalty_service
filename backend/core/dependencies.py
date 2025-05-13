from fastapi import Depends, Request
from fastapi.templating import Jinja2Templates
from backend.dao.holder import HolderDAO
from backend.db.session import create_pool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


async def get_db():
    pool = create_pool()
    async with pool() as session:
        try:
            yield session # Предоставляем сессию в эндпоинт
        finally:
            await session.close() # Закрываем сессию после завершения запроса


async def get_holder_dao(session: AsyncSession = Depends(get_db)) -> HolderDAO:
    """
    Зависимость для получения экземпляра HolderDAO с активной сессией БД.
    """
    return HolderDAO(session=session)


async def get_templates(settings):
    return Jinja2Templates(directory=settings.WEB_APP.TEMPLATES_DIR)


def get_jinja_templates(request: Request) -> Jinja2Templates:
    templates_instance = request.app.state.templates
    return templates_instance
