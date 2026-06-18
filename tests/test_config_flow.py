"""Test the Bose CSP config flow."""

from unittest.mock import MagicMock, patch
from pybosecsp import BoseCSPConnectionError
import pytest

from homeassistant.components.bose_csp.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

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

            def add_to_hass(self, hass):
                """Mock add to hass."""
                hass.config_entries._entries[self.entry_id] = self


async def test_flow_discovery_success(
    hass: HomeAssistant, mock_device, mock_discovery
) -> None:
    """Test config flow with successful discovery and entity selection."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    # Submit IP address
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "host": "10.50.0.70",
        },
    )
    # Since discovery succeeds, it must redirect to select_entities
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "select_entities"

    # Select the zones and sources
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "zones": ["Bar", "Patio"],
            "sources": ["Sonos", "Aux"],
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "10.50.0.70"
    assert result["data"] == {
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
    }


async def test_flow_discovery_failure_fallback(
    hass: HomeAssistant, mock_device, mock_discovery
) -> None:
    """Test config flow with discovery failure falling back to manual setup."""
    mock_discovery.side_effect = BoseCSPConnectionError(
        "Websocket connection closed"
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    with patch("homeassistant.components.bose_csp.config_flow.asyncio.sleep") as mock_sleep:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "10.50.0.70",
            },
        )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "manual"
    assert result["errors"] == {"base": "discovery_failed"}

    # Mock connection test for manual setup
    mock_device.connect.side_effect = None

    # Submit manual entries
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "zones": "Zone 1, Zone 2",
            "sources": "Source 1, Source 2",
            "min_db": -60.0,
            "max_db": 12.0,
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "10.50.0.70"
    assert result["data"] == {
        "host": "10.50.0.70",
        "zones": "Zone 1, Zone 2",
        "sources": "Source 1, Source 2",
        "min_db": -60.0,
        "max_db": 12.0,
    }


async def test_flow_manual_connection_failure(
    hass: HomeAssistant, mock_device, mock_discovery
) -> None:
    """Test config flow manual fallback with connection error."""
    mock_discovery.side_effect = BoseCSPConnectionError("Discovery fails")
    mock_device.connect.side_effect = BoseCSPConnectionError(
        "TCP connection fails"
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    # Enter host
    with patch("homeassistant.components.bose_csp.config_flow.asyncio.sleep") as mock_sleep:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "10.50.0.70",
            },
        )
    assert result["step_id"] == "manual"
    assert result["errors"] == {"base": "discovery_failed"}

    # Submit manual config, connection fails
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "zones": "Zone 1",
            "sources": "Source 1",
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "manual"
    assert result["errors"] == {"base": "cannot_connect"}


async def test_flow_duplicate_abort(
    hass: HomeAssistant, mock_device, mock_discovery
) -> None:
    """Test config flow aborts when device is already configured."""
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

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "host": "10.50.0.70",
        },
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_options_flow(hass: HomeAssistant) -> None:
    """Test updating options via options flow."""
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
        options={
            "volume_interval": 5,
            "other_interval": 30,
            "reconnect_delay": 5,
        },
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    # Submit updated options
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            "volume_interval": 10,
            "other_interval": 60,
            "reconnect_delay": 15,
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        "volume_interval": 10,
        "other_interval": 60,
        "reconnect_delay": 15,
    }


async def test_flow_discovery_zero_limits_fallback(
    hass: HomeAssistant, mock_device, mock_discovery
) -> None:
    """Test config flow with discovery returning zero or invalid limits correctly falls back."""
    mock_discovery.return_value["zones"][0]["min_gain"] = 0.0
    mock_discovery.return_value["zones"][0]["max_gain"] = 0.0
    mock_discovery.return_value["zones"][1]["min_gain"] = 10.0
    mock_discovery.return_value["zones"][1]["max_gain"] = -10.0  # Invalid min > max

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "host": "10.50.0.70",
        },
    )
    assert result["step_id"] == "select_entities"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "zones": ["Bar", "Patio"],
            "sources": ["Sonos", "Aux"],
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    # Both zones should have fallen back to default limits -60.0 and 12.0
    assert result["data"]["zone_limits"] == {
        "Bar": {"min_db": -60.0, "max_db": 12.0},
        "Patio": {"min_db": -60.0, "max_db": 12.0},
    }

