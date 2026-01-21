import json
from pathlib import Path
from unittest.mock import mock_open, patch

from luniix.databases import DatabaseManager, load_db


def test_db_manager_is_singleton():
    with patch.object(DatabaseManager, "_load_db") as mock_load:
        db1 = DatabaseManager()
        db2 = DatabaseManager()
        assert db1 is db2
        assert mock_load.call_count == 1


def test_load_db():
    STORIES = {
        "8706e558-5b12-4138-a963-098e11c42997": {
            "uuid": "8706e558-5b12-4138-a963-098e11c42997",
            "title": "L'agent Jean",
        },
        "f37080ac-25d1-43e1-8365-04c97c74848d": {
            "uuid": "f37080ac-25d1-43e1-8365-04c97c74848d",
            "title": "Bébé Louis - Volume 1",
        },
    }
    m = mock_open(read_data=json.dumps(STORIES))

    file = Path(__file__)
    official = True
    with patch("builtins.open", m):
        db = load_db(file, official)

    m.assert_called_once_with(file, "r")
    assert len(db) == 2
    for key in STORIES.keys():
        assert key in db
        assert db[key]["title"] == STORIES[key]["title"]

    for story in db.values():
        assert story["official"] == official
