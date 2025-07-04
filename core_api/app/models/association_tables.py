from sqlalchemy import BigInteger, Column, ForeignKey, Table

from app.db.base import Base

employee_role_outlet_association = Table(
    "employee_role_outlet_association",
    Base.metadata,
    Column(
        "employee_role_id",
        BigInteger,
        ForeignKey("employee_roles.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "outlet_id",
        BigInteger,
        ForeignKey("outlets.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)
