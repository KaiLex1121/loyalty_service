from typing import Optional, Tuple

from app.core.logger import get_logger
from app.core.security import (
    http_bearer_backoffice,
    http_bearer_employee,
    internal_api_key_header,
    oauth2_scheme_backoffice,
)
from app.core.settings import AppSettings, get_settings
from app.dao.holder import HolderDAO
from app.db.session import create_pool
from app.enums import UserAccessLevelEnum
from app.exceptions.common import (
    ForbiddenException,
    NotFoundException,
    UnauthorizedException,
)
from app.exceptions.services.employee import EmployeeNotFoundException
from app.exceptions.services.outlet import OutletNotFoundException
from app.models.account import Account
from app.models.company import Company
from app.models.customer_role import CustomerRole
from app.models.employee_role import EmployeeRole
from app.models.outlet import Outlet
from app.models.promotions.promotion import Promotion
from app.models.subscription import Subscription
from app.models.telegram_bot import TelegramBot
from app.models.user_role import UserRole
from app.services.account import AccountService
from app.services.backoffice_auth import AuthService
from app.services.backoffice_dashboard import DashboardService
from app.services.company import CompanyService
from app.services.company_customer import CustomerService  # Поздний импорт
from app.services.company_default_cashback_config import (
    CompanyDefaultCashbackConfigService,
)
from app.services.company_employee import EmployeeService
from app.services.company_outlet import OutletService
from app.services.company_promotion import PromotionService
from app.services.company_telegram_broadcast import BroadcastService
from app.services.customer_bot_auth import CustomerAuthService  # Поздний импорт
from app.services.employee_bot_auth import EmployeeAuthService
from app.services.employee_customer_interaction import (
    EmployeeCustomerInteractionService,
)
from app.services.otp_code import OtpCodeService
from app.services.otp_sending import MockOTPSendingService
from app.services.transaction_cashback_calculation import CashbackCalculationService
from fastapi import Depends, HTTPException, Path, Request, Security, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from shared.enums.telegram_bot_enums import BotTypeEnum
from shared.schemas.schemas import TokenPayload
from shared.utils.security import verify_token

logger = get_logger(__name__)


async def verify_internal_api_key(
    api_key: str = Security(internal_api_key_header),
    settings: AppSettings = Depends(get_settings),
):
    if api_key != settings.API.INTERNAL_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid internal API key"
        )


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


async def get_backoffice_token_payload(
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

    token_data = verify_token(
        token=token,
        secret_key=settings.SECURITY.JWT_SECRET_KEY,
        algorithm=settings.SECURITY.ALGORITHM,
    )

    if token_data is None:
        raise credentials_exception

    return token_data


async def get_current_employee_role(
    session: AsyncSession = Depends(get_session),
    dao: HolderDAO = Depends(get_dao),
    http_credentials: HTTPAuthorizationCredentials = Depends(http_bearer_employee),
    settings: AppSettings = Depends(get_settings),
) -> tuple[EmployeeRole, TokenPayload]:
    """
    Проверяет JWT-токен сотрудника и возвращает его модель EmployeeRole.
    Используется для защиты внутренних эндпоинтов, вызываемых Bot Gateway.
    """
    print('Checking employee role...')
    if not http_credentials:
        raise UnauthorizedException("Auth credentials are not provided")

    token = http_credentials.credentials
    payload = verify_token(
        token=token,
        secret_key=settings.SECURITY.JWT_SECRET_KEY,
        algorithm=settings.SECURITY.ALGORITHM,
    )
    if not payload:
        raise UnauthorizedException(
            "Invalid or expired token, or missing required scope."
        )

    try:
        employee_role_id = int(payload.sub)
    except (ValueError, TypeError):
        raise UnauthorizedException("Invalid token payload subject.")

    employee = await dao.employee_role.get_by_id_with_details(session, employee_role_id)
    if not employee or not employee.account or not employee.account.is_active:
        raise UnauthorizedException("Employee not found or inactive.")

    return employee, payload


async def get_employee_token_payload(
    http_credentials: HTTPAuthorizationCredentials = Depends(http_bearer_employee),
    settings: AppSettings = Depends(get_settings),
) -> TokenPayload:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate admin credentials.",
        headers={
            "WWW-Authenticate": http_bearer_employee.scheme_name
        },  # Используем имя схемы
    )
    if http_credentials:
        token = http_credentials.credentials
    else:
        token = oauth_token

    if http_credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен отсутствует",
            headers={"WWW-Authenticate": http_bearer_employee.scheme_name},
        )
    token_data = verify_token(
        token=token,
        secret_key=settings.SECURITY.JWT_SECRET_KEY,
        algorithm=settings.SECURITY.ALGORITHM,
    )

    if token_data is None:
        raise credentials_exception

    return token_data


