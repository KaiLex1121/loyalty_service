# backend/main_test.py (версия 2 для теста)

from fastapi import FastAPI, Security
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader

# --- Определяем объекты FastAPI как обычно ---
oauth2_scheme_backoffice = OAuth2PasswordBearer(tokenUrl="/token")
customer_bot_api_key_header = APIKeyHeader(name="X-Bot-Customer-Api-Key")
employee_bot_api_key_header = APIKeyHeader(name="X-Employee-Bot-Api-Key")

# --- Создаем приложение, определяя ВСЕ схемы вручную ---
app = FastAPI(
    title="TEST APP - Manual OpenAPI Check",
    openapi_components={
        "securitySchemes": {
            # OAuth2 схема, определенная вручную
            "BackofficeBearerAuth": {
                "type": "oauth2",
                "flows": {
                    "password": {
                        "tokenUrl": "/token",  # Должно совпадать с tokenUrl в OAuth2PasswordBearer
                        "scopes": {},  # Можно оставить пустым или добавить описания
                    }
                },
            },
            # API Key схема 1
            "CustomerBotApiKey": {
                "type": "apiKey",
                "in": "header",
                "name": "X-Bot-Customer-Api-Key",
                "description": "API ключ для бота клиентов.",
            },
            # API Key схема 2
            "EmployeeBotApiKey": {
                "type": "apiKey",
                "in": "header",
                "name": "X-Employee-Bot-Api-Key",
                "description": "API ключ для бота сотрудников.",
            },
        }
    },
)


# --- Эндпоинты остаются те же ---
@app.get("/test/backoffice", dependencies=[Security(oauth2_scheme_backoffice)])
def test_backoffice():
    return {"message": "Backoffice OK"}


@app.get("/test/customer-bot", dependencies=[Security(customer_bot_api_key_header)])
def test_customer_bot():
    return {"message": "Customer Bot OK"}


@app.get("/test/employee-bot", dependencies=[Security(employee_bot_api_key_header)])
def test_employee_bot():
    return {"message": "Employee Bot OK"}
