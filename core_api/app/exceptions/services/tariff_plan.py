from typing import Any, Dict, Optional

from app.exceptions.common import ConflictException, ValidationException


class TariffPlanNameConflictException(ConflictException):
    detail = "Tariff plan with this name already exists."

    def __init__(
        self,
        name: str,
        detail: Optional[str] = None,
        internal_details: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not detail:
            detail = f"Tariff plan with name '{name}' already exists."
        _internal_details = {"tariff_name": name}
        if internal_details:
            _internal_details.update(internal_details)
        super().__init__(detail=detail, internal_details=_internal_details)


class ActiveTrialPlanConflictException(
    ValidationException
):  # Используем ValidationException (422)
    detail = "An active trial plan already exists."

    def __init__(
        self,
        existing_plan_name: str,
        detail: Optional[str] = None,
        internal_details: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not detail:
            detail = f"An active trial plan ('{existing_plan_name}') already exists. Cannot create another active trial plan."
        _internal_details = {"existing_active_trial_plan_name": existing_plan_name}
        if internal_details:
            _internal_details.update(internal_details)
        super().__init__(detail=detail, internal_details=_internal_details)
