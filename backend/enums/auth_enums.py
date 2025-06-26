import enum


class UserAccessLevelEnum(str, enum.Enum):
    """
    Уровень доступа пользователя.
    """

    FULL_ADMIN = "full_admin"
    COMPANY_OWNER = "company_owner"
    COMPANY_MANAGER = "company_manager"
    SUPPORT_SPECIALIST = "support_specialist"


class OtpPurposeEnum(str, enum.Enum):
    """
    Назначение OTP кода.
    """

    BACKOFFICE_LOGIN = "backoffice_login"  # Для входа в систему
    PHONE_RESET = "phone_reset"  # Для сброса номера телефона
    TRANSACTION_CONFIRM = (
        "transaction_confirm"  # Для подтверждения важных транзакций/операций
    )
    EMPLOYEE_VERIFICATION = "employee_verification"  # Для верификации сотрудника
    CUSTOMER_VERIFICATION = "customer_verification"  # Для верификации клиента
    EMAIL_VERIFICATION = "email_verification"  # Для верификации email
