from dataclasses import dataclass, field

from backend.dao.account import AccountDAO
from backend.dao.cashback_config import CashbackConfigDAO
from backend.dao.company import CompanyDAO
from backend.dao.company_default_cashback_config import CompanyDefaultCashbackConfigDAO
from backend.dao.customer_role import CustomerRoleDAO
from backend.dao.employee import EmployeeRoleDAO
from backend.dao.otp_code import OtpCodeDAO
from backend.dao.outlet import OutletDAO
from backend.dao.promotion import PromotionDAO
from backend.dao.promotion_usage import PromotionUsageDAO
from backend.dao.subscription import SubscriptionDAO
from backend.dao.tariff_plan import TariffPlanDAO
from backend.dao.user_role import UserRoleDAO


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
    default_cashback_config: CompanyDefaultCashbackConfigDAO = field(init=False)
    customer_role: CustomerRoleDAO = field(init=False)

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
        self.default_cashback_config = CompanyDefaultCashbackConfigDAO()
        self.customer_role = CustomerRoleDAO()
