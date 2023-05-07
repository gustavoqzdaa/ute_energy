"""Constants for the UTE Energy integration."""

DOMAIN: str = "ute_energy"
DEFAULT_NAME: str = "Ute Energy"
MANUFACTURER: str = "@gustavoqzdaa"
SOURCE_URL: str = "https://github.com/gustavoqzdaa/ute_energy"

REQUEST_TOKEN: str = "REQUEST_TOKEN"
REQUEST_CODE: str = "REQUEST_CODE"
VALIDATE_CODE: str = "VALIDATE_CODE"
BASE_ACCOUNTS: str = "BASE_ACCOUNTS"
GET_ACCOUNT_INFO: str = "GET_ACCOUNT_INFO"
PEAK_INFO: str = "PEAK_INFO"
MISC_BEHAVIOUR: str = "MISC_BEHAVIOUR"
INVOICE_INFO: str = "INVOICE_INFO"
REQUEST_CONSUMPTION: str = "REQUEST_CONSUMPTION"
READING_REQUEST: str = "READING_REQUEST"
LAST_READING: str = "LAST_READING"
DEFAULT_PRECISION: int = 1

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

ENDPOINTS: dict[str, str] = {
    REQUEST_TOKEN: "v1/token",
    REQUEST_CODE: "v1/users/register",
    VALIDATE_CODE: "v1/users/validate",
    BASE_ACCOUNTS: "v1/accounts",
    PEAK_INFO: "v1/accounts/{}/peak",
    MISC_BEHAVIOUR: "v1/misc/behaviour",
    INVOICE_INFO: "v2/invoices/{}/1/36",
    REQUEST_CONSUMPTION: "v2/invoices/chart/{}",
    READING_REQUEST: "v1/device/readingRequest",
    LAST_READING: "v1/device/{}/lastReading/30",
}

TOKEN_TYPE: str = "Bearer"

PHONE_LENGHT: int = 11
PHONE_START_WIHT: str = "598"
DEFAULT_USER_PHONE: str = "598XXXXXXXX"
CONF_USER_ACCOUNTS: str = "user_accounts"
CONF_USER_EMAIL: str = "user_email"
CONF_USER_PHONE: str = "user_phone"
CONF_AUTH_CODE: str = "auth_code"
ACCOUNT_SERVICE_POINT_ID: str = "accountServicePointId"
ACCOUNT_SERVICE_POINT_ADDRESS: str = "servicePointAddress"
ACCOUNT_ID: str = "accountId"
RESPONSE_RESULT: str = "result"
RESPONSE_STATUS: str = "success"
RESPONSE_ERRORS: str = "errors"
RESPONSE_ERROR_MESSAGE: str = "text"
CONNECTION: str = "connection"
AGREEMENT_INFO: str = "agreementInfo"
ENTRY_NAME: str = "name"
ENTRY_COORDINATOR: str = "coordinator"
UPDATE_LISTENER: str = "update_listener"
TARIFAS: dict[str, str] = {"TRT": "Tarifa Resindencial Triple Horario"}
SIMPLE_TARIFF: str = "TRS"
DOUBLE_TARIFF: str = "TRD"
TRIPLE_TARIFF: str = "TRT"
INVOICES: str = "invoices"
LATEST_INVOICE = "latest_invoice"
MONTH_CHARGES = "monthCharges"
CURRENCY_UYU: str = "$U"
CONTRACTED_POWER_ON_PEAK = "contractedPowerOnPeak"
CONTRACTED_POWER_ON_VALLEY = "contractedPowerOnValley"
CONTRACTED_POWER_ON_FLAT = "contractedPowerOnFlat"
CONTRACTED_TARIFF = "tariff"
CONTRACTED_VOLTAGE = "voltage"
SERVICE_AGREEMENT_ID = "serviceAgreementId"
SELECTED_PEAK = "selectedPeakStartDescription"
METER_PEAK = "meterPeakStartDescription"
MONTH_CONSUMPTION = "categoryLong"
ACTIVE_CONSUMPTION = "consumosActiva"
SINGLE_SERIE = "unaSerie"

ATTRIBUTION = "Data provided by Ute Energy"
DATA = "data"
MONTH = "month"
YEAR = "year"
VALUE = "value"
VALOR = "valor"
ID = "id"
READINGS = "readings"
CURRENT_POWER = "current_power"
CONSUMPTION_ATTR = "tipoLecturaMGMI"
CURRENT_CONSUMPTION = "I1"
CURRENT_VOLTAGE = "V1"
CURRENT_STATUS = "RELAY_ON"
