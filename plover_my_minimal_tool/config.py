from plover_my_minimal_tool.debug import is_debug_mode

if is_debug_mode():
    PROTOCOL = "http:"
    BASE_WORKER_URL = "localhost:8787"
else:
    PROTOCOL = "https:"
    BASE_WORKER_URL = "relay.stenography.cosmicdna.co.uk"

SESSION_SLUG = "session"
INITIATE_SLUG = "initiate"
CONNECT_SLUG = "connect"
JOIN_SLUG = "join"
TOKEN_PARAM = "token"  # nosec B105
