from backend.dao.base import CRUDBase
from backend.models.subscription import Subscription
from backend.schemas.subscription import SubscriptionCreate


class SubscriptionDAO(CRUDBase[Subscription, SubscriptionCreate, SubscriptionCreate]):
    pass
