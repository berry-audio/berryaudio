import sqlite3
import pathlib
import logging
import json

from pathlib import Path

logger = logging.getLogger(__name__)

DB_FILENAME = "library.db"
DB_PATH = "/home/pi/berryaudio/db/core"
SCHEMA_INIT_SQL = """
        CREATE TABLE IF NOT EXISTS extensions (
            name TEXT PRIMARY KEY,
            config TEXT NOT NULL
        )
    """


class AttrRow(dict):
    """Dict subclass that allows attribute-style access: row.key"""

    __getattr__ = dict.get


def dict_factory(cursor, row):
    """Factory to build AttrRow objects for sqlite3."""
    d = AttrRow()
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


class DBConnection:
    _instance = None

    def __new__(cls, db_file=DB_FILENAME):
        if cls._instance is None:
            cls._instance = super().__new__(cls)

            config_dir = Path(__file__).parent.parent / "core" / "db"
            config_dir.mkdir(parents=True, exist_ok=True)
            db_path = config_dir / db_file

            conn = sqlite3.connect(db_path, check_same_thread=False)
            conn.execute("PRAGMA foreign_keys=ON;")
            conn.row_factory = dict_factory

            cls._instance.conn = conn
            cls._instance.init_db()

        return cls._instance

    def init_db(self):
        self.executescript(SCHEMA_INIT_SQL)
        logger.debug(f"Database initialised")

    def execute(self, query, params=()):
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        self.conn.commit()
        return cursor

    def executescript(self, script: str, params=None):
        cursor = self.conn.cursor()
        if params is None:
            cursor.executescript(script)
        else:
            cursor.execute(script, params)
        self.conn.commit()
        return cursor

    def executemany(self, sql: str, params: list[dict]):
        cursor = self.conn.cursor()
        cursor.executemany(sql, params)
        self.conn.commit()
        return cursor

    def fetchall(self, query, params=()):
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()

    def fetchone(self, query, params=()):
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchone()

    def close(self):
        if hasattr(self, "conn") and self.conn:
            self.conn.close()
            self.__class__._instance = None
            logger.info("Database connection closed.")

    def init_extension(self, name, config):
        sql = "INSERT OR IGNORE INTO extensions (name, config) VALUES (?, ?)"
        params = (name, json.dumps(config))
        self.execute(sql, params)
        logger.debug(f"Initialized extension {name} in database")
        return True

    def get_config(self):
        rows = self.fetchall("SELECT * FROM extensions")
        if not rows:
            return {}
        result = {}
        for row in rows:
            ext_config = json.loads(row["config"])
            result[row.name] = ext_config

        return result

    def set_config(self, config):
        if not config:
            raise ValueError(f"Empty config not allowed")

        _configs = self.get_config()

        for ext_name in config:
            if ext_name not in _configs:
                raise ValueError(f"No config found for extension {ext_name}")

            ext_config = _configs[ext_name]

            _keys = [key for key in config[ext_name].keys() if key not in ext_config]

            if _keys:
                raise ValueError(f"Unknown config for extension {ext_name}: {_keys}")

            for k, v in config[ext_name].items():
                ext_config[k] = v

            sql = "UPDATE extensions SET config = ? WHERE name = ?"
            params = (json.dumps(ext_config), ext_name)
            self.execute(sql, params)
        return True
