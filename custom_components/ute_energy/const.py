"""Constants for the UTE Energy integration."""

DOMAIN = "ute_energy"

REQUEST_TOKEN: str = "REQUEST_TOKEN"
REQUEST_CODE: str = "REQUEST_CODE"
VALIDATE_CODE: str = "VALIDATE_CODE"
GET_ACCOUNTS: str = "GET_ACCOUNTS"
GET_ACCOUNT_INFO: str = "GET_ACCOUNT_INFO"

PROTO: str = "https"
HOST: str = "rocme.ute.com.uy"
BASE_URL: str = f"{PROTO}://{HOST}/api/"

HEADERS: dict[str, str] = {
    "X-Client-Type": "Android",
    "Content-Type": "application/json; charset=utf-8",
    "Host": f"{HOST}",
    "User-Agent": "okhttp/3.8.1",
    "Accept-Encoding": "gzip",
    "Connection": "keep-alive",
    "Accept": "*/*",
}

ENPOINTS: dict[str, str] = {
    REQUEST_TOKEN: "v1/token",
    REQUEST_CODE: "v1/users/register",
    VALIDATE_CODE: "v1/users/validate",
    GET_ACCOUNTS: "v1/accounts",
}

TOKEN_TYPE: str = "Bearer"
PHONE_LENGHT = 11
PHONE_START_WIHT = "598"


DEFAULT_USER_PHONE = "598XXXXXXXX"
CONF_USER_ACCOUNTS = "user_accounts"
CONF_USER_EMAIL = "user_email"
CONF_USER_PHONE = "user_phone"
CONF_AUTH_CODE = "auth_code"

ACCOUNT_SERVICE_POINT_ID = "accountServicePointId"
