"""Base entity for the Bose CSP integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import BoseCSPCoordinator


class BoseCSPEntity(CoordinatorEntity[BoseCSPCoordinator]):
    """Base class for Bose CSP entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: BoseCSPCoordinator,
        zone_name: str,
    ) -> None:
        """Initialize the base entity."""
        super().__init__(coordinator)
        self._zone_name = zone_name
        self._attr_unique_id = f"{coordinator.device.host}-{zone_name}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.device.host)},
            name="Bose CSP",
            manufacturer="Bose Professional",
            model="CSP Processor",
            configuration_url=f"http://{coordinator.device.host}",
        )
