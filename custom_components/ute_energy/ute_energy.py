"""Perform UTE API requests"""
from __future__ import annotations

import logging
import json
import requests
import datetime

from typing import Any
from .utils import (
    generate_random_string,
    generate_random_agent_id,
    convert_number_to_month,
)


from .exceptions import (
    UteEnergyException,
    UteApiAccessDenied,
)

from .const import (
    ACTIVE_CONSUMPTION,
    AGREEMENT_INFO,
    BASE_ACCOUNTS,
    BASE_URL,
    CONTRACTED_TARIFF,
    CONTRACTED_VOLTAGE,
    CONTRACTED_POWER_ON_PEAK,
    CONTRACTED_POWER_ON_VALLEY,
    CONTRACTED_POWER_ON_FLAT,
    DATA,
    ENDPOINTS,
    HEADERS,
    INVOICES,
    INVOICE_INFO,
    MISC_BEHAVIOUR,
    LATEST_INVOICE,
    MONTH,
    MONTH_CHARGES,
    MONTH_CONSUMPTION,
    PEAK_INFO,
    PEAK_TIME,
    PHONE_LENGHT,
    PHONE_START_WIHT,
    SINGLE_SERIE,
    SERVICE_AGREEMENT_ID,
    TOKEN_TYPE,
    REQUEST_CODE,
    REQUEST_CONSUMPTION,
    REQUEST_TOKEN,
    RESPONSE_STATUS,
    VALIDATE_CODE,
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

    def login(self) -> bool:
        """Login in to Ute API.

        :return: True if login successful, False otherwise.
        """
        if not self._check_credentials():
            return False

        if self.email and self.service_token:
            return True

        _LOGGER.debug("UTE logging in with email %s and %s", self.email, self.phone)

        try:
            if self._login_request():
                self.failed_logins = 0
            else:
                self.failed_logins += 1
                _LOGGER.debug("Ute API login attempt %s", self.failed_logins)
        except UteEnergyException as error:
            _LOGGER.info(
                "Error logging on to Ute API (%s): %s",
                self.failed_logins,
                str(error),
            )
            self.failed_logins += 1
            self.service_token = None
            if self.failed_logins > 10:
                _LOGGER.info(
                    "Repeated errors logging on to Ute API. Cleaning stored cookies"
                )
                self._init_session(reset=True)
            return False
        except UteApiAccessDenied as error:
            logging.info(
                "Access denied when logging  on to Ute API. (%s): %s",
                self.failed_logins,
                str(error),
            )
            self.failed_logins += 1
            self.service_token = None
            if self.failed_logins > 10:
                logging.info(
                    "Repeated errors logging  on to Ute API. Cleaning stored cookies"
                )
                self._init_session(reset=True)
            raise error
        except:  # pylint: disable=bare-except
            _LOGGER.exception("Unknown exception occurred!")
            return False

        return True

    def _login_request(self) -> bool:
        try:
            self._init_session()

            url = BASE_URL + ENDPOINTS[REQUEST_TOKEN]
            payload: dict[str, str] = {"Email": self.email, "PhoneNumber": self.phone}

            response = self.session.post(url, data=json.dumps(payload))

            if response.status_code == 403:
                raise UteApiAccessDenied(
                    "Access denied. Did you set the correct api key and/or username?"
                )
            if response.status_code == 200:
                _LOGGER.debug("Response: %s", response.text)
                service_token = response.text

                if service_token:
                    self.service_token = service_token
                    self.session.headers.update(
                        {"Authorization": f"{TOKEN_TYPE} {self.service_token}"}
                    )
                    _LOGGER.debug("Headers: %s ", self.session.headers)
                    _LOGGER.debug("Your service token: %s", self.service_token)

                return True
            _LOGGER.debug(
                "request returned status '%s', reason: %s, content: %s",
                response.status_code,
                response.reason,
                response.text,
            )
            raise UteEnergyException(str(response.status_code) + response.reason)
        except UteApiAccessDenied as error:
            raise error
        except Exception as error:
            raise error

    def _init_session(self, reset=False):
        if not self.session or reset:
            self.session = requests.Session()
            self.session.verify = False
            self.session.headers.update(HEADERS)

    def request_auth_code(self) -> Any:
        """Retrieve auth code from UTE API."""

        # token = await self.get_token_key()

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

        try:
            response = self.session.post(url, data=json.dumps(payload))

            if response.status_code == 403:
                raise UteApiAccessDenied(
                    "Access denied. Did you set the correct emal and/or phone?"
                )

            if response.status_code == 200:
                content = response.json()
                _LOGGER.debug("Auth code requested, response: %s", content)
                return content

            _LOGGER.debug(
                "request returned status '%s', reason: %s, content: %s",
                response.status_code,
                response.reason,
                response.text,
            )
            raise UteEnergyException(str(response.status_code) + response.reason)
        except UteApiAccessDenied as e:  # pylint: disable=invalid-name
            raise e
        except Exception as e:  # pylint: disable=invalid-name
            raise UteEnergyException("Cannot logging on to Ute API: " + str(e)) from e

    def validate_auth_code(self, code: str) -> bool:
        """Validate authentication code"""

        url = BASE_URL + ENDPOINTS[VALIDATE_CODE]

        payload: dict[str, str] = {"ValidationCode": code}

        try:
            response = self.session.post(url, data=json.dumps(payload))

            if response.status_code == 403:
                raise UteApiAccessDenied(
                    "Access denied. Did you set the correct api key and/or username?"
                )

            if response.status_code == 200:
                content = response.json()
                _LOGGER.debug("Auth code validated, response: %s", content)
                return True

            _LOGGER.debug(
                "request returned status '%s', reason: %s, content: %s",
                response.status_code,
                response.reason,
                response.text,
            )
            raise UteEnergyException(str(response.status_code) + response.reason)
        except UteApiAccessDenied as e:  # pylint: disable=invalid-name
            raise e
        except Exception as e:  # pylint: disable=invalid-name
            raise UteEnergyException("Cannot logon to Ute API: " + str(e)) from e

    def request_accounts(self) -> Any:
        """Request all user account services"""

        url = BASE_URL + ENDPOINTS[BASE_ACCOUNTS]

        try:
            response = self.session.get(url)

            if response.status_code == 403:
                raise UteApiAccessDenied(
                    "Access denied. Did you set the correct emal and/or phone?"
                )

            if response.status_code == 200:
                content = response.json()
                _LOGGER.debug("Accounts: %s", content)
                return content["data"]

            _LOGGER.debug(
                "request returned status '%s', reason: %s, content: %s",
                response.status_code,
                response.reason,
                response.text,
            )
            raise UteEnergyException(str(response.status_code) + response.reason)
        except UteApiAccessDenied as e:  # pylint: disable=invalid-name
            raise e
        except Exception as e:  # pylint: disable=invalid-name
            raise UteEnergyException("Cannot logging on to Ute API: " + str(e)) from e

    def retrieve_service_account_data(self, account_id: str) -> dict[str, Any]:
        """Retrieve service account data."""
        data: dict[str, Any] = self._retrieve_service_agreement(account_id)
        data.update(self._retrieve_peak_time(account_id))
        data.update(self._retrieve_latest_invoice_info(account_id))
        data.update(self._retrieve_latest_month_consumption_info(account_id))
        _LOGGER.debug("All service account data: %s", data)
        return data

    def _retrieve_service_agreement(self, account_id: str) -> dict[str, Any]:
        """Retrieve agreement and meter info from UTE API"""
        url = f"{BASE_URL}{ENDPOINTS[BASE_ACCOUNTS]}/{account_id}"
        _LOGGER.debug("URL: %s", url)
        try:
            response = self.session.get(url)

            if response.status_code == 403:
                raise UteApiAccessDenied(
                    "Access denied. Did you set the correct emal and/or phone?"
                )

            if response.status_code == 200:
                data: dict[str, Any] = {}
                content = response.json()
                _LOGGER.debug("agreementInfo and meterInfo: %s", content)
                agreement_info = content[DATA][AGREEMENT_INFO]
                data.update(
                    {
                        SERVICE_AGREEMENT_ID: agreement_info[SERVICE_AGREEMENT_ID],
                        CONTRACTED_TARIFF: agreement_info[CONTRACTED_TARIFF],
                        CONTRACTED_VOLTAGE: agreement_info[CONTRACTED_VOLTAGE],
                        CONTRACTED_POWER_ON_PEAK: agreement_info[
                            CONTRACTED_POWER_ON_PEAK
                        ],
                        CONTRACTED_POWER_ON_VALLEY: agreement_info[
                            CONTRACTED_POWER_ON_VALLEY
                        ],
                        CONTRACTED_POWER_ON_FLAT: agreement_info[
                            CONTRACTED_POWER_ON_FLAT
                        ],
                    }
                )

                _LOGGER.debug("agreement data: %s", data)

                return data

            _LOGGER.debug(
                "request returned status '%s', reason: %s, content: %s",
                response.status_code,
                response.reason,
                response.text,
            )
            raise UteEnergyException(str(response.status_code) + response.reason)
        except UteApiAccessDenied as e:  # pylint: disable=invalid-name
            raise e
        except Exception as e:  # pylint: disable=invalid-name
            raise UteEnergyException("Cannot logging on to Ute API: " + str(e)) from e

    def _retrieve_peak_time(self, account_id: str) -> dict[str, str] | None:
        """Retrieve account and meter info from UTE API"""
        data: dict[str, str] = {}

        if self._is_tariff_peak_unavailable(account_id):
            return data

        path = ENDPOINTS[PEAK_INFO].format(account_id)

        url = f"{BASE_URL}{path}"

        _LOGGER.debug("URL: %s", url)

        try:
            response = self.session.get(url)

            if response.status_code == 403:
                raise UteApiAccessDenied(
                    "Access denied. Did you set the correct emal and/or phone?"
                )

            if response.status_code == 200:
                data: dict[str, Any] = {}
                content = response.json()
                _LOGGER.debug("agreementInfo and meterInfo: %s", content)

                peack_info = content[DATA][PEAK_TIME]

                assert peack_info is not None

                data.update({PEAK_TIME: peack_info})

                _LOGGER.debug("Peak time: %s", data)

                return data

            _LOGGER.debug(
                "request returned status '%s', reason: %s, content: %s",
                response.status_code,
                response.reason,
                response.text,
            )
            raise UteEnergyException(str(response.status_code) + response.reason)
        except UteApiAccessDenied as e:  # pylint: disable=invalid-name
            raise e
        except Exception as e:  # pylint: disable=invalid-name
            raise UteEnergyException("Cannot logging on to Ute API: " + str(e)) from e

    def _is_tariff_peak_unavailable(self, account_id: str) -> bool:
        """Retrieve peak tariff availability"""
        url = f"{BASE_URL}{ENDPOINTS[MISC_BEHAVIOUR]}"

        payload: dict[str, str] = {
            "Name": "IsTariffPeakSelectionAvailable",
            "Value": None,
            "AccountServicePointId": account_id,
        }

        try:
            response = self.session.post(url, data=json.dumps(payload))
            if response.status_code == 403:
                raise UteApiAccessDenied(
                    "Access denied. Did you set the correct emal and/or phone?"
                )

            if response.status_code == 200:
                content = response.json()
                if content[RESPONSE_STATUS]:
                    return False
                return True

            _LOGGER.debug(
                "request returned status '%s', reason: %s, content: %s",
                response.status_code,
                response.reason,
                response.text,
            )
            raise UteEnergyException(str(response.status_code) + response.reason)
        except UteApiAccessDenied as e:  # pylint: disable=invalid-name
            raise e
        except Exception as e:  # pylint: disable=invalid-name
            raise UteEnergyException("Cannot logging on to Ute API: " + str(e)) from e

    def _retrieve_latest_invoice_info(self, account_id: str) -> dict[str, str]:
        """Retrieve latest invoice info"""
        path = ENDPOINTS[INVOICE_INFO].format(account_id)
        url = f"{BASE_URL}/{path}"

        try:
            response = self.session.get(url)

            if response.status_code == 403:
                raise UteApiAccessDenied(
                    "Access denied. Did you set the correct emal and/or phone?"
                )

            if response.status_code == 200:
                data: dict[str, Any] = {}
                content = response.json()

                if content[RESPONSE_STATUS]:
                    invoices = content[DATA][INVOICES]

                    _LOGGER.debug("invoices: %s", invoices)

                    latest_invoice = self._extract_latest_invoice_info(invoices)

                    _month = convert_number_to_month(latest_invoice[MONTH])

                    data.update(
                        {
                            LATEST_INVOICE: f"{_month} {latest_invoice[YEAR]}",
                            MONTH_CHARGES: latest_invoice[MONTH_CHARGES],
                        }
                    )
                    _LOGGER.debug("Last invoice info: %s", data)

                    return data

            _LOGGER.debug(
                "request returned status '%s', reason: %s, content: %s",
                response.status_code,
                response.reason,
                response.text,
            )
            raise UteEnergyException(str(response.status_code) + response.reason)
        except UteApiAccessDenied as e:  # pylint: disable=invalid-name
            raise e
        except Exception as e:  # pylint: disable=invalid-name
            raise UteEnergyException("Cannot logging on to Ute API: " + str(e)) from e

    def _extract_latest_invoice_info(
        self, invoices: list[dict[str, Any]]
    ) -> dict[str, str]:
        """Extract last invoice info"""
        today = datetime.datetime.today()

        last_invoice = max(
            invoices,
            key=lambda x: (x[YEAR], x[MONTH]) <= (today.year, today.month),
        )

        _LOGGER.debug("Last invoice: %s", last_invoice)

        return last_invoice

    def _retrieve_latest_month_consumption_info(
        self, account_id: str
    ) -> dict[str, Any]:
        """Retrieve latest month consumption info"""
        path = ENDPOINTS[REQUEST_CONSUMPTION].format(account_id)
        url = f"{BASE_URL}/{path}"

        try:
            response = self.session.get(url)
            if response.status_code == 403:
                raise UteApiAccessDenied(
                    "Access denied. Did you set the correct emal and/or phone?"
                )

            if response.status_code == 200:
                data: dict[str, Any] = {}
                content = response.json()
                if content[RESPONSE_STATUS]:
                    active_consumption = content[DATA][0][ACTIVE_CONSUMPTION][
                        SINGLE_SERIE
                    ]
                    _LOGGER.debug("Active consumption: %s", active_consumption)
                    latest_consumption = max(
                        active_consumption, key=lambda x: x[MONTH_CONSUMPTION]
                    )
                    data.update({MONTH_CONSUMPTION: latest_consumption[VALUE]})
                    _LOGGER.debug("Lastest consumption info: %s", latest_consumption)
                    return data
                return data

            _LOGGER.debug(
                "request returned status '%s', reason: %s, content: %s",
                response.status_code,
                response.reason,
                response.text,
            )
            raise UteEnergyException(str(response.status_code) + response.reason)
        except UteApiAccessDenied as e:  # pylint: disable=invalid-name
            raise e
        except Exception as e:  # pylint: disable=invalid-name
            raise UteEnergyException("Cannot logging on to Ute API: " + str(e)) from e
