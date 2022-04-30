import os.path
from configparser import ConfigParser

from aliot.core._config.constants import DEFAULT_CONFIG_FILE

__config: ConfigParser | None = None
__updated = False


def config_init(config_file_path: str = DEFAULT_CONFIG_FILE):
    update_config(config_file_path, get_default_config())


def get_default_config():
    config = ConfigParser()
    config["DEFAULT"]["ws_url"] = "wss://alivecode.ca/iotgateway/"
    config["DEFAULT"]["api_url"] = "https://alivecode.ca/api"
    return config


def update_config(config_file_path: str, config: ConfigParser):
    if config_file_path is None:
        raise ValueError("Config file path not set")

    with open(config_file_path, "w") as config_file:
        config.write(config_file)

    global __updated
    __updated = True


def get_config(config_file_path: str = DEFAULT_CONFIG_FILE) -> ConfigParser:
    if not os.path.exists(config_file_path):
        raise FileNotFoundError("Config file not found")
    global __config, __updated
    if __config is None or __updated:
        __config = ConfigParser()
        __config.read(config_file_path)
        __updated = False
    return __config
