"""The UTE Energy integration."""
from __future__ import annotations

import logging
import homeassistant.helpers.entity_registry as er

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntry

from .ute_energy import UteEnergy
from .coordinator import UteEnergyDataUpdateCoordinator

from .const import (
    ACCOUNT_ID,
    ACCOUNT_SERVICE_POINT_ID,
    CONNECTION,
    CONF_USER_EMAIL,
    CONF_USER_PHONE,
    DEFAULT_NAME,
    DOMAIN,
    ENTRY_NAME,
    ENTRY_COORDINATOR,
    UPDATE_LISTENER,
)

_LOGGER = logging.getLogger(__name__)

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
        ENTRY_NAME: DEFAULT_NAME,
        ACCOUNT_ID: account_id,
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


async def async_remove_config_entry_device(
    hass: HomeAssistant, config_entry: ConfigEntry, device_entry: DeviceEntry
) -> bool:
    """Remove a config entry from a device."""
    device_id = device_entry.id

    entity_registry = er.async_get(hass)

    entities = {
        entity.unique_id: entity.entity_id
        for entity in er.async_entries_for_config_entry(
            entity_registry, config_entry.entry_id
        )
        if device_id == entity.device_id
    }

    for entity_id in entities.values():
        entity_registry.async_remove(entity_id)

    if config_entry.data.get(CONNECTION, None) is None:
        _LOGGER.debug(
            "Device %s not found in config entry: finalizing device removal", device_id
        )
        return True

    _LOGGER.debug("Device %s removed", device_id)

    return True
