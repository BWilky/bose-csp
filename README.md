# Bose CSP Integration for Home Assistant


# See https://github.com/BWilky/bose-csp for native HA integration

This custom integration provides control over Bose Commercial Sound Processor (CSP) devices from Home Assistant.

## Features

- **WebSocket Auto-Discovery:** Automatically scans and detects configured zones and sources.
- **Media Player Platform:** Creates media player entities for each selected zone with controls for volume level, muting, and source selection.
- **Dynamic Volume Limits:** Automatically reads and respects the minimum and maximum gain bounds configured on the device for each zone.
- **Source Mapping:** Maps selected sources directly to their respective internal device IDs to align input channels.
- **Connection Recovery:** Uses a persistent TCP client connection that automatically detects drops and reconnects.

## Installation

### Via HACS
1. Open HACS in Home Assistant.
2. Select the three dots in the top-right and click **Custom repositories**.
3. Paste `https://github.com/BWilky/bose-csp` and select **Integration** as the category.
4. Click **Add**, find the integration card, and select **Download**.
5. Restart Home Assistant.

### Manual Installation
1. Copy the `custom_components/bose_csp/` directory into your Home Assistant `config/custom_components/` folder.
2. Restart Home Assistant.

## Important Note

The Bose CSP Web API only allows one active configuration session at a time. If the Web Dashboard is open in a browser, auto-discovery will fail. Ensure the Web Dashboard is closed before attempting integration setup.

## Configuration

1. Go to **Settings** -> **Devices & Services**.
2. Click **Add Integration** and search for **Bose CSP**.
3. Enter the IP address of the device.
4. Select the discovered zones and sources you want to enable.
