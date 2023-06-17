"""Ute energy data coordinator for the UTE API."""

from datetime import timedelta
import logging
from typing import Any

import async_timeout

from homeassistant.core import HomeAssistant
from .ute_energy import UteEnergy
from .exceptions import UteApiUnauthorized, UteApiAccessDenied, UteEnergyException
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

# from homeassistant.util import dt

from .const import (
    DEFAULT_NAME,
    DOMAIN,
    MANUFACTURER,
    REQUEST_TIMEOUT,
    SOURCE_URL,
    SYNC_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(minutes=SYNC_INTERVAL)


class UteEnergyDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching UTE data API."""

    def __init__(
        self,
        hass: HomeAssistant,
        ute_api: UteEnergy,
        device_key: str,
        account_service_point_id: str,
    ) -> None:
        """Initialize coordinator."""
        self._ute_api = ute_api
        self._account_service_point_id = account_service_point_id
        self._device_key = device_key

        _LOGGER.debug("Data will be update every %s", UPDATE_INTERVAL)

        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=UPDATE_INTERVAL)

    async def _async_update_data(self) -> dict[str:Any]:
        """Update the data."""
        data = {}
        async with async_timeout.timeout(REQUEST_TIMEOUT):
            try:
                await self.hass.async_add_executor_job(self._ute_api.login)
                data = await self._service_account_data()
            except (
                UteApiUnauthorized,
                UteApiAccessDenied,
                UteEnergyException,
            ) as error:
                raise UpdateFailed(error) from error
        return data

    async def _service_account_data(self) -> dict[str, Any]:
        """Poll service account data from UTE API."""
        response = await self.hass.async_add_executor_job(
            self._ute_api.retrieve_service_account_data, self._account_service_point_id
        )
        return response

    @property
    def device_info(self) -> DeviceInfo:
        """Device info."""
        return DeviceInfo(
            model=DEFAULT_NAME,
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, self._device_key)},
            manufacturer=MANUFACTURER,
            name=DEFAULT_NAME,
            configuration_url=SOURCE_URL,
        )
