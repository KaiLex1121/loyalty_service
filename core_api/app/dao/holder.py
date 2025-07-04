from dataclasses import dataclass, field

from app.dao.account import AccountDAO
from app.dao.cashback_config import CashbackConfigDAO
from app.dao.company import CompanyDAO
from app.dao.company_default_cashback_config import CompanyDefaultCashbackConfigDAO
from app.dao.customer_role import CustomerRoleDAO
from app.dao.employee import EmployeeRoleDAO
from app.dao.otp_code import OtpCodeDAO
from app.dao.outlet import OutletDAO
from app.dao.promotion import PromotionDAO
from app.dao.promotion_usage import PromotionUsageDAO
from app.dao.subscription import SubscriptionDAO
from app.dao.tariff_plan import TariffPlanDAO
from app.dao.telegram_bot import TelegramBotDAO
from app.dao.transaction import TransactionDAO
from app.dao.user_role import UserRoleDAO
from app.dao.broadcast import BroadcastDAO


@dataclass
class HolderDAO:
    account: AccountDAO = field(init=False)
    otp_code: OtpCodeDAO = field(init=False)
    user_role: UserRoleDAO = field(init=False)
    company: CompanyDAO = field(init=False)
    cashback_config: CashbackConfigDAO = field(init=False)
    tariff_plan: TariffPlanDAO = field(init=False)
    subscription: SubscriptionDAO = field(init=False)
    outlet: OutletDAO = field(init=False)
    employee_role: EmployeeRoleDAO = field(init=False)
    promotion_usage: PromotionUsageDAO = field(init=False)
    promotion: PromotionDAO = field(init=False)
    default_company_cashback_config: CompanyDefaultCashbackConfigDAO = field(init=False)
    customer_role: CustomerRoleDAO = field(init=False)
    transaction: TransactionDAO = field(init=False)
    telegram_bot: TelegramBotDAO = field(init=False)
    broadcast: BroadcastDAO = field(init=False)

    def __post_init__(self):
        self.account = AccountDAO()
        self.otp_code = OtpCodeDAO()
        self.user_role = UserRoleDAO()
        self.company = CompanyDAO()
        self.cashback_config = CashbackConfigDAO()
        self.tariff_plan = TariffPlanDAO()
        self.subscription = SubscriptionDAO()
        self.outlet = OutletDAO()
        self.employee_role = EmployeeRoleDAO()
        self.promotion_usage = PromotionUsageDAO()
        self.promotion = PromotionDAO()
        self.default_company_cashback_config = CompanyDefaultCashbackConfigDAO()
        self.customer_role = CustomerRoleDAO()
        self.transaction = TransactionDAO()
        self.telegram_bot = TelegramBotDAO()
        self.broadcast = BroadcastDAO()
