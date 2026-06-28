"""Pytest conftest for Bose CSP tests."""

import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

# Ensure the custom_components directory is in sys.path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../custom_components"))
)

# Map homeassistant.components.bose_csp to custom_components.bose_csp for local execution
import custom_components.bose_csp as custom_bose_csp
import custom_components.bose_csp.const
import custom_components.bose_csp.coordinator
import custom_components.bose_csp.config_flow
import custom_components.bose_csp.media_player
import custom_components.bose_csp.switch
import custom_components.bose_csp.entity

sys.modules["homeassistant.components.bose_csp"] = custom_bose_csp
sys.modules["homeassistant.components.bose_csp.const"] = custom_bose_csp.const
sys.modules["homeassistant.components.bose_csp.coordinator"] = custom_bose_csp.coordinator
sys.modules["homeassistant.components.bose_csp.config_flow"] = custom_bose_csp.config_flow
sys.modules["homeassistant.components.bose_csp.media_player"] = custom_bose_csp.media_player
sys.modules["homeassistant.components.bose_csp.switch"] = custom_bose_csp.switch
sys.modules["homeassistant.components.bose_csp.entity"] = custom_bose_csp.entity

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
        device.connect = AsyncMock()
        device.disconnect = AsyncMock()

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
        device.set_volume = AsyncMock()
        device.set_mute = AsyncMock()
        device.set_source = AsyncMock()
        device.set_auto_volume = AsyncMock()

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
                    "id": 1,
                    "enabled": True,
                    "min_gain": -60.0,
                    "max_gain": 12.0,
                    "gain": -12.0,
                },
                {
                    "label": "Patio",
                    "id": 2,
                    "enabled": True,
                    "min_gain": -45.0,
                    "max_gain": 0.0,
                    "gain": -20.0,
                },
                {"label": "Disabled Zone", "id": 3, "enabled": False},
            ],
            "sources": [
                {"label": "Sonos", "id": 1, "enabled": True},
                {"label": "Aux", "id": 2, "enabled": True},
                {"label": "Disabled Source", "id": 3, "enabled": False},
            ],
        }
        yield mock


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for testing."""
    yield


@pytest.fixture(autouse=True, scope="session")
def link_custom_component():
    """Link local custom component to the testing_config directory."""
    import os
    import pytest_homeassistant_custom_component
    pkg_dir = os.path.dirname(pytest_homeassistant_custom_component.__file__)
    dest_dir = os.path.join(pkg_dir, "testing_config", "custom_components", "bose_csp")
    src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../custom_components/bose_csp"))
    
    if not os.path.exists(dest_dir):
        try:
            os.symlink(src_dir, dest_dir)
            yield
            try:
                os.unlink(dest_dir)
            except OSError:
                pass
        except Exception:
            yield
    else:
        yield
