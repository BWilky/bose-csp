"""Constants for the Bose CSP integration."""

DOMAIN = "bose_csp"

# Configuration Keys
CONF_ZONES = "zones"
CONF_SOURCES = "sources"
CONF_MIN_DB = "min_db"
CONF_MAX_DB = "max_db"
CONF_ZONE_LIMITS = "zone_limits"
CONF_SOURCE_MAPPING = "source_mapping"

CONF_VOLUME_INTERVAL = "volume_interval"
CONF_OTHER_INTERVAL = "other_interval"
CONF_RECONNECT_DELAY = "reconnect_delay"
CONF_HEALTHCHECK_ENABLED = "health_check_enabled"

DEFAULT_MIN_DB = -60.0
DEFAULT_MAX_DB = 12.0
DEFAULT_VOLUME_INTERVAL = 5
DEFAULT_OTHER_INTERVAL = 30
DEFAULT_RECONNECT_DELAY = 5
DEFAULT_HEALTHCHECK_ENABLED = True

# Seconds to let the device's network stack settle after WebSocket discovery
# before the coordinator opens its control session (single-session constraint).
SETTLE_DELAY_SECONDS = 2