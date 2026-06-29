"""Config flow for Bose CSP integration."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from pybosecsp import BoseCSPConnectionError, discover_zones_and_sources
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.data_entry_flow import AbortFlow
from homeassistant.const import CONF_HOST
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_HEALTHCHECK_ENABLED,
    CONF_MAX_DB,
    CONF_MIN_DB,
    CONF_OTHER_INTERVAL,
    CONF_RECONNECT_DELAY,
    CONF_SOURCES,
    CONF_VOLUME_INTERVAL,
    CONF_ZONES,
    DEFAULT_HEALTHCHECK_ENABLED,
    DEFAULT_OTHER_INTERVAL,
    DEFAULT_RECONNECT_DELAY,
    DEFAULT_VOLUME_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class BoseCSPConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Bose CSP."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        super().__init__()
        self._host: str = ""
        self._min_db: float = -60.0
        self._max_db: float = 12.0
        self._discovered_zones: list[dict[str, Any]] = []
        self._discovered_sources: list[dict[str, Any]] = []
        self._discovery_failed: bool = False

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._host = user_input[CONF_HOST]

            try:
                await self.async_set_unique_id(self._host)
                self._abort_if_unique_id_configured()

                # Attempt WebSocket auto-discovery with retries
                discovery_data = None
                for attempt in range(4):
                    try:
                        discovery_data = await discover_zones_and_sources(self._host)
                        break
                    except BoseCSPConnectionError as err:
                        _LOGGER.warning(
                            "Auto-discovery attempt %d/4 failed for %s: %s",
                            attempt + 1,
                            self._host,
                            err,
                        )
                        if attempt < 3:
                            await asyncio.sleep(3)
                        else:
                            raise err
            except BoseCSPConnectionError:
                _LOGGER.warning(
                    "Auto-discovery failed after 4 attempts. Falling back to manual configuration."
                )
                self._discovery_failed = True
                return await self.async_step_manual()
            except AbortFlow:
                raise
            except Exception as err:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected error during auto-discovery: %s", err)
                errors["base"] = "unknown"
                return self.async_show_form(
                    step_id="user",
                    data_schema=vol.Schema(
                        {
                            vol.Required(CONF_HOST): str,
                        }
                    ),
                    errors=errors,
                )

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
                self._discovery_failed = True
                return await self.async_step_manual()

            return await self.async_step_select_entities()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
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
                    z_min = float(min_gain) if min_gain is not None else self._min_db
                    z_max = float(max_gain) if max_gain is not None else self._max_db
                    if z_min >= z_max or (z_min == 0.0 and z_max == 0.0):
                        z_min = self._min_db
                        z_max = self._max_db
                    zone_limits[label] = {
                        "min_db": z_min,
                        "max_db": z_max,
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
        if self._discovery_failed and user_input is None:
            errors["base"] = "discovery_failed"

        if user_input is not None:
            self._min_db = user_input[CONF_MIN_DB]
            self._max_db = user_input[CONF_MAX_DB]

            # Connectivity is validated when the entry is set up (the
            # coordinator connects on first refresh), so no probe here.
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
                vol.Optional(CONF_MIN_DB, default=-60.0): vol.Coerce(float),
                vol.Optional(CONF_MAX_DB, default=12.0): vol.Coerce(float),
            }
        )

        return self.async_show_form(
            step_id="manual",
            data_schema=manual_schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> BoseCSPOptionsFlowHandler:
        """Get the options flow for this handler."""
        return BoseCSPOptionsFlowHandler(config_entry)


class BoseCSPOptionsFlowHandler(OptionsFlow):
    """Handle options flow for Bose CSP."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        super().__init__()
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_VOLUME_INTERVAL,
                    default=self.config_entry.options.get(
                        CONF_VOLUME_INTERVAL, DEFAULT_VOLUME_INTERVAL
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=60)),
                vol.Optional(
                    CONF_OTHER_INTERVAL,
                    default=self.config_entry.options.get(
                        CONF_OTHER_INTERVAL, DEFAULT_OTHER_INTERVAL
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=5, max=300)),
                vol.Optional(
                    CONF_RECONNECT_DELAY,
                    default=self.config_entry.options.get(
                        CONF_RECONNECT_DELAY, DEFAULT_RECONNECT_DELAY
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=60)),
                vol.Optional(
                    CONF_HEALTHCHECK_ENABLED,
                    default=self.config_entry.options.get(
                        CONF_HEALTHCHECK_ENABLED, DEFAULT_HEALTHCHECK_ENABLED
                    ),
                ): bool,
            }
        )

        return self.async_show_form(step_id="init", data_schema=options_schema)