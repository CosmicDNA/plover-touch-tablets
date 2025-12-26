import logging

plover_logger = logging.getLogger("plover")


def is_debug_mode():
    return plover_logger.isEnabledFor(logging.DEBUG)
