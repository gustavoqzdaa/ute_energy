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
from homeassistant.const import EntityCategory

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)

from homeassistant.const import (
    UnitOfPower,
    UnitOfEnergy,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
)
from .utils import extract_entity_id

from .const import (
    ACCOUNT_ID,
    ATTRIBUTION,
    CONTRACTED_TARIFF,
    CONTRACTED_POWER_ON_PEAK,
    CONTRACTED_POWER_ON_VALLEY,
    CONTRACTED_POWER_ON_FLAT,
    CONTRACTED_VOLTAGE,
    CURRENT_CONSUMPTION,
    CURRENT_POWER,
    CURRENT_STATUS,
    CURRENCY_UYU,
    CURRENT_VOLTAGE,
    DEFAULT_PRECISION,
    DOMAIN,
    DOUBLE_TARIFF,
    ENTRY_NAME,
    ENTRY_COORDINATOR,
    LATEST_INVOICE,
    MONTH_CHARGES,
    MONTH_CONSUMPTION,
    SELECTED_PEAK,
    SERVICE_AGREEMENT_ID,
    TRIPLE_TARIFF,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class UteEnergySensorDescription(SensorEntityDescription):
    """Class that holds service specific info for a Ute account."""

    attributes: tuple = ()
    parent_key: str | None = None


SENSOR_TYPES_REAL_TIME: tuple[UteEnergySensorDescription, ...] = (
    UteEnergySensorDescription(
        key=CURRENT_CONSUMPTION,
        name="Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=DEFAULT_PRECISION,
    ),
    UteEnergySensorDescription(
        key=CURRENT_VOLTAGE,
        name="Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=DEFAULT_PRECISION,
    ),
    UteEnergySensorDescription(
        key=CURRENT_POWER,
        name="Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=DEFAULT_PRECISION,
    ),
)

SENSOR_TYPES_TRD_TRT: tuple[UteEnergySensorDescription, ...] = (
    UteEnergySensorDescription(
        key=SELECTED_PEAK,
        name="Peak time",
        icon="mdi:timer-outline",
    ),
)

SENSOR_TYPES_TRT: tuple[UteEnergySensorDescription, ...] = (
    UteEnergySensorDescription(
        key=CONTRACTED_POWER_ON_FLAT,
        name="Contracted power on flat",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
    ),
    UteEnergySensorDescription(
        key=CONTRACTED_POWER_ON_VALLEY,
        name="Contracted power on valley",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
    ),
)


SENSOR_TYPES_COMMON: tuple[UteEnergySensorDescription, ...] = (
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
        key=CONTRACTED_POWER_ON_PEAK,
        name="Contracted power on peak",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
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
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
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
    account_id = domain_data[ACCOUNT_ID]
    coordinator = domain_data[ENTRY_COORDINATOR]

    tariff_plan = coordinator.data.get(CONTRACTED_TARIFF, None)

    entities: list[AbstractUteEnergySensor] = [
        UteEnergySensor(
            name,
            account_id,
            f"{config_entry.unique_id}_{account_id}_{description.key}",
            description,
            coordinator,
        )
        for description in SENSOR_TYPES_COMMON
    ]

    if tariff_plan in (DOUBLE_TARIFF, TRIPLE_TARIFF):
        entities.extend(
            [
                UteEnergySensor(
                    name,
                    account_id,
                    f"{config_entry.unique_id}_{account_id}_{description.key}",
                    description,
                    coordinator,
                )
                for description in SENSOR_TYPES_TRD_TRT
            ]
        )

    if tariff_plan == TRIPLE_TARIFF:
        entities.extend(
            [
                UteEnergySensor(
                    name,
                    account_id,
                    f"{config_entry.unique_id}_{account_id}_{description.key}",
                    description,
                    coordinator,
                )
                for description in SENSOR_TYPES_TRT
            ]
        )

    if coordinator.data.get(CURRENT_STATUS, None):
        entities.extend(
            [
                UteEnergySensor(
                    name,
                    account_id,
                    f"{config_entry.unique_id}_{account_id}_{description.key}",
                    description,
                    coordinator,
                )
                for description in SENSOR_TYPES_REAL_TIME
            ]
        )

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

        self._attr_name = f"{name} {description.name}"
        self._attr_unique_id = unique_id

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._coordinator.last_update_success

    @property
    def native_value(self) -> StateType:
        """Return the state of the device."""
        return self._coordinator.data.get(self.entity_description.key, None)

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
        account_id: str,
        unique_id: str,
        description: UteEnergySensorDescription,
        coordinator: UteEnergyDataUpdateCoordinator,
    ) -> None:
        """Initialize the sensor."""
        self.entity_id = extract_entity_id(name, account_id, description.name)
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
