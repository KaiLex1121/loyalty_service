import logging
from typing import Optional

from fastapi import (APIRouter, Depends, Form, HTTPException, Request,
                     Response, status)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.dependencies import (get_auth_service,
                                       get_current_active_user,
                                       get_current_user_from_cookie, get_dao,
                                       get_jinja_templates, get_session)
from backend.core.settings import settings
from backend.dao.holder import HolderDAO
from backend.models.user import User
from backend.schemas.auth import OTPVerifyRequest, PhoneRequest
from backend.schemas.token import Token
from backend.schemas.user import UserBase, UserInDBBase
from backend.services.auth import AuthService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/phone-entry", response_class=HTMLResponse, name="phone_entry_page")
async def login_sms_page(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_from_cookie),
    templates: Jinja2Templates = Depends(get_jinja_templates),
):
    if current_user and current_user.is_active:
        return RedirectResponse(
            url=request.url_for("page_profile"), status_code=status.HTTP_302_FOUND
        )
    return templates.TemplateResponse(
        "auth/phone-entry.html", {"request": request, "error": None}
    )


@router.post(
    "/phone-entry", response_class=HTMLResponse, name="handle_phone_entry_page"
)
async def handle_login_sms_request(
    request: Request,
    phone_number: str = Form(...),
    auth_svc: AuthService = Depends(get_auth_service),
    db: AsyncSession = Depends(get_session),
    dao: HolderDAO = Depends(get_dao),
    templates: Jinja2Templates = Depends(get_jinja_templates),
):
    try:
        _ = await auth_svc.request_otp(db, dao, phone_number=phone_number)
        verify_url = request.url_for("verify_otp_page").include_query_params(
            phone=phone_number
        )
        return RedirectResponse(url=verify_url, status_code=status.HTTP_303_SEE_OTHER)
    except HTTPException as e:
        return templates.TemplateResponse(
            "auth/phone-entry.html",
            {"request": request, "error": e.detail, "phone_number": phone_number},
        )
    except Exception:
        logger.error("Error in handle_login_sms_request", exc_info=True)
        return templates.TemplateResponse(
            "auth/phone-entry.html",
            {
                "request": request,
                "error": "Произошла непредвиденная ошибка.",
                "phone_number": phone_number,
            },
        )


@router.get("/verify-otp", response_class=HTMLResponse, name="verify_otp_page")
async def verify_otp_page(
    request: Request,
    phone: str,
    current_user: Optional[User] = Depends(get_current_user_from_cookie),
    templates: Jinja2Templates = Depends(get_jinja_templates),
):
    if current_user and current_user.is_active:
        return RedirectResponse(
            url=request.url_for("page_profile"), status_code=status.HTTP_302_FOUND
        )
    if not phone:
        return RedirectResponse(
            url=request.url_for("page_login_sms"), status_code=status.HTTP_302_FOUND
        )
    return templates.TemplateResponse(
        "auth/code-entry.html",
        {"request": request, "phone_number": phone, "error": None},
    )


@router.post("/verify-otp", response_class=HTMLResponse, name="handle_verify_otp_page")
async def handle_verify_otp_and_set_cookie(
    request: Request,
    fastapi_response: Response,  # Для установки cookie
    phone_number: str = Form(...),
    otp_code: str = Form(...),
    auth_svc: AuthService = Depends(get_auth_service),
    db: AsyncSession = Depends(get_session),
    dao: HolderDAO = Depends(get_dao),
    templates: Jinja2Templates = Depends(get_jinja_templates),
):
    try:
        access_token = await auth_svc.verify_otp_and_login(
            db, dao, phone_number=phone_number, otp_code=otp_code
        )
        # Устанавливаем токен в HttpOnly cookie
        # ACCESS_TOKEN_EXPIRE_MINUTES должно быть доступно (например, из settings)
        # Если settings.ACCESS_TOKEN_EXPIRE_MINUTES нет, используйте значение по умолчанию
        token_expire_minutes = settings.SECURITY.ACCESS_TOKEN_EXPIRE_MINUTES

        fastapi_response.set_cookie(
            key="access_token",
            value=f"Bearer {access_token}",  # Добавляем "Bearer " для консистентности, если get_current_user_from_cookie его ожидает
            httponly=True,
            samesite="lax",  # "lax" или "strict"
            max_age=token_expire_minutes * 60,
            # secure=True, # ВАЖНО: True для HTTPS в продакшене
            path="/",  # Cookie доступен для всего сайта
        )
        # Редирект на страницу профиля. Важно передать headers от fastapi_response, чтобы cookie установился.
        return RedirectResponse(
            url=request.url_for("index_page"),
            status_code=status.HTTP_303_SEE_OTHER,
            headers=fastapi_response.headers,
        )
    except HTTPException as e:
        return templates.TemplateResponse(
            "auth/code-entry.html",
            {"request": request, "phone_number": phone_number, "error": e.detail},
        )
    except Exception:
        logger.error("Error in handle_verify_otp_page", exc_info=True)
        return templates.TemplateResponse(
            "auth/code-entry.html",
            {
                "request": request,
                "phone_number": phone_number,
                "error": "Произошла непредвиденная ошибка.",
            },
        )


@router.get(
    "/resend_sms_code", response_class=HTMLResponse, name="resend_sms_code_page"
)
async def resend_sms_code_page(
    request: Request,
    phone: str,
    current_user: Optional[User] = Depends(get_current_user_from_cookie),
    templates: Jinja2Templates = Depends(get_jinja_templates),
):
    # phone - это номер телефона из query параметра (?phone=...)
    if current_user and current_user.is_active:
        return RedirectResponse(
            url=request.url_for("page_profile"), status_code=status.HTTP_302_FOUND
        )
    if not phone:
        return RedirectResponse(
            url=request.url_for("page_login_sms"), status_code=status.HTTP_302_FOUND
        )
    return templates.TemplateResponse(
        "auth/phone-entry.html",
        {"request": request, "phone_number": phone, "error": None},
    )
