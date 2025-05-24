from dataclasses import dataclass, field

from backend.dao.account import AccountDAO
from backend.dao.otp_code import OtpCodeDAO


@dataclass
class HolderDAO:
    user: AccountDAO = field(init=False)

    def __post_init__(self):
        self.account = AccountDAO()
        self.otp_code = OtpCodeDAO()
