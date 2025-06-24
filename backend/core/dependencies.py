from typing import Optional

from fastapi import Depends, HTTPException, Path, Request, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from backend.core.logger import get_logger
from backend.core.security import (
    bot_api_key_header,
    http_bearer_backoffice,
    oauth2_scheme_backoffice,
    verify_token,
)
from backend.core.settings import AppSettings, get_settings
from backend.dao.holder import HolderDAO
from backend.db.session import create_pool
from backend.enums import UserAccessLevelEnum
from backend.exceptions.common import (
    ForbiddenException,
    NotFoundException,
    UnauthorizedException,
)
from backend.exceptions.services.employee import EmployeeNotFoundException
from backend.exceptions.services.outlet import OutletNotFoundException
from backend.models.account import Account
from backend.models.company import Company
from backend.models.customer_role import CustomerRole
from backend.models.employee_role import EmployeeRole
from backend.models.outlet import Outlet
from backend.models.promotions.promotion import Promotion
from backend.models.subscription import Subscription
from backend.models.user_role import UserRole
from backend.schemas.token import TokenPayload
from backend.services.account import AccountService
from backend.services.auth import AuthService
from backend.services.company import CompanyService
from backend.services.company_default_cashback_config import (
    CompanyDefaultCashbackConfigService,
)
from backend.services.customer import CustomerService  # Поздний импорт
from backend.services.customer_auth import CustomerAuthService  # Поздний импорт
from backend.services.dashboard import DashboardService
from backend.services.employee import EmployeeService
from backend.services.otp_code import OtpCodeService
from backend.services.otp_sending import MockOTPSendingService
from backend.services.outlet import OutletService
from backend.services.promotion import PromotionService

logger = get_logger(__name__)


async def get_session(settings: AppSettings = Depends(get_settings)):
    session_maker = create_pool(settings)

    async with session_maker() as session:
        try:
            yield session
            await session.commit()

        except SQLAlchemyError as db_error:
            await session.rollback()
            logger.error(f"Database error, transaction rolled back: {db_error}")
            raise

        except Exception as general_error:
            await session.rollback()
            logger.error(f"General error, transaction rolled back: {general_error}")
            raise

        finally:
            await session.close()


async def get_dao() -> HolderDAO:
    dao = HolderDAO()
    return dao


async def get_backoffice_user_token_payload(
    oauth_token: str = Depends(oauth2_scheme_backoffice),
    http_credentials: HTTPAuthorizationCredentials = Depends(http_bearer_backoffice),
    settings: AppSettings = Depends(get_settings),
) -> TokenPayload:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate admin credentials.",
        headers={
            "WWW-Authenticate": oauth2_scheme_backoffice.scheme_name
        },  # Используем имя схемы
    )
    if http_credentials:
        token = http_credentials.credentials
    else:
        token = oauth_token

    if oauth_token and http_credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен отсутствует",
            headers={"WWW-Authenticate": oauth2_scheme_backoffice.scheme_name},
        )
    token_data = verify_token(token=token, settings=settings)

    if token_data is None:
        raise credentials_exception

    if "backoffice_user" not in token_data.scopes:  # Проверка скоупа здесь
        raise ForbiddenException(
            detail="Not authorized for backoffice operations. Missing 'backoffice_user' scope."
        )

    return token_data


async def get_current_account_without_relations(
    session: AsyncSession = Depends(get_session),
    dao: HolderDAO = Depends(get_dao),
    token_payload: TokenPayload = Depends(get_backoffice_user_token_payload),
) -> Optional[Account]:
    """
    Зависимость для получения текущего пользователя на основе JWT токена.
    """
    # if "backoffice_user" not in token_payload.scopes:
    #     raise ForbiddenException(detail="Not authorized for backoffice operations. Missing 'backoffice_user' scope.")
    account_id = int(token_payload.sub)
    account = await dao.account.get_by_id_without_relations(session, id_=account_id)
    return account


async def get_current_active_account_without_relations(
    current_account: Account = Depends(get_current_account_without_relations),
) -> Account:

    if not current_account.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Inactive account"
        )
    return current_account


async def get_current_account_with_profiles(
    session: AsyncSession = Depends(get_session),
    dao: HolderDAO = Depends(get_dao),
    token_payload: TokenPayload = Depends(get_backoffice_user_token_payload),
) -> Optional[Account]:
    """
    Зависимость для получения текущего пользователя на основе JWT токена.
    """
    if "backoffice_user" not in token_payload.scopes:
        raise ForbiddenException(
            detail="Not authorized for backoffice operations. Missing 'backoffice_user' scope."
        )

    account_id = int(token_payload.sub)
    account = await dao.account.get_by_id_with_all_profiles(session, id_=account_id)
    return account


async def get_current_active_account_with_profiles(
    current_account: Account = Depends(get_current_account_with_profiles),
) -> Account:

    if not current_account.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Inactive account"
        )
    return current_account


async def get_current_user_profile_from_account(
    current_account: Account = Depends(get_current_active_account_with_profiles),
) -> UserRole:
    if current_account.user_profile is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User profile required for this operation. Account does not have an user profile.",
        )
    return current_account.user_profile


