# backend/services/employee_auth.py
from typing import Optional, Tuple

from asyncpg import InternalServerError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.security import (
    create_access_token,
    generate_otp,
    get_otp_expiry_time,
    get_otp_hash,
    verify_otp_hash,
)
from backend.core.settings import AppSettings
from backend.dao.holder import HolderDAO
from backend.enums import OtpPurposeEnum  # Убедитесь, что EMPLOYEE_BOT_LOGIN там есть

# Кастомные исключения (создайте их, если еще нет, по аналогии с другими)
from backend.exceptions.services.employee_auth import (
    EmployeeAccountInactiveException,
    EmployeeNotFoundInCompanyForLoginException,
    EmployeeOTPExpiredException,
    EmployeeOTPNotFoundException,
    EmployeeOTPSendingException,
    InvalidEmployeeOTPException,
)
from backend.models.account import Account  # Нужен для AccountService и для типа
from backend.models.employee_role import EmployeeRole
from backend.schemas.employee_bot_auth import (  # Схема для верификации OTP сотрудника
    EmployeeOtpVerify,
)
from backend.schemas.otp_code import OtpCodeCreate
from backend.schemas.token import (  # Ваша стандартная схема ответа с токеном
    TokenResponse,
)
from backend.services.account import AccountService  # Для работы с Account
from backend.services.otp_code import OtpCodeService  # Для работы с OTP
from backend.services.otp_sending import (  # Или ваш реальный сервис отправки
    MockOTPSendingService,
)

# from backend.core.logger import get_logger
# logger = get_logger(__name__)


