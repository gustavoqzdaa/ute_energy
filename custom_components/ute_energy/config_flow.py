"""Config flow for UTE Energy integration."""
from __future__ import annotations

import logging
from typing import Any
import voluptuous as vol

from .exceptions import UteApiAccessDenied

from .ute_energy import UteEnergy

from homeassistant import config_entries
from homeassistant.config_entries import SOURCE_REAUTH, ConfigEntry
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.const import CONF_BASE

from .const import (
    DOMAIN,
    CONF_USER_ACCOUNTS,
    CONF_USER_EMAIL,
    CONF_USER_PHONE,
    CONF_AUTH_CODE,
    DEFAULT_USER_PHONE,
    ACCOUNT_SERVICE_POINT_ID,
    RESPONSE_RESULT,
    RESPONSE_STATUS,
    ACCOUNT_SERVICE_POINT_ADDRESS,
    AGREEMENT_INFO,
    ACCOUNT_ID,
)


_LOGGER = logging.getLogger(__name__)

# TODO adjust the data schema to the data that you need # pylint: disable=fixme
AUTH_CONFIG = vol.Schema(
    {
        vol.Required(CONF_USER_EMAIL): str,
        vol.Required(CONF_USER_PHONE, default=DEFAULT_USER_PHONE): str,
    }
)


VALIDATE_CODE = vol.Schema({vol.Required(CONF_AUTH_CODE): str})


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
        self.account: dict[str, Any] = {}
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
                errors[CONF_BASE] = "user_credentials_incomplete"
                return self.async_show_form(
                    step_id="auth", data_schema=AUTH_CONFIG, errors=errors
                )

            self.connection = UteEnergy(user_email, user_phone)
            try:
                if not await self.hass.async_add_executor_job(self.connection.login):
                    errors[CONF_BASE] = "invalid_auth"
            except UteApiAccessDenied:
                errors[CONF_BASE] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception in Ute API login")
                return self.async_abort(reason="unknown")

            if errors:
                return self.async_show_form(
                    step_id="auth", data_schema=AUTH_CONFIG, errors=errors
                )

            self.email = user_email
            self.phone = user_phone

            status_requested_code = await self.hass.async_add_executor_job(
                self.connection.request_auth_code
            )
            if status_requested_code.get(
                RESPONSE_RESULT, None
            ) == 1 and not status_requested_code.get(RESPONSE_STATUS, False):
                errors[CONF_BASE] = "invalid_auth"

                return self.async_show_form(
                    step_id="auth", data_schema=AUTH_CONFIG, errors=errors
                )

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
                    errors[CONF_BASE] = "user_no_accounts"
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

            self.account = self.extract_service_account_info(
                user_input["select_account"]
            )
            await self.async_set_unique_id(self.account[ACCOUNT_SERVICE_POINT_ID])
            self._abort_if_unique_id_configured()

            return await self.extract_service_data()

        select_schema = vol.Schema(
            {
                vol.Required("select_account"): vol.In(
                    self.sanitize_accounts(self.user_accounts)
                )
            }
        )

        return self.async_show_form(
            step_id="select", data_schema=select_schema, errors=errors
        )

    def sanitize_accounts(self, accounts: dict[str, dict[str, Any]]) -> list:
        """Extract info to display"""

        return [
            "{}: {}".format(key, accounts[key][ACCOUNT_SERVICE_POINT_ADDRESS])
            for key in accounts
        ]

    def extract_service_account_info(self, selected_account: str) -> dict[str, Any]:
        """Extract the account service info."""
        account_service_point_id = int(selected_account.split(":")[0].strip())

        _LOGGER.debug("Account: %s", selected_account)
        account = self.user_accounts[account_service_point_id]
        assert account is not None

        return account

    async def extract_service_data(self) -> dict[str, Any]:
        """Extract service data"""

        data: dict[str, Any] = {}
        agreement_meter_info = await self.hass.async_add_executor_job(
            self.connection.retrieve_service_agreement,
            self.account[ACCOUNT_SERVICE_POINT_ID],
        )
        assert agreement_meter_info[AGREEMENT_INFO] is not None

        data.update({AGREEMENT_INFO: agreement_meter_info[AGREEMENT_INFO]})

        return self.async_create_entry(
            title=self.account[ACCOUNT_ID],
            data=data,
        )


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
