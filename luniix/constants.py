from enum import Enum, StrEnum
from pathlib import Path


def vectkey_to_bytes(key_vect: list[int]) -> bytes:
    joined = [k.to_bytes(4, "little") for k in key_vect]
    return b"".join(joined)


def lunii_tea_rounds(buffer):
    return int(1 + 52 / (len(buffer) / 4))


# external flash hardcoded value
# 91BD7A0A A75440A9 BBD49D6C E0DCC0E3
RAW_KEY_GENERIC: list[int] = [0x91BD7A0A, 0xA75440A9, 0xBBD49D6C, 0xE0DCC0E3]
LUNII_GENERIC_KEY = vectkey_to_bytes(RAW_KEY_GENERIC)

OFFICIAL_TOKEN_URL = "https://server-auth-prod.lunii.com/guest/create"
OFFICIAL_DB_URL = "https://server-data-prod.lunii.com/v2/packs"
THIRD_PARTY_DB_URL = (
    "https://github.com/jonasrenault/luniix/releases/download/v0.1.0/third-party.json"
)
LUNII_DATA_URL = "https://storage.googleapis.com/lunii-data-prod"

CFG_DIR: Path = Path.home() / ".luniix"
CACHE_DIR = CFG_DIR / "cache"
FILE_OFFICIAL_DB = CFG_DIR / "official.json"
FILE_THIRD_PARTY_DB = CFG_DIR / "third-party.json"
V3_KEYS = CFG_DIR / "v3.keys"

FAH_V1_USB_VID_PID = (0x0C45, 0x6820)
FAH_V1_FW_2_USB_VID_PID = (0x0C45, 0x6840)
FAH_V2_V3_USB_VID_PID = (0x0483, 0xA341)
FLAM_USB_VID_PID = (0x303A, 0x819E)


class DeviceType(int, Enum):
    UNKNOWN = 255
    LUNII_V1or2 = 0
    LUNII_V1 = 1
    LUNII_V2 = 2
    LUNII_V3 = 3
    FLAM_V1 = 10


class ArchiveType(StrEnum):
    UNKNOWN = "unknown"
    PLAIN = "plain"
    V2 = "v2"
    V3 = "v3"
    ZIP = "zip"
    SEVENZ = "7z"
    STUDIO_ZIP = "studio_zip"
    STUDIO_7Z = "studio_7z"
    FLAM_ZIP = "flam_zip"
    FLAM_7Z = "flam_7z"


class ArchiveExt(StrEnum):
    PLAIN = ".plain.pk"
    V2 = ".v2.pk"
    V3 = ".v3.pk"
    VX = ".pk"
    ZIP = ".zip"
    SEVENZ = ".7z"
