from app.dao.base import BaseDAO

from app.models.broadcast import Broadcast
from app.schemas.broadcast import BroadcastCreateInternal


class BroadcastDAO(BaseDAO[Broadcast, BroadcastCreateInternal, BroadcastCreateInternal]):
    def __init__(self):
        super().__init__(Broadcast)