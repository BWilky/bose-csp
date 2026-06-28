"""Switch platform for Bose CSP (per-zone AutoVolume)."""

from __future__ import annotations

import logging
from typing import Any

from pybosecsp import BoseCSPCommandError

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import BoseCSPConfigEntry
from .entity import BoseCSPEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BoseCSPConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Bose CSP AutoVolume switches from a config entry."""
    coordinator = entry.runtime_data.coordinator

    zones_str = entry.data["zones"]
    zones_list = [zone.strip() for zone in zones_str.split(",")]

    async_add_entities(
        BoseCSPAutoVolumeSwitch(coordinator, zone_name) for zone_name in zones_list
    )


class BoseCSPAutoVolumeSwitch(BoseCSPEntity, SwitchEntity):
    """AutoVolume on/off switch for a single Bose CSP zone."""

    def __init__(self, coordinator, zone_name: str) -> None:
        """Initialize the AutoVolume switch."""
        super().__init__(coordinator, zone_name)
        # The base entity uses "{host}-{zone}", which the media player already
        # owns; add a suffix so this switch gets a distinct unique_id.
        self._attr_unique_id = f"{coordinator.device.host}-{zone_name}-autovolume"
        self._attr_name = f"{zone_name} AutoVolume"
        self._update_state()

    def _update_state(self) -> None:
        """Read AutoVolume state for this zone from coordinator data."""
        data = self.coordinator.data
        zone_state = data.get(self._zone_name) if data else None
        self._attr_is_on = bool(zone_state.auto_volume) if zone_state else False

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._update_state()
        super()._handle_coordinator_update()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn AutoVolume on for this zone."""
        await self._set_auto_volume(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn AutoVolume off for this zone."""
        await self._set_auto_volume(False)

    async def _set_auto_volume(self, enabled: bool) -> None:
        try:
            await self.coordinator.device.set_auto_volume(self._zone_name, enabled)
        except BoseCSPCommandError as err:
            _LOGGER.error(
                "Failed to set AutoVolume for %s: %s", self._zone_name, err
            )
