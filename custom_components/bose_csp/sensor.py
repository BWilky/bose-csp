"""Sensor platform for Bose CSP (health-check status)."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import BoseCSPConfigEntry
from .entity import BoseCSPEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BoseCSPConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Bose CSP health-check sensor from a config entry."""
    async_add_entities([BoseCSPHealthSensor(entry.runtime_data.coordinator)])


class BoseCSPHealthSensor(BoseCSPEntity, SensorEntity):
    """Reports the active control-verify "Health Checking" status."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator) -> None:
        """Initialize the health sensor (one per device)."""
        super().__init__(coordinator, "health")
        self._attr_unique_id = f"{coordinator.device.host}-health"
        self._attr_name = "Health Checking"

    @property
    def available(self) -> bool:
        """Always available so it can report the disconnected status itself."""
        return True

    @property
    def native_value(self) -> str:
        """Return the current health-check status string."""
        return self.coordinator.health_status or "disabled"

    @property
    def extra_state_attributes(self) -> dict[str, str | None]:
        """Expose the probe zone for visibility."""
        return {"health_zone": self.coordinator.device.health_zone}
