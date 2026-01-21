from pathlib import Path

from luniix.constants import ArchiveExt, ArchiveType
from luniix.stories import get_story_archive_type


def test_get_story_archive_type():
    assert (
        get_story_archive_type(Path(f"story{ArchiveExt.PLAIN.value}"))
        == ArchiveType.PLAIN
    )
    assert get_story_archive_type(Path(f"story{ArchiveExt.V2.value}")) == ArchiveType.V2
    assert get_story_archive_type(Path(f"story{ArchiveExt.V3.value}")) == ArchiveType.V3
    assert get_story_archive_type(Path(f"story{ArchiveExt.ZIP.value}")) == ArchiveType.ZIP
    assert (
        get_story_archive_type(Path(f"story{ArchiveExt.SEVENZ.value}"))
        == ArchiveType.SEVENZ
    )
    assert get_story_archive_type(Path("story.unknown_extension")) == ArchiveType.UNKNOWN
