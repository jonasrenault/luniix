import logging
from pathlib import Path
from typing import Annotated
from uuid import UUID

import typer
from rich.logging import RichHandler

from luniix.databases import LOGGER, DatabaseManager
from luniix.devices import Device, list_devices
from luniix.stories import Story

FORMAT = "%(message)s"
logging.basicConfig(
    level=logging.DEBUG,
    format=FORMAT,
    datefmt="[%X]",
    handlers=[RichHandler(markup=True)],
)

app = typer.Typer(no_args_is_help=True)


@app.command()
def list():
    """
    List devices.
    """
    LOGGER.info("Looking for devices...")
    devices = list_devices()
    if len(devices) == 0:
        LOGGER.info("No devices found.")
    else:
        LOGGER.info(f"Found {len(devices)} devices.")
        for device in devices:
            LOGGER.info(f"> {device}")


@app.command()
def info(
    mount_point: Annotated[
        Path | None,
        typer.Option(
            "--device", "-d", dir_okay=True, file_okay=False, help="Device mount point."
        ),
    ] = None,
):
    """
    Print information about a device.
    """
    if mount_point is None:
        LOGGER.info("Looking for devices...")
        devices = list_devices()
        if len(devices) == 0:
            LOGGER.info("No devices found.")
            return
        mount_point = devices[0]
        LOGGER.info(f"Using device {mount_point}")

    device = Device(mount_point)
    LOGGER.info(device)


@app.command()
def db(
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="List story names.")
    ] = False,
):
    """
    List stories in the database.
    """
    db = DatabaseManager()
    LOGGER.info(f"{len(db._db)} stories in database.")
    if verbose:
        LOGGER.info("\n".join([f"{key}: {Story(UUID(key)).name}" for key in db._db]))


if __name__ == "__main__":
    app()
