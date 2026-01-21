import json
import logging
from pathlib import Path
from typing import Any

import requests

from luniix.constants import (
    CFG_DIR,
    FILE_OFFICIAL_DB,
    FILE_THIRD_PARTY_DB,
    OFFICIAL_DB_URL,
    OFFICIAL_TOKEN_URL,
    THIRD_PARTY_DB_URL,
)

LOGGER = logging.getLogger(__name__)


class DatabaseManager:
    """
    Singleton class to manage a stories database.
    """

    _instance = None

    def __new__(cls) -> "DatabaseManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # Mark that __init__ hasn't run yet
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        # Prevent re‑initialisation on subsequent calls
        if self._initialized:
            return
        self._initialized = True

        # Placeholder for an actual DB connection object
        self.connection: Any = None

    # --------------------------------------------------------------------- #
    # Public API
    # --------------------------------------------------------------------- #
    def connect(self, uri: str) -> None:
        """
        Establish a connection to the database.

        Parameters
        ----------
        uri: str
            Database connection string/URL.
        """
        if self.connection is None:
            # In a real implementation you would create a DB engine/connection here.
            # For now we just store the URI as a placeholder.
            self.connection = uri

    def execute_query(self, query: str) -> Any:
        """
        Execute a query against the connected database.

        Parameters
        ----------
        query: str
            The SQL (or NoSQL) query to run.

        Returns
        -------
        Any
            The result of the query.  This stub returns a simple string.
        """
        if self.connection is None:
            raise RuntimeError(
                "Database connection not established. Call `connect` first."
            )
        # Stub implementation; replace with real query execution logic.
        return f"Executed query: {query}"

    def close(self) -> None:
        """Close the database connection (stub)."""
        self.connection = None


def load_db(db_path: Path) -> dict[str, Any]:
    """
    Load a database from a file.

    Args:
        db_path (Path): The path to the database file.

    Returns:
        dict[str, Any]: The loaded database.
    """
    if not db_path.is_file():
        LOGGER.error(f"Database file not found at {db_path}. Unable to load.")
        return {}

    with open(db_path, "r") as f:
        data = json.load(f)

    return data


def download_official_db(force: bool = False):
    """
    Download the official database from Lunii's servers.

    Args:
        force (bool): If True, force download even if the file already exists.
    """
    if FILE_OFFICIAL_DB.is_file() and not force:
        LOGGER.info(
            f"Official database already exists at {FILE_OFFICIAL_DB}. Not downloading."
        )
        return

    # Create CFG dir if needed
    CFG_DIR.mkdir(parents=True, exist_ok=True)

    try:
        LOGGER.info(f"Downloading official database to {FILE_OFFICIAL_DB}.")
        # Fetch auth token
        token_response = requests.get(OFFICIAL_TOKEN_URL)
        token_response.raise_for_status()
        auth_token = token_response.json()["response"]["token"]["server"]
        req_headers = {
            "Application-Sender": "luniistore_desktop",
            "Accept": "application/json",
            "X-AUTH-TOKEN": auth_token,
        }

        db_response = requests.get(OFFICIAL_DB_URL, headers=req_headers, timeout=30)
        db_response.raise_for_status()
        db = db_response.json()["response"]
        db = {db[key]["uuid"]: value for (key, value) in db.items()}

        with open(FILE_OFFICIAL_DB, "w") as fp:
            json.dump(db, fp)
    except (
        requests.exceptions.Timeout,
        requests.exceptions.RequestException,
        requests.exceptions.ConnectionError,
        requests.exceptions.HTTPError,
    ):
        LOGGER.error("Failed to download official database.", exc_info=True)


def download_third_party_db(force: bool = False):
    """
    Download the unofficial database from Lunii's servers.

    Args:
        force (bool): If True, force download even if the file already exists.
    """
    if FILE_THIRD_PARTY_DB.is_file() and not force:
        LOGGER.info(
            f"Third-party database already exists at {FILE_THIRD_PARTY_DB}. "
            "Not downloading."
        )
        return

    # Create CFG dir if needed
    CFG_DIR.mkdir(parents=True, exist_ok=True)

    try:
        LOGGER.info(f"Downloading third-party database to {FILE_THIRD_PARTY_DB}.")

        db_response = requests.get(THIRD_PARTY_DB_URL, timeout=30)
        db_response.raise_for_status()
        db = db_response.json()["response"]

        with open(FILE_THIRD_PARTY_DB, "w") as fp:
            json.dump(db, fp)
    except (
        requests.exceptions.Timeout,
        requests.exceptions.RequestException,
        requests.exceptions.ConnectionError,
        requests.exceptions.HTTPError,
    ):
        LOGGER.error("Failed to download third-party database.", exc_info=True)
