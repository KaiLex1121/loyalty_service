import asyncio
import logging
from typing import Optional, Tuple

import typer
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.security import get_password_hash
from backend.core.settings import settings
from backend.dao.account import AccountDAO  # Используем экземпляры DAO
from backend.dao.user_role import UserRoleDAO  # Используем экземпляры DAO
# Импорты из вашего проекта
from backend.db.session import create_pool
from backend.enums.back_office import \
    UserAccessLevelEnum  # Прямой импорт или из backend.enums
from backend.models.user_role import UserRole  # Используем AdminProfile
from backend.schemas.account import AccountCreateInternal, AccountUpdate
from backend.schemas.user_role import UserRoleCreate

cli_app = typer.Typer()
logger = logging.getLogger(__name__)


async def _create_superuser_logic(
    session: AsyncSession,
    phone_number: str,
    password: str,
    email: Optional[str] = None,
    full_name: Optional[str] = None,
) -> Tuple[str, bool]:  # Возвращаем кортеж (статус, был_ли_создан_новый)
    """
    Создает или обновляет суперпользователя.

    Returns:
        Tuple[str, bool]: (статус_операции, был_ли_создан_новый_пользователь)
        Возможные статусы:
        - "created": Новый пользователь создан
        - "updated": Существующий пользователь обновлен до суперпользователя
        - "already_superuser": Пользователь уже является суперпользователем
    """
    try:
        account_dao = AccountDAO()
        user_role_dao = UserRoleDAO()
        account = await account_dao.get_by_phone_number_with_profiles(
            session, phone_number=phone_number
        )

        if not account:
            # Создаем новый аккаунт
            account_data = AccountCreateInternal(
                phone_number=phone_number,
                hashed_password=get_password_hash(password),
                email=email,
                full_name=full_name,
                is_active=True,
            )
            account = await account_dao.create(session, obj_in=account_data)
            # После создания снова загружаем с профилями
            account = await account_dao.get_by_phone_number_with_profiles(
                session, phone_number=phone_number
            )

            # Создаем профиль суперпользователя
            user_profile_data = UserRoleCreate(
                account_id=account.id,
                access_level=UserAccessLevelEnum.FULL_ADMIN,
            )
            new_user_profile = await user_role_dao.create_for_account(
                session=session,
                obj_in=user_profile_data,
            )
            session.add(new_user_profile)

            return ("created", True)

        else:
            # Аккаунт существует, проверяем статус
            # Обновляем почту, имя и пароль
            updated_account = AccountUpdate(
                hashed_password=get_password_hash(password),
                email=email,
                full_name=full_name
            )
            await account_dao.update(session, db_ojb=account, obj_in=updated_account)

            # Проверяем существующий профиль
            if account.user_profile:
                if account.user_profile.access_level == UserAccessLevelEnum.FULL_ADMIN:
                    # Пользователь уже суперпользователь
                    return ("already_superuser", False)
                else:
                    # Обновляем до суперпользователя
                    account.user_profile.access_level = UserAccessLevelEnum.FULL_ADMIN
                    session.add(account.user_profile)
                    return ("updated", False)
            else:
                # Профиля нет, создаем новый
                user_profile_data = UserRoleCreate(
                    account_id=account.id,
                    access_level=UserAccessLevelEnum.FULL_ADMIN,
                )
                new_user_profile = await user_role_dao.create_for_account(
                    session=session,
                    obj_in=user_profile_data,
                )
                session.add(new_user_profile)
                return ("updated", False)

    except ValueError as ve:
        logger.error(f"Ошибка валидации данных: {ve}", exc_info=True)
        raise
    except IntegrityError as ie:
        logger.error(f"Ошибка целостности базы данных: {ie}", exc_info=True)
        raise
    except SQLAlchemyError as db_err:
        logger.error(
            f"Ошибка базы данных при работе с аккаунтом/профилем: {db_err}",
            exc_info=True,
        )
        raise
    except Exception as e:
        logger.error(
            f"Непредвиденная ошибка при управлении аккаунтом/профилем: {e}",
            exc_info=True,
        )
        raise


@cli_app.command("create_superuser")
def create_superuser(
    phone_number: str = typer.Option(..., prompt="Phone number (e.g., +79991234567)"),
    password: str = typer.Option(
        ..., prompt="Password", hide_input=True, confirmation_prompt=True
    ),
    email: Optional[str] = typer.Option(None, prompt="Email (optional)"),
    full_name: Optional[str] = typer.Option(None, prompt="Full name (optional)"),
):
    async def _runner():
        pool = create_pool(settings)
        async with pool() as session:
            async with session.begin():
                try:
                    status, is_new = await _create_superuser_logic(
                        session, phone_number, password, email, full_name
                    )

                    # Выбираем сообщение в зависимости от статуса
                    if status == "created":
                        success_message = typer.style(
                            f"Superuser '{phone_number}' created successfully!",
                            fg=typer.colors.GREEN,
                            bold=True,
                        )
                    elif status == "updated":
                        success_message = typer.style(
                            f"Account '{phone_number}' already existed and has been updated to superuser.",
                            fg=typer.colors.YELLOW,
                            bold=True,
                        )
                    elif status == "already_superuser":
                        success_message = typer.style(
                            f"Account '{phone_number}' already existed and is a superuser.",
                            fg=typer.colors.BLUE,
                            bold=True,
                        )
                    else:
                        success_message = typer.style(
                            f"Unknown status for account '{phone_number}'.",
                            fg=typer.colors.MAGENTA,
                            bold=True,
                        )

                    typer.echo(success_message)

                    # Показываем детали только если это не случай "уже суперпользователь"
                    if status != "already_superuser":
                        details = [
                            ("Phone Number:", phone_number),
                            ("Email:", email if email else "Not provided"),
                            ("Full Name:", full_name if full_name else "Not provided"),
                            ("Status:", "Active Superuser"),
                        ]

                        typer.echo("\nUser Details:")
                        for label, value in details:
                            styled_label = typer.style(label, fg=typer.colors.BLUE)
                            typer.echo(f"  {styled_label} {value}")
                    else:
                        typer.echo(
                            f"\nPassword has been updated for existing superuser."
                        )

                except Exception as e:
                    error_message = typer.style(
                        f"Error creating/updating superuser: {e}",
                        fg=typer.colors.RED,
                        bold=True,
                    )
                    typer.echo(error_message)
                    raise typer.Exit(code=1)

    asyncio.run(_runner())


@cli_app.command("test_command")
def test_command(name: str = "World"):
    pass


if __name__ == "__main__":
    cli_app()
