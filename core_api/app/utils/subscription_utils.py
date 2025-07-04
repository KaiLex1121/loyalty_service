from app.enums import SubscriptionStatusEnum
from app.exceptions.services.company import (
    ActiveSubscriptionsNotFoundException,
    SubscriptionsNotFoundException,
)
from app.models.company import Company
from app.models.subscription import Subscription


def get_current_subscription(  # Переименовал, чтобы не конфликтовать с @property в модели
    company_model: Company,
) -> Subscription:
    """Выбирает 'текущую' подписку для отображения из загруженных."""

    if not company_model.subscriptions:
        raise SubscriptionsNotFoundException(
            identifier=company_model.id, identifier_type="ID"
        )

    valid_subscriptions = [
        sub for sub in company_model.subscriptions if not sub.is_deleted
    ]

    if not valid_subscriptions:
        raise ActiveSubscriptionsNotFoundException(
            identifier=company_model.id, identifier_type="ID"
        )

    # Сортируем: сначала активные, потом триалы, потом просроченные, затем по дате начала (новейшие первые)
    def sort_key(sub: Subscription):
        status_priority = {
            SubscriptionStatusEnum.ACTIVE: 0,
            SubscriptionStatusEnum.TRIALING: 1,
            SubscriptionStatusEnum.PAST_DUE: 2,
            SubscriptionStatusEnum.CANCELED: 3,
            SubscriptionStatusEnum.EXPIRED: 4,
            SubscriptionStatusEnum.INCOMPLETE: 5,
            SubscriptionStatusEnum.INCOMPLETE_EXPIRED: 6,
            SubscriptionStatusEnum.UNPAID: 7,
        }
        return (status_priority.get(sub.status, 99), -sub.start_date.toordinal())

    return sorted(valid_subscriptions, key=sort_key)[0]
