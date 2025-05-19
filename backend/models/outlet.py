from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship

from backend.db.base import Base  # Base для ассоциативной таблицы

# Ассоциативная таблица для связи многие-ко-многим Employee <-> Outlet
employee_outlet_association = Table(
    "employee_outlet_association",
    Base.metadata,
    Column(
        "employee_id",
        Integer,
        ForeignKey("employees.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "outlet_id",
        Integer,
        ForeignKey("outlets.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Outlet(Base):
    __tablename__ = "outlets"

    name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    company_id = Column(
        Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )

    # Связи
    company = relationship("Company", back_populates="outlets")

    # Связь многие-ко-многим с Employee через ассоциативную таблицу
    employees = relationship(
        "Employee", secondary=employee_outlet_association, back_populates="outlets"
    )

    transactions = relationship("Transaction", back_populates="outlet")

    def __repr__(self):
        return f"<Outlet(id={self.id}, name='{self.name}')>"
