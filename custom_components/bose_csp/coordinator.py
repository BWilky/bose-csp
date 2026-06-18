"""DataUpdateCoordinator for the Bose CSP integration."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from pybosecsp import BoseCSPConnectionError, BoseCSPDevice, ZoneState

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


@dataclass
class BoseCSPData:
    """Runtime data for the Bose CSP integration."""

    device: BoseCSPDevice
    coordinator: BoseCSPCoordinator
    source_list: list[str]
    min_db: float
    max_db: float


type BoseCSPConfigEntry = ConfigEntry[BoseCSPData]


class BoseCSPCoordinator(DataUpdateCoordinator[dict[str, ZoneState]]):
    """Coordinator for Bose CSP push-based updates."""

    config_entry: BoseCSPConfigEntry

    def __init__(self, hass: HomeAssistant, device: BoseCSPDevice) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
        )
        self.device = device

    async def _async_setup(self) -> None:
        """Set up the coordinator: connect and subscribe to push updates."""
        try:
            await self.device.connect()
        except BoseCSPConnectionError as err:
            raise UpdateFailed(
                "Failed to connect to Bose CSP at %s" % self.device.host
            ) from err
        self.device.subscribe_updates(self._handle_device_update)
        self.device.subscribe_availability(self._handle_availability_update)

    @callback
    def _handle_device_update(self, zone_name: str) -> None:
        """Handle a push update from the device."""
        _LOGGER.debug("Push update received for zone: %s", zone_name)
        self.async_set_updated_data(self.device.get_all_states())

    @callback
    def _handle_availability_update(self, is_available: bool) -> None:
        """Handle an availability change from the device."""
        _LOGGER.debug("Availability update: %s", is_available)
        if is_available:
            self.async_set_updated_data(self.device.get_all_states())
        else:
            self.last_update_success = False
            self.async_update_listeners()

    async def _async_update_data(self) -> dict[str, ZoneState]:
        """Fetch the latest data from the device (fallback poll)."""
        return self.device.get_all_states()

    async def async_shutdown(self) -> None:
        """Shut down the coordinator and disconnect device."""
        self.device.unsubscribe_updates(self._handle_device_update)
        self.device.unsubscribe_availability(self._handle_availability_update)
        await super().async_shutdown()
