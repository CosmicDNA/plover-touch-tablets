# from plover_touch_tablets.debug import is_debug_mode

# if is_debug_mode():
#     PROTOCOL = "http:"
#     BASE_WORKER_URL = "localhost:8787"

WORKER_PROTOCOL = "https:"
BASE_WORKER_FQDN = "relay.stenography.cosmicdna.co.uk"
APP_URL = "https://touch.stenography.cosmicdna.co.uk"

SESSION_SLUG = "session"
INITIATE_SLUG = "initiate"
CONNECT_SLUG = "connect"
JOIN_SLUG = "join"
TOKEN_PARAM = "token"  # nosec B105
RELAY_PARAM = "relay"
