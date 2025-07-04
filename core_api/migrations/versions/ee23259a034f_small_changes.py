"""Small changes

Revision ID: ee23259a034f
Revises: aea9651e4b20
Create Date: 2025-06-27 22:59:00.611203

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ee23259a034f"
down_revision: Union[str, None] = "aea9651e4b20"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Создаем enum типы перед их использованием
    transaction_type_enum = sa.Enum(
        "ACCRUAL_PURCHASE",
        "SPENDING_PURCHASE",
        "ACCRUAL_MANUAL",
        "SPENDING_MANUAL",
        "ACCRUAL_REFUND",
        "SPENDING_REFUND",
        "EXPIRATION",
        name="transaction_type_enum",
    )
    transaction_status_enum = sa.Enum(
        "PENDING",
        "COMPLETED",
        "FAILED",
        "REVERTED",
        "CANCELED",
        name="transaction_status_enum",
    )

    # Создаем enum типы в базе данных
    transaction_type_enum.create(op.get_bind())
    transaction_status_enum.create(op.get_bind())

    # Теперь добавляем колонки с enum типами
    op.add_column(
        "transactions",
        sa.Column("transaction_type", transaction_type_enum, nullable=False),
    )
    op.add_column(
        "transactions",
        sa.Column(
            "status",
            transaction_status_enum,
            server_default="COMPLETED",
            nullable=False,
        ),
    )
    op.add_column(
        "transactions", sa.Column("description", sa.String(length=500), nullable=True)
    )
    op.add_column(
        "transactions",
        sa.Column(
            "performed_by_admin_profile_id",
            sa.BigInteger(),
            nullable=True,
            comment="Администратор, выполнивший операцию (для ручных начислений/списаний)",
        ),
    )

    # Создаем индексы
    op.create_index(
        op.f("ix__transactions_performed_by_admin_profile_id"),
        "transactions",
        ["performed_by_admin_profile_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix__transactions_status"), "transactions", ["status"], unique=False
    )
    op.create_index(
        op.f("ix__transactions_transaction_type"),
        "transactions",
        ["transaction_type"],
        unique=False,
    )

    # Создаем внешний ключ
    op.create_foreign_key(
        "fk_transactions_performed_by_admin_profile_id_user_roles",
        "transactions",
        "user_roles",
        ["performed_by_admin_profile_id"],
        ["id"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Удаляем внешний ключ
    op.drop_constraint(
        "fk_transactions_performed_by_admin_profile_id_user_roles",
        "transactions",
        type_="foreignkey",
    )

    # Удаляем индексы
    op.drop_index(op.f("ix__transactions_transaction_type"), table_name="transactions")
    op.drop_index(op.f("ix__transactions_status"), table_name="transactions")
    op.drop_index(
        op.f("ix__transactions_performed_by_admin_profile_id"),
        table_name="transactions",
    )

    # Удаляем колонки
    op.drop_column("transactions", "performed_by_admin_profile_id")
    op.drop_column("transactions", "description")
    op.drop_column("transactions", "status")
    op.drop_column("transactions", "transaction_type")

    # Удаляем enum типы из базы данных
    sa.Enum(name="transaction_type_enum").drop(op.get_bind())
    sa.Enum(name="transaction_status_enum").drop(op.get_bind())
