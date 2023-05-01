"""Support for the UTE Energy service."""
from __future__ import annotations

import logging

from dataclasses import dataclass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.config_entries import ConfigEntry
from .coordinator import UteEnergyDataUpdateCoordinator
from .utils import convert_to_snake_case

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)

from homeassistant.const import UnitOfPower
from .const import (
    ATTRIBUTION,
    CONTRACTED_TARIFF,
    CONTRACTED_POWER_ON_PEAK,
    CONTRACTED_POWER_ON_VALLEY,
    CONTRACTED_POWER_ON_FLAT,
    CONTRACTED_VOLTAGE,
    CURRENCY_UYU,
    DOMAIN,
    ENTRY_NAME,
    ENTRY_COORDINATOR,
    LATEST_INVOICE,
    MONTH_CHARGES,
    MONTH_CONSUMPTION,
    PEAK_TIME,
    SERVICE_AGREEMENT_ID,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class UteEnergySensorDescription(SensorEntityDescription):
    """Class that holds service specific info for a Ute account."""

    attributes: tuple = ()
    parent_key: str | None = None


SENSOR_TYPES: tuple[UteEnergySensorDescription, ...] = (
    UteEnergySensorDescription(
        key=SERVICE_AGREEMENT_ID,
        name="Agreement",
        icon="mdi:identifier",
    ),
    UteEnergySensorDescription(
        key=CONTRACTED_TARIFF,
        name="Contracted tarrif",
    ),
    UteEnergySensorDescription(
        key=CONTRACTED_VOLTAGE,
        name="Contracted voltage",
        icon="mdi:sine-wave",
    ),
    UteEnergySensorDescription(
        key=CONTRACTED_POWER_ON_FLAT,
        name="Contracted power on flat",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        entity_registry_enabled_default=False,
    ),
    UteEnergySensorDescription(
        key=CONTRACTED_POWER_ON_VALLEY,
        name="Contracted power on valley",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        entity_registry_enabled_default=False,
    ),
    UteEnergySensorDescription(
        key=CONTRACTED_POWER_ON_PEAK,
        name="Contracted power on peak",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
    ),
    UteEnergySensorDescription(
        key=PEAK_TIME,
        name="Peak time",
        icon="mdi:timer-outline",
        entity_registry_enabled_default=False,
    ),
    UteEnergySensorDescription(
        key=LATEST_INVOICE,
        name="Latest month invoice",
        icon="mdi:calendar-month",
    ),
    UteEnergySensorDescription(
        key=MONTH_CHARGES,
        name="Latest month charges",
        native_unit_of_measurement=CURRENCY_UYU,
        device_class=SensorDeviceClass.MONETARY,
    ),
    UteEnergySensorDescription(
        key=MONTH_CONSUMPTION,
        name="Latest month consumption",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
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
    entities: list[AbstractUteEnergySensor] = [
        UteEnergySensor(
            name,
            f"{config_entry.unique_id}_{description.key}",
            description,
            coordinator,
        )
        for description in SENSOR_TYPES
    ]

    async_add_entities(entities)


class AbstractUteEnergySensor(SensorEntity):
    """Abstract class for a Ute Energy sensor."""

    _attr_should_poll = False
    _attr_attribution = ATTRIBUTION

    def __init__(
        self,
        name: str,
        unique_id: str,
        description: UteEnergySensorDescription,
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


class UteEnergySensor(AbstractUteEnergySensor):
    """Implementation of a Ute Energy sensor."""

    def __init__(
        self,
        name: str,
        unique_id: str,
        description: UteEnergySensorDescription,
        coordinator: UteEnergyDataUpdateCoordinator,
    ) -> None:
        """Initialize the sensor."""
        self.entity_id = f"sensor.{convert_to_snake_case(description.name)}_{name}"
        super().__init__(name, unique_id, description, coordinator)
        self._coordinator = coordinator

    @property
    def native_value(self) -> StateType:
        """Return the state of the device."""
        return self._coordinator.data.get(self.entity_description.key, None)

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return self._coordinator.device_info
