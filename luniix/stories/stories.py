from __future__ import annotations

from typing import Any
from uuid import UUID

from luniix.databases import DatabaseManager

STORY_UNKNOWN = "Unknown story (maybe a User created story)..."
DESC_NOT_FOUND = "No description found."


class Story:
    def __init__(self, uuid: UUID, hidden: bool = False, size: int = -1):
        self.uuid = uuid
        self.size = size
        self.hidden = hidden

    @property
    def short_uuid(self):
        return self.uuid.hex[24:]

    @property
    def db_story(self):
        return DatabaseManager().get(str(self.uuid))

    @property
    def name(self):
        if self.db_story:
            if self.db_story.get("locales_available") and self.db_story.get(
                "localized_infos"
            ):
                locale = list(self.db_story["locales_available"].keys())[0]
                title = self.db_story["localized_infos"][locale].get("title")
                return title
            else:
                return self.db_story.get("title", STORY_UNKNOWN)

        return STORY_UNKNOWN

    @property
    def desc(self):
        if self.db_story:
            if self.db_story.get("locales_available") and self.db_story.get(
                "localized_infos"
            ):
                locale = list(self.db_story["locales_available"].keys())[0]
                description = self.db_story["localized_infos"][locale].get("description")
                return description
            else:
                return self.db_story.get("description", DESC_NOT_FOUND)

        return DESC_NOT_FOUND

    def is_official(self):
        return self.db_story.get("official", False)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Story):
            return False
        return self.uuid == other.uuid
