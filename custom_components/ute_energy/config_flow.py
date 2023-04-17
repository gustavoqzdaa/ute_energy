"""Config flow for UTE Energy integration."""
from __future__ import annotations

import logging
from typing import Any
from async_timeout import timeout
import voluptuous as vol

from .exceptions import UteApiAccessDenied

# import json

from .ute_energy import UteEnergy

# from .exceptions import InvalidRequestDataError, ApiError, UteApiAccessDenied

from homeassistant import config_entries
from homeassistant.config_entries import SOURCE_REAUTH, ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .const import (
    DOMAIN,
    BASE_URL,
    CONF_USER_ACCOUNTS,
    CONF_USER_EMAIL,
    CONF_USER_PHONE,
    CONF_AUTH_CODE,
    DEFAULT_USER_PHONE,
    ACCOUNT_SERVICE_POINT_ID,
)


_LOGGER = logging.getLogger(__name__)

# TODO adjust the data schema to the data that you need
AUTH_CONFIG = vol.Schema(
    {
        vol.Required(CONF_USER_EMAIL): str,
        vol.Required(CONF_USER_PHONE, default=DEFAULT_USER_PHONE): str,
    }
)

VALIDATE_CODE = vol.Schema({vol.Required(CONF_AUTH_CODE): str})


class PlaceholderHub:
    """Placeholder class to make tests pass.

    TODO Remove this placeholder class and replace with things from your PyPI package.
    """

    def __init__(self, hass: HomeAssistant, host: str) -> None:
        """Initialize."""
        self.hass = hass
        self.host = host

    async def authenticate(self, email: str, phone: str) -> str:
        """Test if we can authenticate with the host."""

        clientsession = async_create_clientsession(self.hass, verify_ssl=False)
        async with timeout(10):
            ute_energy = UteEnergy(email, phone, clientsession)
            code = await ute_energy.get_auth_code()

        return code


async def validate_input(data: dict[str, Any]) -> None:
    """Validate the user input allows us to connect.

    Data has the keys from step_user_data_schema with values provided by the user.
    """
    # TODO validate the data can be used to set up a connection.

    # If your PyPI package is not built with async, pass your methods
    # to the executor:
    # await hass.async_add_executor_job(
    #     your_validate_func, data["email"], data["phone"]
    # )


async def authenticate(hass: HomeAssistant, data: dict[str, Any]) -> str:
    """Retrieve token from UTE API"""
    hub = PlaceholderHub(hass, BASE_URL)

    code = await hub.authenticate(data["email"], data["phone"])

    # If you cannot connect:
    # throw CannotConnect
    # If the authentication is wrong:
    # InvalidAuth

    # Return info that you want to store in the config entry.
    # return {"title": "UTE Energy"}
    return code


async def validate_code(user_input: dict[str, Any]) -> bool:
    """Validate the authentication code."""
    _LOGGER.info("Message from validate code")
    return True


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a Ute Energy config flow."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize."""
        self.token = None
        self.email = None
        self.phone = None
        self.code = None
        self.connection = None
        self.user_accounts: dict[str, dict[str, Any]] = {}

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlowHandler:
        """Get the options flow."""
        return OptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""

        return await self.async_step_auth()

    async def async_step_auth(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Auth user on to Ute API."""

        errors: dict[str, str] = {}

        if user_input is not None:
            user_email = user_input.get(CONF_USER_EMAIL)
            user_phone = user_input.get(CONF_USER_PHONE)

            if not user_email or not user_phone:
                errors["base"] = "user_credentials_incomplete"
                return self.async_show_form(
                    step_id="auth", data_schema=AUTH_CONFIG, errors=errors
                )

            self.connection = UteEnergy(user_email, user_phone)
            try:
                if not await self.hass.async_add_executor_job(self.connection.login):
                    errors["base"] = "login_error"
            except UteApiAccessDenied:
                errors["base"] = "login_error"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception in Ute API login")
                return self.async_abort(reason="unknown")

            if errors:
                return self.async_show_form(
                    step_id="auth", data_schema=AUTH_CONFIG, errors=errors
                )

            self.email = user_email
            self.phone = user_phone

            await self.hass.async_add_executor_job(self.connection.request_auth_code)

            return await self.async_step_code()

        return self.async_show_form(
            step_id="auth", data_schema=AUTH_CONFIG, errors=errors
        )

    async def async_step_code(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Request and validate SMS code."""

        errors: dict[str, str] = {}

        accounts: dict[str, str] = {}

        if user_input is not None:
            is_validated = await self.hass.async_add_executor_job(
                self.connection.validate_auth_code, user_input[CONF_AUTH_CODE]
            )
            if is_validated:
                accounts = await self.hass.async_add_executor_job(
                    self.connection.request_accounts
                )

                if not accounts:
                    errors["base"] = "user_no_accounts"
                    return self.async_show_form(
                        step_id="code", data_schema=VALIDATE_CODE, errors=errors
                    )
                i = 0
                for account in accounts:
                    i += 1
                    _LOGGER.debug("Account #%s: %s", i, account)

                    service_id = account[ACCOUNT_SERVICE_POINT_ID]
                    self.user_accounts[service_id] = account
                _LOGGER.debug("User accounts: %s", self.user_accounts)

                # if len(self.user_accounts) == 1:
                #     self.extract_cloud_info(list(self.cloud_devices.values())[0])
                #     return await self.async_step_connect()

                return await self.async_step_select()

        return self.async_show_form(
            step_id="code", data_schema=VALIDATE_CODE, errors=errors
        )

    async def async_step_select(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle multiple account services found."""
        errors: dict[str, str] = {}
        if user_input is not None:
            _LOGGER.debug("Account selected: %s", user_input)
            account = self.user_accounts[user_input["select_account"]]
            self.extract_service_account_info(account)

        select_schema = vol.Schema(
            {vol.Required("select_account"): vol.In(list(self.user_accounts))}
        )

        return self.async_show_form(
            step_id="select", data_schema=select_schema, errors=errors
        )

    def extract_service_account_info(self, account: dict[str, Any]) -> None:
        """Extract the account service info."""
        _LOGGER.debug("message from extract_service_account_info")
        _LOGGER.debug("Account: %s", account)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Options for the component."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Init object."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""

        errors: dict[str, str] = {}
        if user_input is not None:
            user_account = user_input.get(CONF_USER_ACCOUNTS, False)

            if user_account and len(user_account) == 0:
                errors["base"] = "credentials_incomplete"
                # trigger re-auth flow
                self.hass.async_create_task(
                    self.hass.config_entries.flow.async_init(
                        DOMAIN,
                        context={"source": SOURCE_REAUTH},
                        data=self.config_entry.data,
                    )
                )

            if not errors:
                return self.async_create_entry(title="", data=user_input)

        settings_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_USER_ACCOUNTS,
                    default=self.config_entry.options.get(CONF_USER_ACCOUNTS, False),
                ): bool
            }
        )

        return self.async_show_form(
            step_id="init", data_schema=settings_schema, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
