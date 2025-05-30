from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import BigInteger, MetaData, inspect
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql.functions import func

convention = {
    "ix": "ix__%(column_0_label)s",
    "uq": "uq__%(table_name)s__%(column_0_name)s",
    "ck": "ck__%(table_name)s__%(constraint_name)s",
    "fk": "fk__%(table_name)s__%(column_0_name)s__%(referred_table_name)s",
    "pk": "pk__%(table_name)s",
}
meta = MetaData(naming_convention=convention)


class Base(DeclarativeBase):
    metadata = meta
    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True, index=True
    )

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def as_dict(self) -> Dict[str, Any]:
        """
        Возвращает словарь с атрибутами модели SQLAlchemy.
        Включает только те атрибуты, которые являются колонками таблицы.
        Не включает связанные объекты (relationships) или другие методы/свойства.
        """
        # Используем inspect для получения имен колонок, чтобы быть уверенными,
        # что мы берем только атрибуты, соответствующие колонкам в БД.
        mapper = inspect(self.__class__)
        return {
            column.key: getattr(self, column.key)
            for column in mapper.attrs
            if hasattr(self, column.key)
        }
