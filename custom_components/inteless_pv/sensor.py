"""Sensor platform for Inteless PV."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(minutes=5)


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    """Set up Inteless PV sensors."""
    client = hass.data[DOMAIN][entry.entry_id]

    async def async_update_data():
        try:
            return await client.async_get_realtime()
        except Exception as err:
            raise UpdateFailed(f"Error fetching data: {err}") from err

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="inteless_pv",
        update_method=async_update_data,
        update_interval=SCAN_INTERVAL,
    )
    await coordinator.async_config_entry_first_refresh()

    async_add_entities([IntelessPVPowerSensor(coordinator)])


class IntelessPVPowerSensor(SensorEntity):
    """Representation of current power sensor."""

    def __init__(self, coordinator: DataUpdateCoordinator) -> None:
        self.coordinator = coordinator
        self._attr_name = "Inteless PV Power"
        self._attr_unique_id = "inteless_pv_power"

    @property
    def native_value(self) -> float | None:
        return self.coordinator.data.get("pac")

    @property
    def unit_of_measurement(self) -> str:
        return "kW"

    async def async_update(self) -> None:
        await self.coordinator.async_request_refresh()
