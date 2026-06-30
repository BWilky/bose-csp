"""Diagnostics support for Bose CSP."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant

from .coordinator import BoseCSPConfigEntry

TO_REDACT = {CONF_HOST}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: BoseCSPConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data.coordinator
    device = coordinator.device

    return {
        "entry_data": async_redact_data(dict(entry.data), TO_REDACT),
        "entry_options": dict(entry.options),
        "is_connected": device.is_connected,
        "health_status": coordinator.health_status,
        "health_zone": device.health_zone,
        "zones": {
            zone: asdict(state)
            for zone, state in device.get_all_states().items()
        },
    }
