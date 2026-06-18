"""The Bose CSP integration."""

from __future__ import annotations

import asyncio
import logging

from pybosecsp import BoseCSPDevice

from homeassistant.const import CONF_HOST, Platform
from homeassistant.core import HomeAssistant

from .const import (
    CONF_MAX_DB,
    CONF_MIN_DB,
    CONF_OTHER_INTERVAL,
    CONF_RECONNECT_DELAY,
    CONF_SOURCES,
    CONF_VOLUME_INTERVAL,
    CONF_ZONES,
    DEFAULT_OTHER_INTERVAL,
    DEFAULT_RECONNECT_DELAY,
    DEFAULT_VOLUME_INTERVAL,
)
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

    # Parse options with defaults
    volume_interval = entry.options.get(CONF_VOLUME_INTERVAL, DEFAULT_VOLUME_INTERVAL)
    other_interval = entry.options.get(CONF_OTHER_INTERVAL, DEFAULT_OTHER_INTERVAL)
    reconnect_delay = entry.options.get(CONF_RECONNECT_DELAY, DEFAULT_RECONNECT_DELAY)

    device = BoseCSPDevice(
        host,
        zones_list,
        volume_interval=volume_interval,
        other_interval=other_interval,
        reconnect_delay=reconnect_delay,
    )

    coordinator = BoseCSPCoordinator(hass, device)

    # Allow DSP network stack to settle after WebSocket discovery
    await asyncio.sleep(2)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = BoseCSPData(
        device=device,
        coordinator=coordinator,
        source_list=source_list,
        min_db=min_db,
        max_db=max_db,
    )

    # Register options update listener
    entry.async_on_unload(entry.add_update_listener(update_listener))

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


async def update_listener(hass: HomeAssistant, entry: BoseCSPConfigEntry) -> None:
    """Handle options update."""
    _LOGGER.debug("Reloading Bose CSP integration due to options update")
    await hass.config_entries.async_reload(entry.entry_id)