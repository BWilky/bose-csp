"""Test the Bose CSP AutoVolume switch platform."""

from pybosecsp import ZoneState

from homeassistant.components.bose_csp.const import DOMAIN
from homeassistant.components.switch import (
    DOMAIN as SWITCH_DOMAIN,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
)
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant

try:
    from tests.common import MockConfigEntry
except ImportError:
    from pytest_homeassistant_custom_component.common import MockConfigEntry


async def setup_integration(hass: HomeAssistant, mock_device) -> MockConfigEntry:
    """Set up the integration for switch testing."""
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
    return entry


async def test_switch_setup_reflects_state(hass: HomeAssistant, mock_device) -> None:
    """AutoVolume switches are created, one per zone, reflecting device state."""
    mock_device.get_all_states.return_value = {
        "Bar": ZoneState(volume=-12.0, current_source=1, auto_volume=True),
        "Patio": ZoneState(volume=-20.0, current_source=2, auto_volume=False),
    }
    await setup_integration(hass, mock_device)

    state_bar = hass.states.get("switch.bose_csp_bar_autovolume")
    assert state_bar is not None
    assert state_bar.state == "on"

    state_patio = hass.states.get("switch.bose_csp_patio_autovolume")
    assert state_patio is not None
    assert state_patio.state == "off"


async def test_switch_turn_on_off(hass: HomeAssistant, mock_device) -> None:
    """Turning the switch on/off calls set_auto_volume."""
    await setup_integration(hass, mock_device)

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "switch.bose_csp_bar_autovolume"},
        blocking=True,
    )
    mock_device.set_auto_volume.assert_awaited_with("Bar", True)

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: "switch.bose_csp_bar_autovolume"},
        blocking=True,
    )
    mock_device.set_auto_volume.assert_awaited_with("Bar", False)
