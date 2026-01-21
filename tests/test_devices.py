from pathlib import Path
from unittest.mock import patch

import pytest

from luniix.devices import Device


def test_new_device_with_invalid_mount_point_raises_exception():
    mock_mount_point = Path("/non/existent/path")

    with pytest.raises(
        RuntimeError, match="Device /non/existent/path is an unknown device type."
    ):
        Device(mock_mount_point)


@patch("luniix.devices.Device.is_lunii", return_value=True)
@patch("luniix.devices.Device._parse_metadata")
def test_device_can_be_created(mock_parse_metadata, mock_is_lunii):
    mock_mount_point = Path("/mock/mount/point")

    device = Device(mock_mount_point)

    assert device.mount_point == mock_mount_point
    assert device.is_lunii() is True
    assert mock_parse_metadata.call_count == 1
