"""Test the Bose CSP health-check sensor platform."""

from homeassistant.components.bose_csp.const import DOMAIN
from homeassistant.core import HomeAssistant

try:
    from tests.common import MockConfigEntry
except ImportError:
    from pytest_homeassistant_custom_component.common import MockConfigEntry


async def setup_integration(hass: HomeAssistant, mock_device) -> MockConfigEntry:
    """Set up the integration for sensor testing."""
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


async def test_health_sensor_created_and_updates(
    hass: HomeAssistant, mock_device
) -> None:
    """The health sensor exists, is a diagnostic, and tracks status updates."""
    entry = await setup_integration(hass, mock_device)

    state = hass.states.get("sensor.bose_csp_health_checking")
    assert state is not None
    assert state.attributes.get("health_zone") == "Bar"

    # Drive a health-status change through the coordinator callback.
    coordinator = entry.runtime_data.coordinator
    coordinator._handle_health_update("starting")
    await hass.async_block_till_done()
    assert hass.states.get("sensor.bose_csp_health_checking").state == "starting"

    coordinator._handle_health_update("Socket Not Connected")
    await hass.async_block_till_done()
    assert (
        hass.states.get("sensor.bose_csp_health_checking").state
        == "Socket Not Connected"
    )


async def test_health_sensor_available_while_disconnected(
    hass: HomeAssistant, mock_device
) -> None:
    """The sensor stays available when the device is offline so it can report it."""
    entry = await setup_integration(hass, mock_device)
    coordinator = entry.runtime_data.coordinator

    coordinator._handle_availability_update(False)
    coordinator._handle_health_update("Socket Not Connected")
    await hass.async_block_till_done()

    state = hass.states.get("sensor.bose_csp_health_checking")
    assert state.state == "Socket Not Connected"  # not "unavailable"