async def get_current_full_system_admin(
    current_user_profile: UserRole = Depends(get_current_user_profile_from_account),
    token_payload: TokenPayload = Depends(get_backoffice_user_token_payload),
) -> UserRole:
    if current_user_profile.access_level != UserAccessLevelEnum.FULL_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Full system administrator privileges required.",
        )
    if "backoffice_admin" not in token_payload.scopes:
        logger.warning(
            f"User {current_user_profile.account_id} has FULL_ADMIN access_level but token lacks 'backoffice_admin' scope."
        )
        raise ForbiddenException(
            detail="Not authorized for system operations. Missing 'backoffice_admin' scope."
        )
    return current_user_profile


async def get_owned_company(
    # company_id берется из параметра пути с тем же именем (тот, что в эндпоинте)
    company_id: int,
    session: AsyncSession = Depends(get_session),
    current_user_role: UserRole = Depends(get_current_user_profile_from_account),
) -> Company:
    """
    Проверяет, имеет ли текущий пользователь (UserRole) доступ к запрашиваемой компании.
    Возвращает объект Company, если доступ разрешен.
    Загружает связанные сущности для ответа.
    """

    if current_user_role.access_level == UserAccessLevelEnum.FULL_ADMIN:
        stmt = select(Company).filter(
            Company.id == company_id, Company.deleted_at.is_(None)
        )
    else:  # Иначе, он должен быть владельцем
        stmt = select(Company).filter(
            Company.id == company_id,
            Company.owner_user_role_id == current_user_role.id,
            Company.deleted_at.is_(None),
        )

    stmt = stmt.options(
        selectinload(Company.owner_user_role),
        selectinload(Company.default_cashback_config),
        selectinload(Company.subscriptions).options(
            selectinload(Subscription.tariff_plan)
        ),
    )

    result = await session.execute(stmt)
    company = result.scalars().first()

    if not company:
        raise NotFoundException(
            detail=f"Company with ID {company_id} not found or you do not have permission to access it.",
        )

    return company


async def get_verified_outlet_for_company(
    outlet_id: int,  # Из пути
    company: Company = Depends(get_owned_company),
    session: AsyncSession = Depends(get_session),
    dao: HolderDAO = Depends(get_dao),
) -> Outlet:
    """
    Получает активную торговую точку (Outlet) по ID и проверяет,
    принадлежит ли она компании, к которой у текущего пользователя есть доступ
    (через зависимость get_owned_company).
    Возвращает объект Outlet, если все проверки пройдены.
    """
    outlet = await dao.outlet.get_active(session, id_=outlet_id)

    if not outlet:
        raise OutletNotFoundException(identifier=outlet_id)

    if outlet.company_id != company.id:
        raise NotFoundException(
            detail=f"Outlet with ID {outlet_id} not found in company {company.id}."
        )

    return outlet


async def get_owned_employee_role(
    employee_role_id: int,  # Из пути
    company: Company = Depends(get_owned_company),
    session: AsyncSession = Depends(get_session),
    dao: HolderDAO = Depends(get_dao),
) -> EmployeeRole:
    """
    Получает EmployeeRole по ID и проверяет, принадлежит ли он компании,
    к которой у текущего пользователя есть доступ (через зависимость get_owned_company).
    Возвращает EmployeeRoleModel с загруженными account и assigned_outlets.
    """
    employee_role = await dao.employee_role.get_by_id_with_details(
        session, employee_role_id=employee_role_id
    )

    if not employee_role:
        raise EmployeeNotFoundException(identifier=employee_role_id)

    if employee_role.company_id != company.id:
        raise NotFoundException(
            detail=f"Employee with ID {employee_role_id} not found in company {company.id}."
        )

    return employee_role


async def get_owned_promotion(
    promotion_id: int,  # Из параметра пути
    company: Company = Depends(
        get_owned_company
    ),  # Зависит от company_id в пути и проверяет права на компанию
    session: AsyncSession = Depends(get_session),
    dao: HolderDAO = Depends(get_dao),  # Можно использовать DAO или прямой запрос
) -> Promotion:
    """
    Получает акцию по ID и проверяет, принадлежит ли она компании,
    к которой у текущего пользователя есть доступ (через зависимость get_owned_company).
    Загружает связанный cashback_config.
    """
    promotion = await dao.promotion.get_by_id_with_details(
        session, promotion_id=promotion_id
    )

    if not promotion:
        raise NotFoundException(resource_name="Promotion", identifier=promotion_id)

    if promotion.company_id != company.id:
        raise NotFoundException(
            detail=f"Promotion with ID {promotion_id} not found in company {company.id}."
        )

    return promotion


