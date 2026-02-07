# from plover_my_minimal_tool.debug import is_debug_mode

# if is_debug_mode():
#     PROTOCOL = "http:"
#     BASE_WORKER_URL = "localhost:8787"

#     # From cloudflared tunnel
#     INGRESS_PROTOCOL = "https:"
#     INGRESS_BASE_WORKER_URL = "compromise-rhythm-austin-growing.trycloudflare.com"

#     # PROTOCOL = "https:"
#     # BASE_WORKER_URL = "relay.stenography.cosmicdna.co.uk"
# else:
#     PROTOCOL = "https:"
#     BASE_WORKER_URL = "relay.stenography.cosmicdna.co.uk"

#     INGRESS_PROTOCOL = PROTOCOL
#     INGRESS_BASE_WORKER_URL = BASE_WORKER_URL

PROTOCOL = "https:"
BASE_WORKER_URL = "relay.stenography.cosmicdna.co.uk"

INGRESS_PROTOCOL = PROTOCOL
INGRESS_BASE_WORKER_URL = BASE_WORKER_URL

SESSION_SLUG = "session"
INITIATE_SLUG = "initiate"
CONNECT_SLUG = "connect"
JOIN_SLUG = "join"
TOKEN_PARAM = "token"  # nosec B105
