"""Constants for the Bose CSP integration."""

DOMAIN = "bose_csp"

# Configuration Keys
CONF_ZONES = "zones"
CONF_SOURCES = "sources"
CONF_MIN_DB = "min_db"
CONF_MAX_DB = "max_db"

CONF_VOLUME_INTERVAL = "volume_interval"
CONF_OTHER_INTERVAL = "other_interval"
CONF_RECONNECT_DELAY = "reconnect_delay"
CONF_HEALTHCHECK_ENABLED = "health_check_enabled"

DEFAULT_VOLUME_INTERVAL = 5
DEFAULT_OTHER_INTERVAL = 30
DEFAULT_RECONNECT_DELAY = 5
DEFAULT_HEALTHCHECK_ENABLED = True