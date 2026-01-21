from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

import requests

from luniix.constants import CACHE_DIR, LUNII_DATA_URL
from luniix.databases import DatabaseManager

STORY_UNKNOWN = "Unknown story (maybe a User created story)..."
DESC_NOT_FOUND = "No description found."

LOGGER = logging.getLogger(__name__)


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

    def __hash__(self) -> int:
        return hash(self.uuid)


def download_story_image(story: Story, force: bool = False):
    story_image_file = CACHE_DIR / str(story.uuid)
    if story_image_file.is_file() and not force:
        LOGGER.debug(
            f"Story image already exists at {story_image_file}. Not downloading."
        )
        return

    if not story.db_story.get("locales_available") or not story.db_story.get(
        "localized_infos"
    ):
        LOGGER.debug(
            f"Story {story.uuid} has no localized infos. Skipping image download."
        )

    locale = list(story.db_story["locales_available"].keys())[0]
    image = story.db_story["localized_infos"][locale].get("image")
    if not image or "image_url" not in image:
        LOGGER.debug(f"Story {story.uuid} has no image URL. Skipping image download.")
        return

    image_url = LUNII_DATA_URL + image["image_url"]
    try:
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        with open(story_image_file, "wb") as f:
            f.write(response.content)
    except (
        requests.exceptions.Timeout,
        requests.exceptions.RequestException,
        requests.exceptions.ConnectionError,
        requests.exceptions.HTTPError,
    ):
        LOGGER.error(f"Failed to download story image for {story.uuid}", exc_info=True)