async def get_current_account_without_relations(
    session: AsyncSession = Depends(get_session),
    dao: HolderDAO = Depends(get_dao),
    token_payload: TokenPayload = Depends(get_backoffice_token_payload),
) -> Optional[Account]:
    """
    Зависимость для получения текущего пользователя на основе JWT токена.
    """
    if "backoffice_user" not in token_payload.scopes:
        raise ForbiddenException(
            detail="Not authorized for backoffice operations. Missing 'backoffice_user' scope."
        )
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
    token_payload: TokenPayload = Depends(get_backoffice_token_payload),
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
    token_payload: TokenPayload = Depends(get_backoffice_token_payload),
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
    company_id: int = Path(..., description="The ID of the company to access"),
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


async def authenticate_bot_and_get_company(
    bot_token: str = Path(..., description="Уникальный токен Telegram-бота из URL"),
    session: AsyncSession = Depends(get_session),
    dao: HolderDAO = Depends(get_dao),
) -> Tuple[int, BotTypeEnum]:
    """
    Аутентифицирует запрос от Telegram-бота по токену из URL.
    Возвращает ID компании и тип бота.
    """
    bot = await dao.telegram_bot.get_by_token(session, token=bot_token)

    if not bot:
        # Не используем NotFoundException, чтобы не раскрывать существование токенов
        raise UnauthorizedException(detail="Invalid or missing bot token.")

    if not bot.is_active:
        raise ForbiddenException(detail="This bot is currently inactive.")

    return bot.company_id, bot.bot_type


async def authenticate_customer_bot_and_get_company_id(
    bot_data: Tuple[int, BotTypeEnum] = Depends(authenticate_bot_and_get_company),
) -> int:
    """
    Проверяет, что бот является клиентским, и возвращает ID его компании.
    """
    company_id, bot_type = bot_data
    if bot_type != BotTypeEnum.CUSTOMER:
        raise ForbiddenException(detail="This operation requires a customer bot token.")
    return company_id


async def authenticate_employee_bot_and_get_company_id(
    bot_data: Tuple[int, BotTypeEnum] = Depends(authenticate_bot_and_get_company),
) -> int:
    """
    Проверяет, что бот является ботом для сотрудников, и возвращает ID его компании.
    """
    company_id, bot_type = bot_data
    if bot_type != BotTypeEnum.EMPLOYEE:
        raise ForbiddenException(
            detail="This operation requires an employee bot token."
        )
    return company_id


async def get_employee_role_id_from_token_payload(
    token_payload: TokenPayload = Depends(get_employee_token_payload),
) -> int:
    """Извлекает employee_role_id из payload и проверяет скоуп сотрудника."""
    required_scope = "employee.workspace:bot"
    if required_scope not in token_payload.scopes:
        raise ForbiddenException(
            detail=f"Not authorized for employee operations. Missing '{required_scope}' scope."
        )
    try:
        # Для сотрудника в 'sub' находится employee_role_id
        employee_role_id = int(token_payload.sub)
        return employee_role_id
    except (ValueError, TypeError, AttributeError):
        logger.error(f"Invalid 'sub' in employee token payload: {token_payload.sub}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid employee token payload (subject).",
        )


