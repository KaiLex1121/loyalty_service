from typing import List, Optional

from pydantic import BaseModel


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class TokenPayload(BaseModel):
    sub: str
    exp: int

    scopes: List[str] = []  # Например, ["client"] или ["backoffice_admin"]
    company_id: Optional[int] = (
        None  # Для клиентского токена, чтобы знать контекст компании
    )
    account_id: Optional[int] = None  # Для клиентского токена, ID связанного Account
