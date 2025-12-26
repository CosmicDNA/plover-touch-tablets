"""Server configuration."""

from json import dump, load
from pathlib import Path

from nacl.encoding import HexEncoder
from nacl.public import PrivateKey
from nacl_middleware import Nacl
from plover import log
from plover.oslayer.config import CONFIG_DIR


class ClientConfig:
    """Loads server configuration.

    Attributes:
        host: The host address for the server to run on.
        port: The port for the server to run on.

    """

    public_key: str
    public_key: str

    def __init__(self, client_config_file: str) -> None:
        """Initialize the server configuration object.

        Args:
            client_config_file: The file path of the configuration file to load.

        Raises:
            IOError: Errored when loading the server configuration file.

        """
        # Try to load from the other plugin's config file first (read-only)
        other_config_path = Path(CONFIG_DIR) / client_config_file
        data = {}
        keys_found = False

        if other_config_path.exists():
            try:
                with other_config_path.open(encoding="utf-8") as config_file:
                    other_data = load(config_file)
                    if "private_key" in other_data and "public_key" in other_data:
                        data = other_data
                        keys_found = True
                        log.debug(f"Loaded keys from {other_config_path}")
            except Exception as e:
                log.warning(f"Error reading {other_config_path}: {e}")

        # If not found, use our own config file
        if not keys_found:
            my_config_path = Path(CONFIG_DIR) / "plover_my_minimal_tool.json"
            if my_config_path.exists():
                try:
                    with my_config_path.open(encoding="utf-8") as config_file:
                        data = load(config_file)
                        if "private_key" in data and "public_key" in data:
                            keys_found = True
                            log.debug(f"Loaded keys from {my_config_path}")
                except Exception as e:
                    log.warning(f"Error reading {my_config_path}: {e}")

            if not keys_found:
                log.info("No existing keys found. Generating new keys...")
                nacl_helper = Nacl()
                data["private_key"] = nacl_helper.decoded_private_key()
                data["public_key"] = nacl_helper.decoded_public_key()

                log.info(f"Saving new keys to {my_config_path}")
                with my_config_path.open("w", encoding="utf-8") as config_file:
                    dump(data, config_file, indent=2)

        # Assign values to class attributes
        self.ssl = data.get("ssl")
        self.private_key = PrivateKey(data["private_key"], HexEncoder)
        self.public_key = data["public_key"]