async def get_current_employee_role_for_bot_company(  # Новая основная зависимость для сотрудника
    employee_role_id: int = Depends(
        get_employee_role_id_from_token_payload
    ),  # ID из токена
    # ID компании, к которой привязан бот сотрудников, через который идет запрос
    current_employee_bot_company_id: int = Depends(
        authenticate_employee_bot_and_get_company_id
    ),
    session: AsyncSession = Depends(get_session),
    dao: HolderDAO = Depends(get_dao),
) -> EmployeeRole:
    """
    Извлекает EmployeeRole на основе JWT токена сотрудника и проверяет его принадлежность
    к компании текущего бота сотрудников.
    """
    employee_role = await dao.employee_role.get_by_id_with_details(
        session, employee_role_id=employee_role_id
    )

    if not employee_role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Профиль сотрудника не найден для данного токена.",
        )

    if not employee_role.account or not employee_role.account.is_active:
        # EmployeeRole связан с Account, который должен быть активен
        raise ForbiddenException(
            detail="Связанный аккаунт для этого профиля сотрудника неактивен."
        )

    # Ключевая проверка: EmployeeRole должен принадлежать компании текущего бота сотрудников
    if employee_role.company_id != current_employee_bot_company_id:
        # logger.error(f"Токен сотрудника (EmployeeRole {employee_role.id}, компания {employee_role.company_id}) "
        #              f"использован с ботом для компании {current_employee_bot_company_id}.")
        raise ForbiddenException(
            detail="Профиль сотрудника не принадлежит компании, обслуживаемой этим ботом."
        )

    return employee_role


async def get_target_customer_role_for_employee_operation(
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
    bot_company_id: int = Depends(authenticate_customer_bot_and_get_company_id),
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


async def get_owned_bot(
    bot_id: int = Path(..., description="ID of the bot"),
    company: Company = Depends(get_owned_company),  # Зависит от company_id в пути
    session: AsyncSession = Depends(get_session),
    dao: HolderDAO = Depends(get_dao),
) -> TelegramBot:
    """
    Проверяет, что запрашиваемый бот принадлежит компании,
    к которой у текущего администратора есть доступ.
    """
    bot = await dao.telegram_bot.get_by_id_and_company_id(
        session, bot_id=bot_id, company_id=company.id
    )
    if not bot:
        raise NotFoundException(
            detail=f"Bot with ID {bot_id} not found in company {company.id}."
        )
    return bot


async def get_internal_api_key(
    api_key: str = Security(internal_api_key_header),
    settings: AppSettings = Depends(get_settings),
) -> str:
    if api_key == settings.API.INTERNAL_KEY:
        return api_key
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Invalid or missing Internal API Key",
    )


def get_client_onboarding_service(
    dao: HolderDAO = Depends(get_dao),
    settings: AppSettings = Depends(get_settings),
) -> CustomerAuthService:
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


def get_cashback_calculation_service(
    dao: HolderDAO = Depends(get_dao),
) -> CashbackCalculationService:
    return CashbackCalculationService(dao=dao)


def get_employee_customer_interaction_service(
    dao: HolderDAO = Depends(get_dao),
    cashback_calculation_service: CashbackCalculationService = Depends(
        get_cashback_calculation_service
    ),
    otp_code_service: OtpCodeService = Depends(get_otp_code_service),
    otp_sending_service: MockOTPSendingService = Depends(get_otp_sending_service),
    settings: AppSettings = Depends(get_settings),
) -> EmployeeCustomerInteractionService:
    return EmployeeCustomerInteractionService(
        dao=dao,
        cashback_calculation_service=cashback_calculation_service,
        otp_code_service=otp_code_service,
        settings=settings,
        otp_sending_service=otp_sending_service,
    )


def get_broadcast_service(
    dao: HolderDAO = Depends(get_dao),
) -> BroadcastService:
    """
    Зависимость для получения экземпляра BroadcastService.
    В будущем сюда можно будет добавить другие зависимости, если они понадобятся сервису.
    """
    return BroadcastService(dao=dao)


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


def get_employee_auth_service(
    settings: AppSettings = Depends(get_settings),
    dao: HolderDAO = Depends(get_dao),
    otp_code_service: OtpCodeService = Depends(get_otp_code_service),
    otp_sending_service: MockOTPSendingService = Depends(get_otp_sending_service),
) -> EmployeeAuthService:
    return EmployeeAuthService(
        otp_code_service=otp_code_service,
        otp_sending_service=otp_sending_service,
        settings=settings,
        dao=dao,
    )
