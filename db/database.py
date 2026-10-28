"""Подключение к SQLite и чтение именованных SQL-запросов."""

import sqlite3
from functools import lru_cache
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
DB_PATH = ROOT_DIR / "data" / "fleet.sqlite"
SCHEMA_PATH = ROOT_DIR / "sql" / "schema.sql"
QUERIES_PATH = ROOT_DIR / "sql" / "queries.sql"
MAX_SQLITE_INTEGER = 2**63 - 1


def get_connection(path: Path = DB_PATH, *,
                   write: bool = False) -> sqlite3.Connection:
    """Открыть базу с именованными строками и проверкой внешних ключей."""
    if write:
        conn = sqlite3.connect(path)
    else:
        conn = sqlite3.connect(path.absolute().as_uri() + "?mode=ro", uri=True)
    try:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
    except sqlite3.Error:
        conn.close()
        raise
    return conn


@lru_cache(maxsize=1)
def load_queries() -> dict[str, str]:
    """Прочитать блоки, начинающиеся с комментария -- name: имя."""
    sql = QUERIES_PATH.read_text(encoding="utf-8")
    queries = {}
    for section in sql.split("-- name: ")[1:]:
        name, _, statement = section.partition("\n")
        queries[name.strip()] = statement.strip()
    return queries
