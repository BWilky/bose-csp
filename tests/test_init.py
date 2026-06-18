"""Test the Bose CSP integration initialization."""

from unittest.mock import patch
from pybosecsp import BoseCSPConnectionError
import pytest

from homeassistant.components.bose_csp.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

try:
    from tests.common import MockConfigEntry
except ImportError:
    try:
        from pytest_homeassistant_custom_component.common import MockConfigEntry
    except ImportError:
        # Fallback dummy class if not running in a full HA test context
        class MockConfigEntry:
            """Dummy config entry for testing fallback."""

            def __init__(self, **kwargs):
                self.__dict__.update(kwargs)
                self.state = ConfigEntryState.NOT_LOADED
                self.entry_id = "test_entry"

            def add_to_hass(self, hass):
                """Mock add to hass."""
                hass.config_entries._entries[self.entry_id] = self


async def test_setup_unload_entry(hass: HomeAssistant, mock_device) -> None:
    """Test setting up and unloading the config entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="10.50.0.70",
        data={
            "host": "10.50.0.70",
            "zones": "Bar, Patio",
            "sources": "Sonos, Aux",
            "min_db": -60.0,
            "max_db": 12.0,
            "zone_limits": {
                "Bar": {"min_db": -60.0, "max_db": 12.0},
                "Patio": {"min_db": -45.0, "max_db": 0.0},
            },
            "source_mapping": {
                "Sonos": 1,
                "Aux": 2,
            },
        },
    )
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.config_entries.ConfigEntries.async_forward_entry_setups",
        return_value=True,
    ) as mock_forward:
        # Setup the entry
        assert await hass.config_entries.async_setup(entry.entry_id)
        assert entry.state is ConfigEntryState.LOADED
        assert mock_forward.call_count == 1

        # Unload the entry
        assert await hass.config_entries.async_unload(entry.entry_id)
        assert entry.state is ConfigEntryState.NOT_LOADED
        assert mock_device.disconnect.call_count == 1


async def test_setup_entry_connection_error(
    hass: HomeAssistant, mock_device
) -> None:
    """Test setup failure when device connection fails."""
    mock_device.connect.side_effect = BoseCSPConnectionError(
        "TCP connection fails"
    )

    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="10.50.0.70",
        data={
            "host": "10.50.0.70",
            "zones": "Bar",
            "sources": "Sonos",
            "min_db": -60.0,
            "max_db": 12.0,
        },
    )
    entry.add_to_hass(hass)

    # Setup should fail and set state to SETUP_RETRY
    await hass.config_entries.async_setup(entry.entry_id)
    assert entry.state is ConfigEntryState.SETUP_RETRY
