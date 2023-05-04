"""The UTE Energy integration."""
from __future__ import annotations
from datetime import timedelta

import logging
import aiohttp
from typing import Any
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .ute_energy import UteEnergy
from .coordinator import UteEnergyDataUpdateCoordinator

from .const import (
    DOMAIN,
    CONNECTION,
    CONF_USER_EMAIL,
    CONF_USER_PHONE,
    ACCOUNT_SERVICE_POINT_ID,
    ENTRY_NAME,
    ENTRY_COORDINATOR,
    UPDATE_LISTENER,
)

_LOGGER = logging.getLogger(__name__)

# TODO List the platforms that you want to support.
# For your initial PR, limit it to 1 platform.
PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up UTE Energy from a config entry."""
    email = entry.data[CONNECTION][CONF_USER_EMAIL]
    phone = entry.data[CONNECTION][CONF_USER_PHONE]
    account_id = entry.data[ENTRY_NAME]
    account_service_point_id = entry.data[CONNECTION][ACCOUNT_SERVICE_POINT_ID]

    ute_api = UteEnergy(email, phone)

    coordinator = UteEnergyDataUpdateCoordinator(
        hass, ute_api, entry.entry_id, account_service_point_id
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})

    hass.data[DOMAIN][entry.entry_id] = {
        ENTRY_NAME: account_id,
        ENTRY_COORDINATOR: coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    update_listener = entry.add_update_listener(async_update_options)
    hass.data[DOMAIN][entry.entry_id][UPDATE_LISTENER] = update_listener
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options."""
    await hass.config_entries.async_reload(entry.entry_id)
