"""Media player platform for Bose CSP."""

from __future__ import annotations

import logging

from pybosecsp import BoseCSPCommandError

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import BoseCSPConfigEntry, BoseCSPCoordinator
from .entity import BoseCSPEntity

_LOGGER = logging.getLogger(__name__)

# Entities are updated from the coordinator; commands need no serialisation.
PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BoseCSPConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Bose CSP media player entities from a config entry."""
    data = entry.runtime_data
    coordinator = data.coordinator
    source_list = data.source_list
    min_db = data.min_db
    max_db = data.max_db

    zones_str = entry.data["zones"]
    zones_list = [zone.strip() for zone in zones_str.split(",")]

    zone_limits = entry.data.get("zone_limits", {})
    entities = []
    for zone_name in zones_list:
        limits = zone_limits.get(zone_name, {})
        z_min = limits.get("min_db", min_db)
        z_max = limits.get("max_db", max_db)
        entities.append(
            BoseCSPZone(coordinator, zone_name, source_list, z_min, z_max)
        )
    async_add_entities(entities)


class BoseCSPZone(BoseCSPEntity, MediaPlayerEntity):
    """Representation of a single Bose CSP Zone."""

    _attr_assumed_state = False
    _attr_supported_features = (
        MediaPlayerEntityFeature.VOLUME_SET
        | MediaPlayerEntityFeature.VOLUME_MUTE
        | MediaPlayerEntityFeature.SELECT_SOURCE
    )

    def __init__(
        self,
        coordinator: BoseCSPCoordinator,
        zone_name: str,
        source_list: list[str],
        min_db: float,
        max_db: float,
    ) -> None:
        """Initialize the zone entity."""
        super().__init__(coordinator, zone_name)
        self._attr_name = zone_name

        self._min_db = min_db
        self._max_db = max_db
        if (max_db - min_db) <= 0:
            self._db_range = 1.0
            _LOGGER.warning("Min/Max dB range is invalid, defaulting to 1.0")
        else:
            self._db_range = max_db - min_db

        self._attr_source_list = source_list

        self._source_mapping = coordinator.config_entry.data.get("source_mapping", {})
        self._reverse_source_mapping = {v: k for k, v in self._source_mapping.items()}

        # Set initial state from coordinator data
        self._sync_state_from_coordinator()

    def _sync_state_from_coordinator(self) -> None:
        """Synchronize entity state from coordinator data."""
        if self.coordinator.data is None:
            return

        zone_state = self.coordinator.data.get(self._zone_name)
        if zone_state is None:
            return

        # Volume: convert dB to 0.0-1.0 range
        vol_db = zone_state.volume
        clamped_db = max(self._min_db, min(vol_db, self._max_db))
        self._attr_volume_level = (clamped_db - self._min_db) / self._db_range

        # Mute
        self._attr_is_volume_muted = zone_state.is_muted

        # Source
        source_index = zone_state.current_source
        if self._reverse_source_mapping:
            self._attr_source = self._reverse_source_mapping.get(
                source_index, "Source %s" % source_index
            )
        else:
            list_index = source_index - 1
            if 0 <= list_index < len(self._attr_source_list):
                self._attr_source = self._attr_source_list[list_index]
            else:
                _LOGGER.warning(
                    "Device reported unknown source index: %s", source_index
                )
                self._attr_source = "Source %s" % source_index

        # AutoVolume: surface as an attribute. While On, the device controls the
        # level and rejects manual gain sets (the library no-ops them).
        self._attr_extra_state_attributes = {
            "auto_volume": zone_state.auto_volume
        }

        # State
        self._attr_state = MediaPlayerState.ON

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._sync_state_from_coordinator()
        super()._handle_coordinator_update()

    async def async_set_volume_level(self, volume: float) -> None:
        """Set volume level, range 0.0 to 1.0."""
        vol_db = (volume * self._db_range) + self._min_db
        try:
            await self.coordinator.device.set_volume(
                self._zone_name, round(vol_db, 1)
            )
        except BoseCSPCommandError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="set_volume_failed",
                translation_placeholders={
                    "zone": self._zone_name,
                    "error": str(err),
                },
            ) from err

    async def async_mute_volume(self, mute: bool) -> None:
        """Mute or unmute the volume."""
        try:
            await self.coordinator.device.set_mute(self._zone_name, mute)
        except BoseCSPCommandError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="set_mute_failed",
                translation_placeholders={
                    "zone": self._zone_name,
                    "error": str(err),
                },
            ) from err

    async def async_select_source(self, source: str) -> None:
        """Select input source."""
        if self._source_mapping:
            source_index = self._source_mapping.get(source)
            if source_index is None:
                _LOGGER.error("Invalid source name selected: %s", source)
                return
        else:
            try:
                list_index = self._attr_source_list.index(source)
            except ValueError:
                _LOGGER.error("Invalid source name selected: %s", source)
                return
            source_index = list_index + 1

        try:
            await self.coordinator.device.set_source(
                self._zone_name, source_index
            )
        except BoseCSPCommandError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="set_source_failed",
                translation_placeholders={
                    "zone": self._zone_name,
                    "error": str(err),
                },
            ) from err