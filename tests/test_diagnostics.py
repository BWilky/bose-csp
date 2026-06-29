"""Test the Bose CSP diagnostics."""

from homeassistant.components.bose_csp.const import DOMAIN
from homeassistant.components.bose_csp.diagnostics import (
    async_get_config_entry_diagnostics,
)
from homeassistant.core import HomeAssistant

try:
    from tests.common import MockConfigEntry
except ImportError:
    from pytest_homeassistant_custom_component.common import MockConfigEntry


async def test_diagnostics(hass: HomeAssistant, mock_device) -> None:
    """Diagnostics redact the host and include zone/health data."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="10.50.0.70",
        data={
            "host": "10.50.0.70",
            "zones": "Bar, Patio",
            "sources": "Sonos, Aux",
            "min_db": -60.0,
            "max_db": 12.0,
        },
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    diag = await async_get_config_entry_diagnostics(hass, entry)

    assert diag["entry_data"]["host"] == "**REDACTED**"
    assert "Bar" in diag["zones"]
    assert "is_connected" in diag
    assert "health_status" in diag
