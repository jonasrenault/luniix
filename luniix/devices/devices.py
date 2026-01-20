import logging
import platform
from pathlib import Path

import psutil

LOGGER = logging.getLogger(__name__)


def is_device(drive_path: Path) -> bool:
    """
    Check if the given drive path is a Lunii device.

    Args:
        drive_path (Path): The path to the drive to check.

    Returns:
        bool: True if the drive is a Lunii device, False otherwise.
    """
    try:
        if drive_path.joinpath(".md").is_file():
            return True
    except PermissionError:
        pass

    try:
        if drive_path.joinpath(".mdf").is_file():
            return True
    except PermissionError:
        pass
    return False


def list_devices() -> list[Path]:
    devices: list[Path] = []
    current_os = platform.system()
    if current_os == "Windows":
        # check all drive letters
        for drive in range(ord("A"), ord("Z") + 1):
            dev_path = Path(f"{chr(drive)}:/")
            if is_device(dev_path):
                LOGGER.debug(f"Device found at {dev_path}.")
                devices.append(dev_path)
    elif current_os == "Linux":
        # Iterate through all partitions
        for part in psutil.disk_partitions():
            if part.device.startswith("/dev/sd") and (
                part.fstype.startswith("msdos") or part.fstype == "vfat"
            ):
                dev_path = Path(part.mountpoint)
                if is_device(dev_path):
                    LOGGER.debug(f"Device found at {dev_path}.")
                    devices.append(dev_path)
    elif current_os == "Darwin":
        # Iterate through all partitions
        for part in psutil.disk_partitions():
            if any(
                part.mountpoint.lower().startswith(mnt_pt)
                for mnt_pt in ["/mnt", "/media", "/volume"]
            ) and (part.fstype.startswith("msdos") or part.fstype == "vfat"):
                dev_path = Path(part.mountpoint)
                if is_device(dev_path):
                    LOGGER.debug(f"Device found at {dev_path}.")
                    devices.append(dev_path)
    else:
        raise NotImplementedError(f"Unsupported OS: {current_os}")

    return devices
