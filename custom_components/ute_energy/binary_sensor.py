"""Support for the UTE Energy service."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.typing import StateType
from homeassistant.core import HomeAssistant
from homeassistant.const import EntityCategory

from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .coordinator import UteEnergyDataUpdateCoordinator
from .utils import convert_to_snake_case

from .const import (
    ATTRIBUTION,
    CURRENT_STATUS,
    DOMAIN,
    ENTRY_COORDINATOR,
    ENTRY_NAME,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class UteEnergyBinarySensorDescription(BinarySensorEntityDescription):
    """A class that describes binary sensor entities."""

    value: Callable | None = None
    parent_key: str | None = None


BINARY_SENSOR_TYPES: tuple[UteEnergyBinarySensorDescription, ...] = (
    UteEnergyBinarySensorDescription(
        key=CURRENT_STATUS,
        name="Power Meter",
        icon="mdi:meter-electric",
        device_class=BinarySensorDeviceClass.POWER,
        value=lambda value: not value,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up UTE Energy sensor entities based on a config entry."""
    domain_data = hass.data[DOMAIN][config_entry.entry_id]
    name = domain_data[ENTRY_NAME]
    coordinator = domain_data[ENTRY_COORDINATOR]

    entities: list[AbstractUteEnergyBinarySensor] = [
        UteEnergyBinarySensor(
            name,
            f"{config_entry.unique_id}_{description.key}",
            description,
            coordinator,
        )
        for description in BINARY_SENSOR_TYPES
    ]

    async_add_entities(entities)


class AbstractUteEnergyBinarySensor(BinarySensorEntity):
    """Abstract class for a Ute Energy sensor."""

    _attr_should_poll = False
    _attr_attribution = ATTRIBUTION

    def __init__(
        self,
        name: str,
        unique_id: str,
        description: UteEnergyBinarySensorDescription,
        coordinator: DataUpdateCoordinator,
    ) -> None:
        """Initialize the sensor."""
        self.entity_description = description
        self._coordinator = coordinator

        self._attr_name = description.name
        self._attr_unique_id = unique_id
        self._attr_state = name

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._coordinator.last_update_success

    async def async_added_to_hass(self) -> None:
        """Connect to dispatcher listening for entity data notifications."""
        self.async_on_remove(
            self._coordinator.async_add_listener(self.async_write_ha_state)
        )

    async def async_update(self) -> None:
        """Get the latest data from Ute API and updates the states."""
        await self._coordinator.async_request_refresh()


class UteEnergyBinarySensor(AbstractUteEnergyBinarySensor):
    """Implementation of a Ute Energy sensor."""

    def __init__(
        self,
        name: str,
        unique_id: str,
        description: UteEnergyBinarySensorDescription,
        coordinator: UteEnergyDataUpdateCoordinator,
    ) -> None:
        """Initialize the sensor."""
        self.entity_id = f"sensor.{convert_to_snake_case(description.name)}_{name}"
        super().__init__(name, unique_id, description, coordinator)
        self._coordinator = coordinator
        self._attr_is_on = self.native_value

    @property
    def native_value(self) -> StateType:
        """Return the state of the device."""
        return self._coordinator.data.get(self.entity_description.key, None)

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return self._coordinator.device_info
