from pathlib import Path


def reverse_bytes(input_bytes: bytes) -> bytes:
    if len(input_bytes) % 4 != 0:
        raise ValueError("Input buffer must be modulo 4")

    groups_of_4 = [input_bytes[i : i + 4] for i in range(0, len(input_bytes), 4)]
    reversed_groups = [group[::-1] for group in groups_of_4]
    final_key = b"".join(reversed_groups)

    return final_key


def fetch_keys(keyfile: Path) -> tuple[bytes, bytes]:
    if not keyfile.is_file():
        raise FileNotFoundError(f"Keyfile '{keyfile}' not found")

    with open(keyfile, "rb") as fk:
        key = reverse_bytes(fk.read(0x10))
        iv = reverse_bytes(fk.read(0x10))

    return key, iv
