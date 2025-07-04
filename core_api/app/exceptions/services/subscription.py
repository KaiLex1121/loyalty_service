from typing import Any, Dict, Optional

from app.exceptions.common import NotFoundException


class SubscriptionNotFoundException(NotFoundException):
    def __init__(
        self,
        identifier: Any,
        identifier_type: str = "ID",
        detail: Optional[str] = None,
        internal_details: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not detail:
            detail = f"Subscription with {identifier_type} '{identifier}' not found."
        super().__init__(
            resource_name="Subscription",
            identifier=identifier,
            detail=detail,
            internal_details=internal_details,
        )
