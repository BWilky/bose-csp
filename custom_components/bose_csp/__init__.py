"""The Bose CSP integration."""

from __future__ import annotations

import logging

from pybosecsp import BoseCSPDevice

from homeassistant.const import CONF_HOST, Platform
from homeassistant.core import HomeAssistant

from .const import CONF_MAX_DB, CONF_MIN_DB, CONF_SOURCES, CONF_ZONES
from .coordinator import BoseCSPConfigEntry, BoseCSPCoordinator, BoseCSPData

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.MEDIA_PLAYER]


async def async_setup_entry(hass: HomeAssistant, entry: BoseCSPConfigEntry) -> bool:
    """Set up Bose CSP from a config entry."""
    host = entry.data[CONF_HOST]
    zones_str = entry.data[CONF_ZONES]
    zones_list = [zone.strip() for zone in zones_str.split(",")]

    sources_str = entry.data[CONF_SOURCES]
    source_list = [source.strip() for source in sources_str.split(",")]

    min_db: float = entry.data[CONF_MIN_DB]
    max_db: float = entry.data[CONF_MAX_DB]

    device = BoseCSPDevice(host, zones_list)

    coordinator = BoseCSPCoordinator(hass, device)

    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = BoseCSPData(
        device=device,
        coordinator=coordinator,
        source_list=source_list,
        min_db=min_db,
        max_db=max_db,
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: BoseCSPConfigEntry
) -> bool:
    """Unload a config entry."""
    if not await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        return False

    await entry.runtime_data.device.disconnect()

    return True