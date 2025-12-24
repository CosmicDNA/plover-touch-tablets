import logging
import sys


def get_logger(name: str):
    log = logging.getLogger(f"plover.{name.lower()}")
    if not log.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(f"%(asctime)s [%(threadName)s] %(levelname)s: [{name}] %(message)s"))
        log.addHandler(handler)
    log.setLevel(logging.INFO)
    log.propagate = False

    return log
