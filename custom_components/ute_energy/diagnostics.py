"""Diagnostics support for AccuWeather."""
from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry

# from homeassistant.const import CONF_API_KEY, CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.core import HomeAssistant

from .coordinator import UteEnergyDataUpdateCoordinator
from .const import (
    DOMAIN,
    CONF_USER_EMAIL,
    CONF_USER_PHONE,
    ACCOUNT_SERVICE_POINT_ID,
)

TO_REDACT = {
    CONF_USER_EMAIL,
    CONF_USER_EMAIL,
    CONF_USER_PHONE,
    ACCOUNT_SERVICE_POINT_ID,
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, config_entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    diagnostics_data: dict[str, Any] = {
        "config_entry": async_redact_data(config_entry.as_dict(), TO_REDACT)
    }

    # diagnostics_data = {
    #     "config_entry_data": async_redact_data(dict(config_entry.data), TO_REDACT),
    #     "coordinator_data": coordinator.data,
    # }

    # not every device uses DataUpdateCoordinator
    if coordinator := hass.data[DOMAIN][config_entry.entry_id]:
        if isinstance(coordinator, dict):
            diagnostics_data["coordinator_data"] = coordinator
        else:
            diagnostics_data["coordinator_data"] = repr(coordinator)

    return diagnostics_data
