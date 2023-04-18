"""Perform UTE API requests"""
from __future__ import annotations

import logging
import json
import requests

from typing import Any
from .utils import generate_random_string, generate_random_agent_id


from .exceptions import (
    UteEnergyException,
    UteApiAccessDenied,
)

from .const import (
    PHONE_LENGHT,
    PHONE_START_WIHT,
    HEADERS,
    ENDPOINTS,
    BASE_URL,
    REQUEST_TOKEN,
    REQUEST_CODE,
    VALIDATE_CODE,
    TOKEN_TYPE,
    BASE_ACCOUNTS,
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
        if code == "0000":
            return True

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

    def retrieve_service_agreement(self, account_id: str) -> dict[str, Any]:
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
                content = response.json()
                _LOGGER.debug("agreementInfo and meterInfo: %s", content)
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

        return {}
