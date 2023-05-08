"""Perform UTE API requests"""
from __future__ import annotations

import logging
import json
import requests
import datetime
import time

from typing import Any
from .utils import (
    generate_random_string,
    generate_random_agent_id,
    convert_number_to_month,
)


from .exceptions import (
    UteEnergyException,
    UteApiAccessDenied,
    UteApiUnauthorized,
)

from .const import (
    ACCOUNT_SERVICE_POINT_ID,
    ACTIVE_CONSUMPTION,
    AGREEMENT_INFO,
    BASE_ACCOUNTS,
    BASE_URL,
    CONSUMPTION_ATTR,
    CONTRACTED_TARIFF,
    CONTRACTED_VOLTAGE,
    CONTRACTED_POWER_ON_PEAK,
    CONTRACTED_POWER_ON_VALLEY,
    CONTRACTED_POWER_ON_FLAT,
    CURRENT_CONSUMPTION,
    CURRENT_ENERGY_CONSUMPTION,
    CURRENT_POWER,
    CURRENT_VOLTAGE,
    DATA,
    ENDPOINTS,
    HEADERS,
    ID,
    INVOICES,
    INVOICE_INFO,
    MISC_BEHAVIOUR,
    LATEST_INVOICE,
    LAST_READING,
    METER_PEAK,
    MONTH,
    MONTH_CHARGES,
    MONTH_CONSUMPTION,
    PEAK_INFO,
    SELECTED_PEAK,
    PHONE_LENGHT,
    PHONE_START_WIHT,
    READINGS,
    READING_REQUEST,
    REQUEST_CODE,
    REQUEST_CONSUMPTION,
    REQUEST_TOKEN,
    RESPONSE_STATUS,
    SINGLE_SERIE,
    SERVICE_AGREEMENT_ID,
    TOKEN_TYPE,
    SYNC_INTERVAL,
    VALIDATE_CODE,
    VALOR,
    VALUE,
    YEAR,
)

_LOGGER = logging.getLogger(__name__)


