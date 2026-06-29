---
title: Bose CSP
description: Instructions on how to integrate Bose Professional CSP commercial sound processors into Home Assistant.
ha_category:
  - Media player
ha_release: "2026.7"
ha_iot_class: Local Polling
ha_config_flow: true
ha_codeowners:
  - "@BWilky"
ha_domain: bose_csp
ha_integration_type: device
ha_quality_scale: bronze
ha_platforms:
  - diagnostics
  - media_player
  - sensor
  - switch
ha_dhcp: true
---

The **Bose CSP** {% term integration %} lets you control Bose Professional
[CSP-428 and CSP-1248](https://boseprofessional.com/solutions/csp-systems)
commercial sound processors from Home Assistant over your local network.

Each configured listening area (zone) is exposed as a {% term "media player" %}
for volume, mute, and source (input) control. The integration communicates with
the processor using the documented Bose CSP Serial Control Protocol over TCP
(SoIP, port 10055); no cloud connection is used.

## Supported devices

- Bose Professional CSP-428
- Bose Professional CSP-1248

The processor must be running software version 2.2 or later and have a **static
IP address** (set in the device web UI under **Settings > Network**, or with the
Bose Discovery Tool).

## Prerequisites

The CSP exposes a single, exclusive web configuration dashboard. While that
dashboard is open in a browser it holds the device's configuration session and
the integration cannot connect (and is disconnected if it was connected). Close
the web dashboard before adding or using the integration.

{% include integrations/config_flow.md %}

During setup the integration connects to the processor and attempts to
auto-discover the configured listening areas (zones) and input sources. If
auto-discovery cannot reach the device, you are asked to enter the zone and
source names manually (comma-separated), along with default minimum and maximum
volume limits in dB.

## Supported functionality

### Media player

One media player entity is created per listening area, supporting:

- Volume set (mapped to the zone's configured min/max dB range)
- Mute / unmute
- Source selection (input routing)

The `auto_volume` attribute reports whether the zone's AutoVolume is active.
While AutoVolume is on, the device controls the level and manual volume changes
are ignored (see [Known limitations](#known-limitations)).

### Switch

An **AutoVolume** switch is created per zone to turn the device's AutoVolume
feature on or off. (AutoVolume can only be toggled on zones that have been
AutoVolume-calibrated on the device.)

### Sensor

A diagnostic **Health Checking** sensor reports the status of the optional
active health check (see [Configuration options](#configuration-options)).

## Configuration options

After setup, select **Configure** on the integration to adjust:

- **Volume Polling Interval** – how often the device volume is polled.
- **Mute/Source Polling Interval** – how often mute/source/AutoVolume are polled.
- **Reconnection Delay** – base delay between reconnection attempts.
- **Health Checking** – when enabled (default), the integration periodically
  (every 30 minutes) verifies it can actively control the device by making an
  inaudible 0.5 dB adjustment on a non-AutoVolume zone, reading it back, and
  immediately restoring the original level. You will not hear or see any change.
  The **Health Checking** sensor reports the result: `Healthy`, `Starting`,
  `Checking`, `Not available - AutoVolume` (no usable zone), `Socket Not
  Connected`, `Failing`, or `Can't reconnect`.

## Removing the integration

This integration can be removed by following these steps:

{% include integrations/remove_device_service.md %}

## Troubleshooting

### Zones become unavailable when I open the device web dashboard

This is expected. The CSP allows only one configuration session; opening the web
dashboard disconnects the integration. Close the dashboard and the integration
reconnects automatically (typically within 30 seconds).

### Volume changes do nothing on a zone

The zone likely has AutoVolume enabled, which makes the device control the level
and reject manual volume changes. Turn the zone's **AutoVolume** switch off to
regain manual control.

## Known limitations

- Setting volume is not possible while a zone's AutoVolume is on.
- The integration cannot run while the device's web configuration dashboard is
  open (single-session device).
- Source names and zone names come from the device configuration and are not
  translated.
