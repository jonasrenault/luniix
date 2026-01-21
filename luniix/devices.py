import binascii
import logging
import platform
from io import BufferedReader
from pathlib import Path
from uuid import UUID

import psutil
import xxtea

from luniix.aes_keys import fetch_keys, reverse_bytes
from luniix.constants import (
    CFG_DIR,
    FAH_V1_FW_2_USB_VID_PID,
    FAH_V1_USB_VID_PID,
    FAH_V2_V3_USB_VID_PID,
    FLAM_USB_VID_PID,
    LUNII_GENERIC_KEY,
    DeviceType,
    lunii_tea_rounds,
)
from luniix.stories import Story

LOGGER = logging.getLogger(__name__)

FLAM_LIB_BASEDIR = "etc/library/"


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
    """
    List all Lunii devices connected to the system.

    Returns:
        list[Path]: A list of paths to Lunii devices.
    """
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


class Device:
    def __init__(self, mount_point: Path):
        self.mount_point = mount_point
        self.device_type = DeviceType.UNKNOWN
        self.device_key: bytes = b""
        self.device_iv: bytes = b""
        self.story_key: bytes = b""
        self.story_iv: bytes = b""
        self.snu: bytes = b""
        self.fw_main = "?.?.?"
        self.fw_comm = "?.?.?"
        self.fw_vers_major = 0
        self.fw_vers_minor = 0
        self.fw_vers_subminor = 0
        self.bt = b""
        self.stories: list[Story] = []

        self._parse_metadata()
        self._load_stories()

    @property
    def snu_str(self) -> str:
        return self.snu.hex().upper().lstrip("0")

    @property
    def snu_hex(self) -> bytes:
        return self.snu

    def is_lunii(self) -> bool:
        return self.mount_point.joinpath(".md").is_file()

    def is_flam(self) -> bool:
        return self.mount_point.joinpath(".mdf").is_file()

    @property
    def md_path(self) -> Path:
        if self.is_lunii():
            return self.mount_point.joinpath(".md")
        elif self.is_flam():
            return self.mount_point.joinpath(".mdf")
        else:
            raise RuntimeError(f"Device {self.mount_point} is an unknown device type.")

    def __repr__(self):
        if self.is_flam():
            repr_str = f"Flam Device at {self.mount_point}\n"
            repr_str += f"- Main firmware : v{self.fw_main}\n"
            repr_str += f"- Comm firmware : v{self.fw_comm}\n"
            repr_str += f"- SNU      : {binascii.hexlify(self.snu_hex, ' ')}\n"
        elif self.is_lunii():
            repr_str = f"Lunii device at {self.mount_point}\n"
            if self.device_type <= DeviceType.LUNII_V2:
                repr_str += f"- firmware : v{self.fw_vers_major}.{self.fw_vers_minor}\n"
            else:
                repr_str += (
                    f"- firmware : v{self.fw_vers_major}.{self.fw_vers_minor}"
                    f".{self.fw_vers_subminor}\n"
                )
            repr_str += f"- SNU      : {binascii.hexlify(self.snu_hex, ' ')}\n"
            repr_str += f"- dev key  : {binascii.hexlify(self.device_key, ' ')}\n"
            if self.device_type == DeviceType.LUNII_V3:
                repr_str += f"- dev iv   : {binascii.hexlify(self.device_iv, ' ')}\n"
                if self.story_key:
                    repr_str += f"- story key: {binascii.hexlify(self.story_key, ' ')}\n"
                if self.device_type == DeviceType.LUNII_V3:
                    repr_str += f"- story iv : {binascii.hexlify(self.story_iv, ' ')}\n"
        else:
            repr_str = "Unknown device type."
            return repr_str

        repr_str += f"- stories  : {len(self.stories)}\n"
        repr_str += "\n".join(
            [f"> {story.short_uuid} - {story.name}" for story in self.stories]
        )
        return repr_str

    def _parse_metadata(self):
        """
        Parse device metadata.
        """
        with open(self.md_path, "rb") as fp_md:
            md_version = int.from_bytes(fp_md.read(2), "little")

            if md_version >= 6:
                self.__md6toN_parse(fp_md)
            elif md_version >= 1:
                self.__md1to5_parse(fp_md)
            elif md_version == 1:
                self.__md1_parse(fp_md)
            else:
                raise RuntimeError(f"Unsupported MD version: {md_version}")

    def __md1_parse(self, fp_md: BufferedReader):
        """
        Parse MD1 format firmware metadata.

        Args:
            fp_md (BufferedReader): File pointer to the MD1 file.
        """
        fp_md.seek(2)

        # parsing firmware versions
        raw = fp_md.read(48)
        raw_str = raw.decode("utf-8").strip("\x00")
        raw_str = raw_str.replace("main: ", "").replace("comm: ", "")
        versions = raw_str.splitlines()

        self.fw_main = versions[0].split("-")[0]
        if len(versions) > 1:
            self.fw_comm = versions[1].split("-")[0]

        # parsing snu
        snu_str = fp_md.read(24).decode("utf-8").rstrip("\x00")
        self.snu = binascii.unhexlify(snu_str)

        # parsing VID/PID
        vid = int.from_bytes(fp_md.read(2), "little")
        pid = int.from_bytes(fp_md.read(2), "little")

        if (vid, pid) == FLAM_USB_VID_PID:
            self.device_type = DeviceType.FLAM_V1
        else:
            self.device_type = DeviceType.UNKNOWN

    def __md1to5_parse(self, fp_md: BufferedReader):
        """
        Parse MD1 to 5 firmware metadata.

        Args:
            fp_md (BufferedReader): File pointer to the metadata file.
        """
        fp_md.seek(6)
        self.fw_vers_major = int.from_bytes(fp_md.read(2), "little")
        self.fw_vers_minor = int.from_bytes(fp_md.read(2), "little")
        self.snu = fp_md.read(8)

        vid = int.from_bytes(fp_md.read(2), "little")
        pid = int.from_bytes(fp_md.read(2), "little")

        if (vid, pid) == FAH_V1_USB_VID_PID or (vid, pid) == FAH_V1_FW_2_USB_VID_PID:
            self.device_type = DeviceType.LUNII_V1
        elif (vid, pid) == FAH_V2_V3_USB_VID_PID:
            self.device_type = DeviceType.LUNII_V2
        else:
            self.device_type = DeviceType.LUNII_V1or2
        fp_md.seek(0x100)
        self.raw_devkey = fp_md.read(0x100)
        dec = xxtea.decrypt(
            self.raw_devkey,
            LUNII_GENERIC_KEY,
            padding=False,
            rounds=lunii_tea_rounds(self.raw_devkey),
        )
        # Reordering Key components
        self.device_key = dec[8:16] + dec[0:8]

    def __md6toN_parse(self, fp_md: BufferedReader):
        """
        Parse MD6 to N firmware metadata.

        Args:
            fp_md (BufferedReader): File pointer to the metadata file.
        """
        self.device_type = DeviceType.LUNII_V3
        # reading metadata version
        fp_md.seek(0)
        md_vers = int.from_bytes(fp_md.read(1))
        fp_md.seek(2)
        # reading fw version
        self.fw_vers_major = int.from_bytes(fp_md.read(1), "little") - 0x30
        fp_md.read(1)
        self.fw_vers_minor = int.from_bytes(fp_md.read(1), "little") - 0x30
        fp_md.read(1)
        self.fw_vers_subminor = int.from_bytes(fp_md.read(1), "little") - 0x30
        # reading SNU
        fp_md.seek(0x1A)
        self.snu = binascii.unhexlify(fp_md.read(14).decode("utf-8"))

        # getting candidated for story bt file
        fp_md.seek(0x40)
        if md_vers == 6:
            LOGGER.debug("Forging story keys for v6 metadata file")
            # forging bt file based on ciphered part of md
            self.bt = fp_md.read(0x20)
            # forging keys based on plain part of md (SNU x2)
            self.story_key = reverse_bytes(binascii.hexlify(self.snu) + b"\x00\x00")
            self.story_iv = reverse_bytes(
                b"\x00\x00\x00\x00\x00\x00\x00\x00" + binascii.hexlify(self.snu)[:8]
            )
        else:
            LOGGER.debug("Forging story keys for v7+ metadata file")
            # forging keys based on md ciphered part
            self.story_key = reverse_bytes(fp_md.read(0x10))
            self.story_iv = reverse_bytes(fp_md.read(0x10))
            # forging bt file based on plain part of md (SNU x2)
            self.bt = (
                binascii.hexlify(self.snu)
                + b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                + binascii.hexlify(self.snu)[:8]
            )

        # real keys if available
        dev_keyfile = CFG_DIR / f"{self.snu_str}.keys"
        try:
            self.device_key, self.device_iv = fetch_keys(dev_keyfile)
        except FileNotFoundError:
            pass

        vid, pid = FAH_V2_V3_USB_VID_PID

    def _load_stories(self):
        """
        Load stories from the device.
        """
        if self.is_lunii():
            stories_path = self.mount_point.joinpath(".pi")
            hidden_stories_path = self.mount_point.joinpath(".pi.hidden")
            stories = set(load_lunii_stories(stories_path, hidden=False))
            stories.update(load_lunii_stories(hidden_stories_path, hidden=True))
            self.stories = list(stories)
            LOGGER.info(f"Loaded {len(self.stories)} stories")

        elif self.is_flam():
            stories_path = self.mount_point.joinpath(FLAM_LIB_BASEDIR + "list")
            hidden_stories_path = self.mount_point.joinpath(
                FLAM_LIB_BASEDIR + "list.hidden"
            )
            stories = set(load_flam_stories(stories_path, hidden=False))
            stories.update(load_flam_stories(hidden_stories_path, hidden=True))
            self.stories = list(stories)
            LOGGER.info(f"Loaded {len(self.stories)} stories")


def load_flam_stories(file_path: Path, hidden: bool = False) -> list[Story]:
    """
    Load stories from a Flam device.

    Args:
        file_path (Path): The path to the stories file.
        hidden (bool): Whether to load hidden stories.

    Returns:
        list[Story]: The list of stories.
    """
    if not file_path.is_file():
        LOGGER.error(
            f"Stories directory {file_path} does not exist. Not loading stories."
        )
        return []

    with open(file_path, "r") as f:
        ids = f.readlines()
        stories = [Story(UUID(id.strip()), hidden=hidden) for id in ids]
        return stories


def load_lunii_stories(file_path: Path, hidden: bool = False) -> list[Story]:
    """
    Load stories from a Lunii device.

    Args:
        file_path (Path): The path to the stories file.
        hidden (bool): Whether to load hidden stories.

    Returns:
        list[Story]: The list of stories.
    """
    if not file_path.is_file():
        LOGGER.error(
            f"Stories directory {file_path} does not exist. Not loading stories."
        )
        return []

    with open(file_path, "rb") as f:
        stories = [
            Story(UUID(bytes=id), hidden=hidden) for id in iter(lambda: f.read(16), b"")
        ]
        return stories