class UteEnergy:
    """Main class to perform UTE API requests."""

    def __init__(self, email: str, phone: str) -> None:
        """Initialize."""
        self.email = email
        self.phone = phone
        self.service_token = None
        self.session = None

        self.failed_logins = 0

        self.agent_id = generate_random_agent_id()
        self.useragent = (
            "Android-7.1.1-1.0.0-ONEPLUS A3010-136-"
            + self.agent_id
            + " APP/xiaomi.smarthome APPV/62830"
        )
        if not self._check_credentials():
            raise UteEnergyException("email or phone can't be empty")

        self.client_id = generate_random_string(6)

    def login(self) -> bool:
        """Login in to Ute API.

        :return: True if login successful, False otherwise.
        """
        if not self._check_credentials():
            return False

        if self.email and self.service_token:
            return True

        self._init_session()

        url = BASE_URL + ENDPOINTS[REQUEST_TOKEN]
        payload: dict[str, str] = {"Email": self.email, "PhoneNumber": self.phone}

        response = self._call_ute_api("POST", url, "Login", payload)

        service_token = response.text

        if service_token:
            self.service_token = service_token
            self.session.headers.update(
                {"Authorization": f"{TOKEN_TYPE} {self.service_token}"}
            )
            return True
        return False

    def _check_credentials(self) -> bool:
        """Return True if user data are valid."""
        if (
            isinstance(self.email, str)
            and isinstance(self.phone, str)
            and len(self.phone) == PHONE_LENGHT
            and self.phone.startswith(PHONE_START_WIHT)
        ):
            return True
        return False

    def _init_session(self, reset=False):
        """Initilize session object."""
        if not self.session or reset:
            self.session = requests.Session()
            self.session.verify = False
            self.session.headers.update(HEADERS)

    def request_auth_code(self) -> None:
        """Retrieve auth code from UTE API."""

        url = BASE_URL + ENDPOINTS[REQUEST_CODE]

        payload: dict[str, str] = {
            "UserId": 0,
            "Name": self.email,
            "Email": self.email,
            "PhoneNumber": self.phone,
            "IsValidated": False,
            "IsBanned": False,
            "UniqueId": None,
        }

        return self._call_ute_api("POST", url, "Request auth code", payload)

    def validate_auth_code(self, code: str) -> bool:
        """Validate authentication code"""

        url = BASE_URL + ENDPOINTS[VALIDATE_CODE]

        payload: dict[str, str] = {"ValidationCode": code}

        response = self._call_ute_api(
            "POST", url, "Validate authentication code", payload
        )

        return response[RESPONSE_STATUS]

    def request_accounts(self) -> Any:
        """Request all user account services"""
        url = BASE_URL + ENDPOINTS[BASE_ACCOUNTS]
        content = self._call_ute_api("GET", url, "Request accounts")
        return content[DATA]

    def retrieve_service_account_data(self, account_id: str) -> dict[str, Any]:
        """Retrieve service account data."""
        data = self._retrieve_service_agreement(account_id)
        if self._is_tariff_peak_available(account_id):
            data.update(self._retrieve_peak_time(account_id))
        data.update(self._retrieve_latest_invoice_info(account_id))
        data.update(self._retrieve_latest_month_consumption_info(account_id))
        if self._is_remote_reading_available(account_id):
            data.update(self._retrieve_latest_reading_info(account_id))
        return data

    def _retrieve_service_agreement(self, account_id: str) -> dict[str, Any]:
        """Retrieve agreement and meter info from UTE API"""
        url = f"{BASE_URL}{ENDPOINTS[BASE_ACCOUNTS]}/{account_id}"

        data: dict[str, Any] = {}
        content = self._call_ute_api("GET", url, "Retrieve service agreement")
        agreement_info = content[DATA][AGREEMENT_INFO]
        data.update(
            {
                SERVICE_AGREEMENT_ID: agreement_info[SERVICE_AGREEMENT_ID],
                CONTRACTED_TARIFF: agreement_info[CONTRACTED_TARIFF],
                CONTRACTED_VOLTAGE: agreement_info[CONTRACTED_VOLTAGE],
                CONTRACTED_POWER_ON_PEAK: agreement_info[CONTRACTED_POWER_ON_PEAK],
                CONTRACTED_POWER_ON_VALLEY: agreement_info[CONTRACTED_POWER_ON_VALLEY],
                CONTRACTED_POWER_ON_FLAT: agreement_info[CONTRACTED_POWER_ON_FLAT],
            }
        )

        return data

    def _retrieve_peak_time(self, account_id: str) -> dict[str, str] | None:
        """Retrieve account and meter info from UTE API"""
        data: dict[str, str] = {}

        path = ENDPOINTS[PEAK_INFO].format(account_id)

        url = f"{BASE_URL}{path}"

        content = self._call_ute_api("GET", url, "Retrieve peak time")

        peak_time = SELECTED_PEAK or METER_PEAK

        data.update({peak_time: content[DATA][peak_time]})
        return data

    def _is_tariff_peak_available(self, account_id: str) -> bool:
        """Retrieve peak tariff availability"""
        url = f"{BASE_URL}{ENDPOINTS[MISC_BEHAVIOUR]}"

        payload: dict[str, str] = {
            "Name": "IsTariffPeakSelectionAvailable",
            "Value": None,
            ACCOUNT_SERVICE_POINT_ID: account_id,
        }

        content = self._call_ute_api(
            "POST", url, "Verify tariff peak selection available", payload
        )
        return content[RESPONSE_STATUS]

    def _retrieve_latest_invoice_info(self, account_id: str) -> dict[str, str]:
        """Retrieve latest invoice info"""
        path = ENDPOINTS[INVOICE_INFO].format(account_id)
        url = f"{BASE_URL}/{path}"

        data: dict[str, Any] = {}
        content = self._call_ute_api("GET", url, "Retrieve latest invoice info")

        if content[RESPONSE_STATUS]:
            invoices = content[DATA][INVOICES]
            latest_invoice = self._extract_latest_invoice_info(invoices)
            _month = convert_number_to_month(latest_invoice[MONTH])
            data.update(
                {
                    LATEST_INVOICE: f"{_month} {latest_invoice[YEAR]}",
                    MONTH_CHARGES: latest_invoice[MONTH_CHARGES],
                }
            )
        return data

    def _extract_latest_invoice_info(
        self, invoices: list[dict[str, Any]]
    ) -> dict[str, str]:
        """Extract last invoice info"""
        today = datetime.datetime.today()

        last_invoice = max(
            invoices,
            key=lambda x: (x[YEAR], x[MONTH]) <= (today.year, today.month),
        )
        return last_invoice

    def _retrieve_latest_month_consumption_info(
        self, account_id: str
    ) -> dict[str, Any]:
        """Retrieve latest month consumption info"""
        path = ENDPOINTS[REQUEST_CONSUMPTION].format(account_id)
        url = f"{BASE_URL}/{path}"

        data: dict[str, Any] = {}
        content = self._call_ute_api("GET", url, "Retrieve latest consumption")

        if content[RESPONSE_STATUS]:
            active_consumption = content[DATA][0][ACTIVE_CONSUMPTION][SINGLE_SERIE]
            latest_consumption = self._extract_latest_consumption_info(
                active_consumption
            )
            data.update({MONTH_CONSUMPTION: latest_consumption[VALUE]})
        return data

    def _is_remote_reading_available(self, account_id: str) -> bool:
        """Send reading request to UTE API"""
        url = f"{BASE_URL}{ENDPOINTS[READING_REQUEST]}"
        payload: dict[str, str] = {ACCOUNT_SERVICE_POINT_ID: account_id}

        content = self._call_ute_api("POST", url, "Send reading request", payload)
        return content[RESPONSE_STATUS]

    def _retrieve_latest_reading_info(self, account_id: str) -> dict[str, str]:
        """Send reading request to UTE API"""
        path = ENDPOINTS[LAST_READING].format(account_id)
        url = f"{BASE_URL}/{path}"

        data: dict[str, Any] = {}
        reading_in_process = True
        count = 1
        while reading_in_process:
            content = self._call_ute_api("GET", url, "Retrieve latest reading info")
            if content[RESPONSE_STATUS]:
                reading_in_process = False
                latest_reading = content[DATA][READINGS]

                for status in latest_reading:
                    data[status[CONSUMPTION_ATTR]] = status[VALOR]

                current_power = float(data[CURRENT_VOLTAGE]) * float(
                    data[CURRENT_CONSUMPTION]
                )
                data.update({CURRENT_POWER: current_power})
                current_energy = (current_power * (SYNC_INTERVAL / 60)) / 1000
                data.update({CURRENT_ENERGY_CONSUMPTION: current_energy})
            if count == 40:
                count = 0
                reading_in_process = False
                continue

            count += 1
            _LOGGER.debug(
                "Waiting 2000 ms to avoid to many requests, account: %s, request: #%s",
                account_id,
                count,
            )
            time.sleep(3)
            continue
        return data

    def _extract_latest_consumption_info(
        self, active_consumption: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Extract latest month consumption info."""
        latest_consumption: dict[str, Any] = {VALUE: 0}

        active_consumption_filtered = list(
            filter(lambda x: x[ID] > 0, active_consumption)
        )
        if (
            len(active_consumption_filtered) > 0
            and active_consumption[0][MONTH_CONSUMPTION] == 0
        ):
            latest_consumption = active_consumption_filtered[-1]
        else:
            latest_consumption = max(
                active_consumption, key=lambda x: x[MONTH_CONSUMPTION]
            )
        return latest_consumption

    def _call_ute_api(self, method, url, action, payload=None) -> dict[str, Any]:
        """Execute request to UTE API."""
        try:
            json_data = json.dumps(payload) if payload is not None else None
            response = self.session.request(method, url, data=json_data)

            if response.status_code == 200:
                if action == "Login":
                    return response
                _LOGGER.debug(
                    "%s return status: %s, content: %s",
                    action,
                    response.status_code,
                    response.json(),
                )
                return response.json()

            message = (
                f"{action} return status: {response.status_code}, reason: {response.reason}, content: {response.text}",
            )

            if response.status_code == 401:
                raise UteApiAccessDenied(message)

            if response.status_code == 403:
                raise UteApiUnauthorized(message)

            raise UteEnergyException(message)

        except (
            UteApiUnauthorized,
            UteApiAccessDenied,
            UteEnergyException,
        ) as error:
            _LOGGER.error(error.message)
            raise error

        except Exception as error:
            _LOGGER.error("%s failed: %s", action, error, exc_info=True)
            raise error
