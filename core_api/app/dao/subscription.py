from app.dao.base import BaseDAO
from app.models.subscription import Subscription
from app.schemas.company_subscription import SubscriptionCreate


class SubscriptionDAO(BaseDAO[Subscription, SubscriptionCreate, SubscriptionCreate]):
    def __init__(self):
        super().__init__(Subscription)
