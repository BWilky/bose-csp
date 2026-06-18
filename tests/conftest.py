"""Pytest conftest for Bose CSP tests."""

import os
import sys
from unittest.mock import MagicMock, patch
import pytest

# Ensure the custom_components directory is in sys.path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../custom_components"))
)

# Map homeassistant.components.bose_csp to local bose_csp for local execution
import bose_csp

sys.modules["homeassistant.components.bose_csp"] = bose_csp
sys.modules["homeassistant.components.bose_csp.const"] = sys.modules.get(
    "bose_csp.const"
)
sys.modules["homeassistant.components.bose_csp.coordinator"] = sys.modules.get(
    "bose_csp.coordinator"
)
sys.modules["homeassistant.components.bose_csp.config_flow"] = sys.modules.get(
    "bose_csp.config_flow"
)
sys.modules["homeassistant.components.bose_csp.media_player"] = sys.modules.get(
    "bose_csp.media_player"
)
sys.modules["homeassistant.components.bose_csp.entity"] = sys.modules.get(
    "bose_csp.entity"
)

from pybosecsp import ZoneState


@pytest.fixture
def mock_device():
    """Mock a BoseCSPDevice."""
    with (
        patch(
            "homeassistant.components.bose_csp.config_flow.BoseCSPDevice",
            autospec=True,
        ) as mock_flow_device,
        patch(
            "homeassistant.components.bose_csp.coordinator.BoseCSPDevice",
            autospec=True,
        ) as mock_coord_device,
        patch(
            "homeassistant.components.bose_csp.BoseCSPDevice", autospec=True
        ) as mock_root_device,
    ):
        device = mock_root_device.return_value
        device.host = "10.50.0.70"
        device.is_connected = True
        device.connect = MagicMock()
        device.disconnect = MagicMock()

        # Default mock states
        states = {
            "Bar": ZoneState(volume=-12.0, is_muted=False, current_source=1),
            "Patio": ZoneState(volume=-20.0, is_muted=True, current_source=2),
        }
        device.get_all_states = MagicMock(return_value=states)
        device.get_zone_state = MagicMock(side_effect=lambda z: states[z])

        device.subscribe_updates = MagicMock()
        device.subscribe_availability = MagicMock()
        device.unsubscribe_updates = MagicMock()
        device.unsubscribe_availability = MagicMock()
        device.set_volume = MagicMock()
        device.set_mute = MagicMock()
        device.set_source = MagicMock()

        # Make other mocks return the same instance for consistency
        mock_flow_device.return_value = device
        mock_coord_device.return_value = device

        yield device


@pytest.fixture
def mock_discovery():
    """Mock discover_zones_and_sources."""
    with patch(
        "homeassistant.components.bose_csp.config_flow.discover_zones_and_sources"
    ) as mock:
        mock.return_value = {
            "zones": [
                {
                    "label": "Bar",
                    "zoneId": 1,
                    "enabled": True,
                    "min_gain": -60.0,
                    "max_gain": 12.0,
                    "gain": -12.0,
                },
                {
                    "label": "Patio",
                    "zoneId": 2,
                    "enabled": True,
                    "min_gain": -45.0,
                    "max_gain": 0.0,
                    "gain": -20.0,
                },
                {"label": "Disabled Zone", "zoneId": 3, "enabled": False},
            ],
            "sources": [
                {"label": "Sonos", "sourceId": 1, "enabled": True},
                {"label": "Aux", "sourceId": 2, "enabled": True},
                {"label": "Disabled Source", "sourceId": 3, "enabled": False},
            ],
        }
        yield mock
