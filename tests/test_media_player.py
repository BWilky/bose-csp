"""Test the Bose CSP media player platform."""

from pybosecsp import ZoneState
import pytest

from homeassistant.components.bose_csp.const import DOMAIN
from homeassistant.components.media_player import (
    ATTR_INPUT_SOURCE,
    ATTR_MEDIA_VOLUME_LEVEL,
    ATTR_MEDIA_VOLUME_MUTED,
    DOMAIN as MEDIA_PLAYER_DOMAIN,
    SERVICE_SELECT_SOURCE,
    SERVICE_VOLUME_MUTE,
    SERVICE_VOLUME_SET,
)
from homeassistant.const import ATTR_ENTITY_ID
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
                self.entry_id = "test_entry"

            def add_to_hass(self, hass):
                """Mock add to hass."""
                hass.config_entries._entries[self.entry_id] = self


async def setup_integration(hass: HomeAssistant, mock_device) -> MockConfigEntry:
    """Set up the integration for media player testing."""
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
                "Patio": {"min_db": -40.0, "max_db": 0.0},
            },
            "source_mapping": {
                "Sonos": 1,
                "Aux": 2,
            },
        },
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_media_player_setup(hass: HomeAssistant, mock_device) -> None:
    """Test media player entity creation and initial state."""
    await setup_integration(hass, mock_device)

    # Verify entities are created
    state_bar = hass.states.get("media_player.bar")
    assert state_bar is not None
    assert state_bar.state == "on"
    assert state_bar.attributes.get("friendly_name") == "Bar"
    # Bar uses min_db=-60.0, max_db=12.0 (range=72.0). Default volume in mock is -12.0dB.
    # Level = (-12.0 - (-60.0)) / 72.0 = 48.0 / 72.0 = 0.6666...
    assert round(state_bar.attributes.get(ATTR_MEDIA_VOLUME_LEVEL), 2) == 0.67
    assert state_bar.attributes.get(ATTR_MEDIA_VOLUME_MUTED) is False
    assert state_bar.attributes.get(ATTR_INPUT_SOURCE) == "Sonos"

    state_patio = hass.states.get("media_player.patio")
    assert state_patio is not None
    assert state_patio.state == "on"
    # Patio uses min_db=-40.0, max_db=0.0 (range=40.0). Default volume in mock is -20.0dB.
    # Level = (-20.0 - (-40.0)) / 40.0 = 20.0 / 40.0 = 0.50
    assert state_patio.attributes.get(ATTR_MEDIA_VOLUME_LEVEL) == 0.50
    assert state_patio.attributes.get(ATTR_MEDIA_VOLUME_MUTED) is True
    assert state_patio.attributes.get(ATTR_INPUT_SOURCE) == "Aux"


async def test_media_player_set_volume(
    hass: HomeAssistant, mock_device
) -> None:
    """Test volume control service call converts dB correctly."""
    await setup_integration(hass, mock_device)

    # Set volume for Bar (min_db=-60, max_db=12, range=72)
    # level = 0.5 -> volume_db = 0.5 * 72 + (-60) = -24dB
    await hass.services.async_call(
        MEDIA_PLAYER_DOMAIN,
        SERVICE_VOLUME_SET,
        {ATTR_ENTITY_ID: "media_player.bar", ATTR_MEDIA_VOLUME_LEVEL: 0.5},
        blocking=True,
    )
    mock_device.set_volume.assert_called_with("Bar", -24.0)

    # Set volume for Patio (min_db=-40, max_db=0, range=40)
    # level = 0.8 -> volume_db = 0.8 * 40 + (-40) = -8dB
    await hass.services.async_call(
        MEDIA_PLAYER_DOMAIN,
        SERVICE_VOLUME_SET,
        {ATTR_ENTITY_ID: "media_player.patio", ATTR_MEDIA_VOLUME_LEVEL: 0.8},
        blocking=True,
    )
    mock_device.set_volume.assert_called_with("Patio", -8.0)


async def test_media_player_mute(hass: HomeAssistant, mock_device) -> None:
    """Test muting service call."""
    await setup_integration(hass, mock_device)

    await hass.services.async_call(
        MEDIA_PLAYER_DOMAIN,
        SERVICE_VOLUME_MUTE,
        {ATTR_ENTITY_ID: "media_player.bar", ATTR_MEDIA_VOLUME_MUTED: True},
        blocking=True,
    )
    mock_device.set_mute.assert_called_with("Bar", True)


async def test_media_player_select_source(
    hass: HomeAssistant, mock_device
) -> None:
    """Test select source service maps source names back to sourceId."""
    await setup_integration(hass, mock_device)

    # Sonos -> sourceId 1
    await hass.services.async_call(
        MEDIA_PLAYER_DOMAIN,
        SERVICE_SELECT_SOURCE,
        {ATTR_ENTITY_ID: "media_player.bar", ATTR_INPUT_SOURCE: "Sonos"},
        blocking=True,
    )
    mock_device.set_source.assert_called_with("Bar", 1)

    # Aux -> sourceId 2
    await hass.services.async_call(
        MEDIA_PLAYER_DOMAIN,
        SERVICE_SELECT_SOURCE,
        {ATTR_ENTITY_ID: "media_player.bar", ATTR_INPUT_SOURCE: "Aux"},
        blocking=True,
    )
    mock_device.set_source.assert_called_with("Bar", 2)


async def test_media_player_coordinator_update(
    hass: HomeAssistant, mock_device
) -> None:
    """Test coordinator updates propagate to media player state."""
    await setup_integration(hass, mock_device)

    # Find the coordinator in active entries
    entries = hass.config_entries.async_entries(DOMAIN)
    entry = entries[0]
    coordinator = entry.runtime_data.coordinator

    # Update states in mocked device
    new_states = {
        "Bar": ZoneState(volume=-6.0, is_muted=True, current_source=2),
        "Patio": ZoneState(volume=0.0, is_muted=False, current_source=1),
    }
    mock_device.get_all_states.return_value = new_states
    mock_device.get_zone_state.side_effect = lambda z: new_states[z]

    # Trigger callback
    coordinator._handle_device_update("Bar")
    await hass.async_block_till_done()

    state_bar = hass.states.get("media_player.bar")
    # Bar level: (-6.0 - (-60.0)) / 72.0 = 54.0 / 72.0 = 0.75
    assert state_bar.attributes.get(ATTR_MEDIA_VOLUME_LEVEL) == 0.75
    assert state_bar.attributes.get(ATTR_MEDIA_VOLUME_MUTED) is True
    assert state_bar.attributes.get(ATTR_INPUT_SOURCE) == "Aux"


async def test_media_player_availability(
    hass: HomeAssistant, mock_device
) -> None:
    """Test availability changes when device goes offline."""
    await setup_integration(hass, mock_device)

    entries = hass.config_entries.async_entries(DOMAIN)
    entry = entries[0]
    coordinator = entry.runtime_data.coordinator

    # Device goes offline
    coordinator._handle_availability_update(False)
    await hass.async_block_till_done()

    state_bar = hass.states.get("media_player.bar")
    assert state_bar.state == "unavailable"
