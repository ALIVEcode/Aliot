from os import path
from pathlib import Path

CONFIG_FILE_NAME = "config.ini"


def __determine_default_folder() -> bool:
    current = Path(path.abspath("."))  # get current path
    if (current / CONFIG_FILE_NAME).exists():  # checks if the folder contains the config file
        return True
    return False


DEFAULT_FOLDER = "." if __determine_default_folder() else ".."

DEFAULT_CONFIG_FILE_PATH = path.join(DEFAULT_FOLDER, CONFIG_FILE_NAME)
CHECK_FOR_UPDATE_URL = "https://alivecode.ca/aliot/py/versions"
