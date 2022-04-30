import os.path
from configparser import DuplicateSectionError
from typing import TypeAlias

from aliot.core._config.constants import CONFIG_FILE_NAME, DEFAULT_FOLDER
from aliot.core._config.config import update_config, config_init, get_config

result: TypeAlias = tuple[bool | None, str | None]


def make_init(folder: str) -> result:
    """Makes the _config.ini"""
    os.makedirs(folder, exist_ok=True)
    path = f"{folder}/{CONFIG_FILE_NAME}"
    if os.path.exists(path):
        return False, "Config file already exists"
    try:
        config_init(path)
    except ValueError as e:
        return None, f"Could not create config file: {e!r}"
    return True, None


def make_obj(obj_name: str) -> result:
    path = f"{DEFAULT_FOLDER}/{obj_name}"
    if os.path.exists(path):
        return False, "Object already exists"
    variable = obj_name.replace('-', '_')
    try:
        os.makedirs(path, exist_ok=True)
        with open(f"{path}/{obj_name}.py", "w+") as f:
            f.write(
                f"""from aliot.aliot_obj import AliotObj

{variable} = AliotObj("{obj_name}")

# write your code here

{variable}.run()
""")
    except FileNotFoundError:
        return None, f"Could not create object script at {path!r}"

    return True, None


def make_obj_config(obj_name: str) -> result:
    config_path = f"{DEFAULT_FOLDER}/{CONFIG_FILE_NAME}"
    try:
        config = get_config(config_path)
        config.add_section(obj_name)
        config[obj_name]["obj_id"] = f"Paste the id of {obj_name} here :)"
        update_config(f"{DEFAULT_FOLDER}/{CONFIG_FILE_NAME}", config)
    except (ValueError, DuplicateSectionError) as e:
        return False, f"Could not update config file: {e!r}"
    except FileNotFoundError:
        return (
            None,
            f"Could not find config file at {config_path!r} (try running `aliot init)`",
        )

    return True, None
