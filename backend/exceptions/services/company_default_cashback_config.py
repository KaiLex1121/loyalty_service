from typing import Any, Dict, Optional

from backend.exceptions.common import InternalServerError


class CompanyDefaultCashbackNotConfiguredException(InternalServerError):
    detail = "Company default cashback is not configured."

    def __init__(
        self,
        detail: Optional[str] = None,
        internal_details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(detail=detail, internal_details=internal_details)
