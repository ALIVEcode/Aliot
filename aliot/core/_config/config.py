import os.path
from configparser import ConfigParser
from typing import Literal

from aliot.core._config.constants import DEFAULT_CONFIG_FILE_PATH

__config: ConfigParser | None = None
__updated = False


def config_init(config_file_path: str = DEFAULT_CONFIG_FILE_PATH):
    update_config(config_file_path, get_config_default())


def get_config_default():
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


def get_config(config_file_path: str = DEFAULT_CONFIG_FILE_PATH) -> ConfigParser:
    if not os.path.exists(config_file_path):
        raise FileNotFoundError("Config file not found")
    global __config, __updated
    if __config is None or __updated:
        __config = ConfigParser()
        success = __config.read(config_file_path) != []
        if not success:
            raise IOError(f"Cannot read {config_file_path}")
        __updated = False
    return __config


def make_config_section(obj_name: str):
    return {
        "obj_id": f"Paste the id of {obj_name} here :)",
        "main": f"{obj_name}.py"
    }


def get_default_code(obj_name: str) -> str:
    variable = obj_name.replace('-', '_')

    return f"""from aliot.aliot_obj import AliotObj

{variable} = AliotObj("{obj_name}")

# write your code here

{variable}.run()
"""