async def authenticate_bot_and_get_company_id(  # Ключевая новая зависимость
    bot_api_key: str = Depends(bot_api_key_header),
    settings: AppSettings = Depends(get_settings),
    # dao: HolderDAO = Depends(get_dao) # Если ключи и их связь с компаниями хранятся в БД
) -> int:  # Возвращает ID компании, к которой привязан бот
    """
    Аутентифицирует запрос от Telegram-бота по API-ключу и возвращает ID его компании.
    TODO: Заменить заглушку на реальную логику проверки ключей.
    """
    # Пример логики: ключи могут храниться в settings.py или в базе данных
    # BOT_API_KEYS = {
    #     "SECRET_KEY_COMPANY_1_BOT": 1,
    #     "SECRET_KEY_COMPANY_2_BOT": 2,
    # }
    # company_id = BOT_API_KEYS.get(bot_api_key)

    # ЗАГЛУШКА ДЛЯ ТЕСТИРОВАНИЯ:
    if bot_api_key == "5":
        logger.info(f"Бот для компании 1 аутентифицирован по ключу: {bot_api_key}")
        return 5
    elif bot_api_key == "TEST_BOT_KEY_COMPANY_2":
        logger.info(f"Бот для компании 2 аутентифицирован по ключу: {bot_api_key}")
        return 2
    return 3
    # --- Конец Заглушки ---


async def get_target_customer_role_for_company_operation(
    customer_role_id: int,
    requesting_company: Company = Depends(get_owned_company),
    session: AsyncSession = Depends(get_session),
    dao: HolderDAO = Depends(get_dao),
) -> CustomerRole:
    customer_role = await dao.customer_role.get_active_by_id_with_account(
        session, id_=customer_role_id
    )
    if not customer_role:
        raise NotFoundException(
            resource_name="CustomerRole", identifier=customer_role_id
        )

    if customer_role.company_id != requesting_company.id:
        raise ForbiddenException(
            detail=f"Customer profile ID {customer_role_id} does not belong to company '{requesting_company.name}' (ID: {requesting_company.id})."
        )

    if not customer_role.account or not customer_role.account.is_active:
        raise ForbiddenException(
            detail="The account associated with this customer profile is inactive."
        )

    return customer_role


async def get_customer_role_by_telegram_id_for_bot(
    telegram_user_id: int = Path(..., description="Telegram ID клиента из пути"),
    bot_company_id: int = Depends(authenticate_bot_and_get_company_id),
    session: AsyncSession = Depends(get_session),
    dao: HolderDAO = Depends(get_dao),
) -> CustomerRole:
    account = await dao.account.get_by_telegram_id_with_all_profiles(
        session, telegram_user_id=telegram_user_id
    )
    if not account or not account.is_active:
        raise NotFoundException(
            detail=f"Активный аккаунт для Telegram ID {telegram_user_id} не найден."
        )

    customer_role: Optional[CustomerRole] = None
    if account.customer_profiles:
        for cr in account.customer_profiles:
            if cr.company_id == bot_company_id:
                customer_role = cr
                break

    if not customer_role:
        raise NotFoundException(
            detail=f"Профиль клиента для Telegram ID {telegram_user_id} не найден в компании ID {bot_company_id}."
        )

    if not customer_role.account:
        customer_role.account = account

    return customer_role


def get_client_onboarding_service(
    dao: HolderDAO = Depends(get_dao),
    settings: AppSettings = Depends(get_settings),
    # Если OTP все же будет, то и OTP сервисы
) -> CustomerAuthService:  # ClientOnboardingService будет определен ниже
    return CustomerAuthService(dao=dao, settings=settings)


# Зависимость для сервиса профиля клиента
def get_customer_profile_service(
    dao: HolderDAO = Depends(get_dao),
) -> CustomerService:  # CustomerProfileService будет определен ниже
    return CustomerService(dao=dao)


def get_promotion_service(
    dao: HolderDAO = Depends(get_dao),
) -> PromotionService:
    return PromotionService(dao=dao)


def get_otp_sending_service() -> MockOTPSendingService:
    return MockOTPSendingService()


def get_account_service() -> AccountService:
    return AccountService()


def get_otp_code_service() -> OtpCodeService:
    return OtpCodeService()


def get_dashboard_service() -> DashboardService:
    return DashboardService()


def get_outlet_service(
    dao: HolderDAO = Depends(get_dao),
) -> OutletService:
    return OutletService(dao=dao)


def get_company_service(
    settings: AppSettings = Depends(get_settings),
    dao: HolderDAO = Depends(get_dao),
) -> CompanyService:
    return CompanyService(settings=settings, dao=dao)


def get_employee_service(
    dao: HolderDAO = Depends(get_dao),
) -> EmployeeService:
    return EmployeeService(dao=dao)


def get_cashback_service(
    dao: HolderDAO = Depends(get_dao),
) -> CompanyDefaultCashbackConfigService:
    return CompanyDefaultCashbackConfigService(dao=dao)


def get_auth_service(
    account_service: AccountService = Depends(get_account_service),
    otp_sending_service: MockOTPSendingService = Depends(get_otp_sending_service),
    otp_code_service: OtpCodeService = Depends(get_otp_code_service),
    settings: AppSettings = Depends(get_settings),
) -> AuthService:
    return AuthService(
        account_service=account_service,
        otp_sending_service=otp_sending_service,
        otp_code_service=otp_code_service,
        settings=settings,
    )
