from dataclasses import dataclass, field

from backend.dao.account import AccountDAO
from backend.dao.company import CompanyDAO
from backend.dao.otp_code import OtpCodeDAO
from backend.dao.subscription import SubscriptionDAO
from backend.dao.tariff_plan import TariffPlanDAO
from backend.dao.user_role import UserRoleDAO
from backend.dao.cashback import CashbackConfigDAO


@dataclass
class HolderDAO:
    account: AccountDAO = field(init=False)
    otp_code: OtpCodeDAO = field(init=False)
    user_role: UserRoleDAO = field(init=False)
    company: CompanyDAO = field(init=False)
    cashback_config: CashbackConfigDAO = field(init=False)
    tariff_plan: TariffPlanDAO = field(init=False)
    subscription: SubscriptionDAO = field(init=False)

    def __post_init__(self):
        self.account = AccountDAO()
        self.otp_code = OtpCodeDAO()
        self.user_role = UserRoleDAO()
        self.company = CompanyDAO()
        self.cashback_config = CashbackConfigDAO()
        self.tariff_plan = TariffPlanDAO()
        self.subscription = SubscriptionDAO()