class EmployeeAuthService:
    def __init__(
        self,
        otp_code_service: OtpCodeService,  # Сервис для работы с OTP кодами
        otp_sending_service: MockOTPSendingService,  # Сервис для отправки OTP
        settings: AppSettings,
        dao: HolderDAO,  # DAO для прямого доступа, если нужно (например, к EmployeeRole)
    ):
        self.otp_code_service = otp_code_service
        self.otp_sending_service = otp_sending_service
        self.settings = settings
        self.dao = dao

    async def request_otp_for_employee_login(
        self,
        session: AsyncSession,
        work_phone_number: str,
        bot_company_id: int,  # ID компании, к которой привязан бот сотрудников
    ) -> EmployeeRole:  # Возвращаем EmployeeRole, чтобы показать, для кого запрошен OTP
        """
        Запрашивает OTP для входа сотрудника.
        Находит EmployeeRole по work_phone_number и bot_company_id.
        Создает и отправляет OTP.
        """
        # logger.info(f"Запрос OTP для сотрудника: тел. {work_phone_number}, компания ID {bot_company_id}")

        # 1. Найти EmployeeRole по рабочему номеру телефона и ID компании бота
        employee_role = (
            await self.dao.employee_role.get_by_work_phone_and_company_id_with_account(
                session, work_phone_number=work_phone_number, company_id=bot_company_id
            )
        )

        if not employee_role:
            # logger.warning(f"Сотрудник с рабочим тел. {work_phone_number} не найден в компании ID {bot_company_id}.")
            raise EmployeeNotFoundInCompanyForLoginException(
                work_phone_number=work_phone_number, company_id=bot_company_id
            )

        if not employee_role.account:  # Должен быть загружен DAO методом
            # logger.error(f"Критическая ошибка: Account не загружен для EmployeeRole ID {employee_role.id}")
            # Это внутренняя ошибка, если DAO не отработал как ожидалось
            raise InternalServerError(
                f"Внутренняя ошибка: не удалось загрузить данные аккаунта для сотрудника ID {employee_role.id}."
            )

        if not employee_role.account.is_active:
            # logger.warning(f"Аккаунт сотрудника {employee_role.account.id} (EmployeeRole ID {employee_role.id}) неактивен.")
            raise EmployeeAccountInactiveException(account_id=employee_role.account.id)

        # 2. Генерация и сохранение OTP
        otp_purpose = OtpPurposeEnum.EMPLOYEE_VERIFICATION
        plain_otp = generate_otp(self.settings)  # Используем вашу функцию генерации OTP
        hashed_otp = get_otp_hash(plain_otp, self.settings)
        otp_expires_at = get_otp_expiry_time(self.settings)

        # Инвалидируем предыдущие OTP для этого аккаунта и цели
        await self.otp_code_service.invalidate_previous_otps(
            session, dao=self.dao, account=employee_role.account, purpose=otp_purpose
        )

        otp_code_schema = OtpCodeCreate(
            hashed_code=hashed_otp,
            expires_at=otp_expires_at,
            purpose=otp_purpose,
            account_id=employee_role.account_id,  # OTP привязывается к Account
            channel="employee_bot",  # Канал отправки
        )
        await self.otp_code_service.create_otp(
            session=session, dao=self.dao, obj_in=otp_code_schema
        )

        # 3. Отправка OTP (например, через SMS на work_phone_number или через Telegram, если есть связь)
        # Для простоты, отправляем на work_phone_number
        sms_sent_successfully = await self.otp_sending_service.send_otp(
            phone_number=employee_role.work_phone_number,  # Отправляем на рабочий номер
            otp_code=plain_otp,
        )
        if not sms_sent_successfully:
            # logger.error(f"Не удалось отправить OTP на рабочий номер {employee_role.work_phone_number} для EmployeeRole ID {employee_role.id}")
            raise EmployeeOTPSendingException(
                phone_number=employee_role.work_phone_number
            )

        # logger.info(f"OTP успешно запрошен для EmployeeRole ID {employee_role.id} (Account ID {employee_role.account_id}).")
        return employee_role  # Возвращаем EmployeeRole, чтобы API мог вернуть какие-то данные, если нужно

    async def verify_otp_and_login_employee(
        self,
        session: AsyncSession,
        otp_data: EmployeeOtpVerify,  # Содержит work_phone_number и otp_code
        bot_company_id: int,  # ID компании, к которой привязан бот сотрудников
    ) -> TokenResponse:
        """
        Проверяет OTP сотрудника и в случае успеха выдает JWT токен.
        """
        # logger.info(f"Попытка верификации OTP для сотрудника: тел. {otp_data.work_phone_number}, компания ID {bot_company_id}")

        # 1. Найти EmployeeRole (и связанный Account)
        employee_role = (
            await self.dao.employee_role.get_by_work_phone_and_company_id_with_account(
                session,
                work_phone_number=otp_data.work_phone_number,
                company_id=bot_company_id,
            )
        )
        if not employee_role:
            raise EmployeeNotFoundInCompanyForLoginException(
                work_phone_number=otp_data.work_phone_number, company_id=bot_company_id
            )
        if not employee_role.account:  # Должен быть загружен
            raise Exception(
                f"Внутренняя ошибка: не удалось загрузить данные аккаунта для сотрудника ID {employee_role.id}."
            )
        if not employee_role.account.is_active:
            raise EmployeeAccountInactiveException(account_id=employee_role.account.id)

        # 2. Проверка OTP (используем методы из OtpCodeService, как в вашем AuthService)
        active_otp_code_model = await self.dao.otp_code.get_active_otp_by_account_and_purpose(
            session,
            account_id=employee_role.account_id,
            purpose=OtpPurposeEnum.EMPLOYEE_VERIFICATION,  # Используем правильный purpose
        )
        if not active_otp_code_model:
            raise EmployeeOTPNotFoundException(account_id=employee_role.account_id)

        if (
            active_otp_code_model.is_expired
        ):  # Убедитесь, что is_expired есть в модели OtpCode
            raise EmployeeOTPExpiredException(otp_id=active_otp_code_model.id)

        if not verify_otp_hash(
            otp_code=otp_data.otp_code,
            hashed_otp_code=active_otp_code_model.hashed_code,
            settings=self.settings,
        ):
            # Можно добавить логику увеличения счетчика попыток и блокировки OTP
            # await self.otp_code_service.increment_attempts(session, self.dao, active_otp_code_model)
            raise InvalidEmployeeOTPException(otp_id=active_otp_code_model.id)

        # Помечаем OTP как использованный
        await self.otp_code_service.set_mark_otp_as_used(
            session, dao=self.dao, otp_obj=active_otp_code_model
        )

        # 3. Генерация JWT токена
        # Субъектом токена будет employee_role.id
        # В claims можно добавить company_id и account_id для удобства
        token_payload_data = {
            "sub": str(employee_role.id),
            "account_id": employee_role.account_id,
            "company_id": employee_role.company_id,
        }

        jwt_scopes = [
            "employee.workspace:bot"
        ]  # Скоуп для сотрудника, работающего в боте
        # Можно добавить доп. скоупы на основе employee_role.position, если есть разные уровни доступа у сотрудников

        access_token = create_access_token(
            data=token_payload_data, settings=self.settings, scopes=jwt_scopes
        )

        # logger.info(f"Сотрудник EmployeeRole ID {employee_role.id} успешно аутентифицирован. Токен выдан.")
        return TokenResponse(access_token=access_token, token_type="bearer")
