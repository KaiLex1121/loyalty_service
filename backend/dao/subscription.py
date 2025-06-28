from backend.dao.base import BaseDAO
from backend.models.subscription import Subscription
from backend.schemas.company_subscription import SubscriptionCreate


class SubscriptionDAO(BaseDAO[Subscription, SubscriptionCreate, SubscriptionCreate]):
    def __init__(self):
        super().__init__(Subscription)
