from typing import Literal

import click

import _cli.cli_service as service
from _config.constants import DEFAULT_FOLDER

from _cli.utils import print_success, print_err, print_fail


@click.group()
def main():
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
@click.argument("folder", default=DEFAULT_FOLDER)
def init(folder: str):
    print_result(f"You aliot project is ready to go!", *service.make_init(folder))


@main.command()
@click.argument("name")
# @click.option("-o", "mode", is_flag=True, help="Specify what you want to make")
def new(name: str):
    success = print_result(
        f"Object {name!r} config created successfully", *service.make_obj_config(name)
    )
    if success is None:
        return

    print_result(f"Object {name!r} created successfully", *service.make_obj(name))
