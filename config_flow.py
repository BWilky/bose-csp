"""Config flow for Bose CSP integration."""

from __future__ import annotations

import logging
from typing import Any

from pybosecsp import BoseCSPConnectionError, BoseCSPDevice
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST

from .const import CONF_MAX_DB, CONF_MIN_DB, CONF_SOURCES, CONF_ZONES, DOMAIN

_LOGGER = logging.getLogger(__name__)


class BoseCSPConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Bose CSP."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._host: str = ""
        self._min_db: float = -60.0
        self._max_db: float = 12.0
        self._discovered_zones: list[dict[str, Any]] = []
        self._discovered_sources: list[dict[str, Any]] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._host = user_input[CONF_HOST]
            self._min_db = user_input[CONF_MIN_DB]
            self._max_db = user_input[CONF_MAX_DB]

            await self.async_set_unique_id(self._host)
            self._abort_if_unique_id_configured()

            # Attempt WebSocket auto-discovery
            try:
                discovery_data = await discover_zones_and_sources(self._host)
            except BoseCSPConnectionError as err:
                _LOGGER.warning(
                    "Auto-discovery failed: %s. Falling back to manual configuration.",
                    err,
                )
                return await self.async_step_manual()

            self._discovered_zones = [
                z for z in discovery_data.get("zones", []) if z.get("enabled")
            ]
            self._discovered_sources = [
                s for s in discovery_data.get("sources", []) if s.get("enabled")
            ]

            if not self._discovered_zones:
                _LOGGER.warning(
                    "No enabled zones discovered. Falling back to manual configuration."
                )
                return await self.async_step_manual()

            return await self.async_step_select_entities()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Optional(CONF_MIN_DB, default=-60.0): vol.Coerce(float),
                    vol.Optional(CONF_MAX_DB, default=12.0): vol.Coerce(float),
                }
            ),
            errors=errors,
        )

    async def async_step_select_entities(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle selecting zones and sources from discovered data."""
        errors: dict[str, str] = {}

        if user_input is not None:
            selected_zones = user_input[CONF_ZONES]
            selected_sources = user_input[CONF_SOURCES]

            zone_limits = {}
            for zone in self._discovered_zones:
                label = zone["label"]
                if label in selected_zones:
                    min_gain = zone.get("min_gain")
                    max_gain = zone.get("max_gain")
                    zone_limits[label] = {
                        "min_db": float(min_gain) if min_gain is not None else self._min_db,
                        "max_db": float(max_gain) if max_gain is not None else self._max_db,
                    }

            source_mapping = {}
            for src in self._discovered_sources:
                label = src["label"]
                if label in selected_sources:
                    source_mapping[label] = src["id"]

            return self.async_create_entry(
                title=self._host,
                data={
                    CONF_HOST: self._host,
                    CONF_ZONES: ", ".join(selected_zones),
                    CONF_SOURCES: ", ".join(selected_sources),
                    CONF_MIN_DB: self._min_db,
                    CONF_MAX_DB: self._max_db,
                    "zone_limits": zone_limits,
                    "source_mapping": source_mapping,
                },
            )

        zone_options = [z["label"] for z in self._discovered_zones if z.get("label")]
        source_options = [s["label"] for s in self._discovered_sources if s.get("label")]

        select_schema = vol.Schema(
            {
                vol.Required(CONF_ZONES, default=zone_options): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=zone_options,
                        mode=selector.SelectSelectorMode.LIST,
                        multiple=True,
                    )
                ),
                vol.Required(CONF_SOURCES, default=source_options): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=source_options,
                        mode=selector.SelectSelectorMode.LIST,
                        multiple=True,
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="select_entities",
            data_schema=select_schema,
            errors=errors,
        )

    async def async_step_manual(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle manual configuration fallback."""
        errors: dict[str, str] = {}

        if user_input is not None:
            zones_str = user_input[CONF_ZONES]
            zones_list = [zone.strip() for zone in zones_str.split(",")]

            device = BoseCSPDevice(self._host, zones_list)
            try:
                await device.connect()
                await device.disconnect()
            except BoseCSPConnectionError as err:
                _LOGGER.error("Failed to connect to %s: %s", self._host, err)
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=self._host,
                    data={
                        CONF_HOST: self._host,
                        CONF_ZONES: user_input[CONF_ZONES],
                        CONF_SOURCES: user_input[CONF_SOURCES],
                        CONF_MIN_DB: self._min_db,
                        CONF_MAX_DB: self._max_db,
                    },
                )

        manual_schema = vol.Schema(
            {
                vol.Required(CONF_ZONES): str,
                vol.Required(CONF_SOURCES): str,
            }
        )

        return self.async_show_form(
            step_id="manual",
            data_schema=manual_schema,
            errors=errors,
        )