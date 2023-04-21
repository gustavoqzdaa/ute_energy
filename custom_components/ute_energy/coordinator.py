"""Ute energy data coordinator for the UTE API."""

from datetime import timedelta
import logging
from typing import Any

import async_timeout

from homeassistant.core import HomeAssistant
from .ute_energy import UteEnergy
from .exceptions import ApiError, UteApiAccessDenied, UteEnergyException
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

# from homeassistant.util import dt

from .const import (
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(minutes=10)


class UteEnergyDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching UTE data API."""

    def __init__(
        self,
        hass: HomeAssistant,
        ute_api: UteEnergy,
        account_service_point_id: str,
    ) -> None:
        """Initialize coordinator."""
        self._ute_api = ute_api
        self._account_service_point_id = account_service_point_id
        # self.device_info = DeviceInfo(
        #     entry_type=DeviceEntryType.SERVICE,
        #     identifiers={(DOMAIN, account_service_point_id)},
        #     name=name,
        #     configuration_url=(
        #         f"{BASE_URL}/{ENPOINTS[GET_ACCOUNTS]/{account_service_point_id}}"
        #     ),
        # )

        _LOGGER.debug("Data will be update every %s", UPDATE_INTERVAL)

        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=UPDATE_INTERVAL)

    async def _async_update_data(self) -> dict[str:Any]:
        """Update the data."""
        data = {}
        async with async_timeout.timeout(20):
            try:
                await self.hass.async_add_executor_job(self._ute_api.login)
                data = await self._service_account_data()
                # data = self._convert_weather_response(response)
            except (ApiError, UteApiAccessDenied, UteEnergyException) as error:
                raise UpdateFailed(error) from error
        _LOGGER.debug("Data from coordinator: %s", data)
        return data

    async def _service_account_data(self) -> dict[str, Any]:
        """Poll service account data from UTE API."""
        response = await self.hass.async_add_executor_job(
            self._ute_api.retrieve_service_account_data, self._account_service_point_id
        )
        return response
