import json
import sys

import click
import requests
from subprocess import Popen
import os

import aliot.core._cli.cli_service as service
from aliot.core._config.constants import DEFAULT_FOLDER, CHECK_FOR_UPDATE_URL, CONFIG_FILE_NAME, \
    DEFAULT_CONFIG_FILE_PATH

from aliot.core._cli.utils import print_success, print_err, print_fail


@click.group()
def main():
    # response = requests.get(CHECK_FOR_UPDATE_URL)
    # if response.status_code != 200:
    #     return
    # try:
    #     content = response.json()
    # except json.JSONDecodeError:
    #     return
    # latest_version = content.get("latest", None) or content.get("versions", [None])[-1]
    # if latest_version is None:
    #     return
    # TODO finish the "auto-check for update" system
    pass


def print_result(success_msg: str, success: bool | None, err_msg: str) -> bool | None:
    if success:
        print_success(success_msg)
    elif success is None:
        print_err(err_msg)
    else:
        print_fail(err_msg)

    return success


@main.command()
@click.argument("folder", default=".")
def init(folder: str):
    print_result(f"Your aliot project is ready to go!", *service.make_init(folder))


@main.command()
@click.argument("object-name")
# @click.option("-o", "mode", is_flag=True, help="Specify what you want to make")
def new(object_name: str):
    # TODO add --main to change the main value in the config.ini
    # TODO add --obj-id to change the value of the obj_id in the config.ini
    success = print_result(
        f"Object {object_name!r} config created successfully", *service.make_obj_config(object_name)
    )
    if success is None:
        return

    print_result(f"Object {object_name!r} created successfully", *service.make_obj(object_name))


@main.command()
@click.argument("object-name")
def run(object_name: str):
    if not os.path.exists(DEFAULT_CONFIG_FILE_PATH):
        print_err(f"Could not find config file at {DEFAULT_CONFIG_FILE_PATH!r} (try running `aliot init`)")

    obj_main = service.get_config(DEFAULT_CONFIG_FILE_PATH).get(object_name, "main",
                                                                fallback=f"{object_name}.py")
    obj_dir_path = f"{DEFAULT_FOLDER}/{object_name}"

    if not os.path.exists(obj_dir_path):
        print_err(
            f"The object {object_name!r} doesn't exist (at path {obj_dir_path!r}). "
            f"Make sure you wrote it correctly or create it using the"
            f" `aliot new` command."
        )
        return

    obj_path = f"{obj_dir_path}/{obj_main}"

    if not os.path.exists(obj_path):
        print_err(
            f"The main file of the object {object_name!r} doesn't exist (at path {obj_path!r}). "
            f"In your {CONFIG_FILE_NAME!r} file, you specified the main as {obj_main!r}. Make sure to create it "
            f"or change the value of the field in the {CONFIG_FILE_NAME!r} file to suit your needs."
        )

    Popen([sys.executable, obj_path]).communicate()


@main.group()
def check():
    """Group of commands to check the status of the aliot"""


@check.command(name="iot")
@click.option("--name", default=None)
def objects(name: str):
    """Look up all (or one) objects' id in the config.ini and validate them with the server"""
    if name is None:
        """Validate all the objects"""
    else:
        """Validate only the object with the name"""


@main.command()
@click.argument("name", default=None)
def update():
    """Update aliot with the latest version"""
