import sqlite3
import time
import math
from contextlib import contextmanager


@contextmanager
def sqlite_execute(db_path, q, params=()):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor = conn.cursor()
        cursor.execute(q, params)
        conn.commit()
        yield cursor
    finally:
        cursor.close()
        conn.close()


class SqliteStore(object):
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._schema_migrations = {
            0: self._migrate_0_to_1
        }
        self._migrate_schema()
    
    def append_event(self, event_type: str, event_host: str):
        timestamp = math.floor(time.time() * 1000)
        with sqlite_execute(self.db_path,
                            "INSERT INTO events (timestamp, event_type, event_host) VALUES(?, ?, ?)",
                            (timestamp, event_type, event_host)
                            ):
            pass

    def _migrate_schema(self):
        schema_version = self._get_schema_version()
        latest_schema_version = max(self._schema_migrations.keys()) + 1
        if schema_version == latest_schema_version:
            print(f"Already on latest schema version {latest_schema_version}")
            return
        migrate_versions = [i for i in range(schema_version, latest_schema_version)]
        for v in migrate_versions:
            if v not in self._schema_migrations:
                raise RuntimeError(f'Schema migration for version {v} is undefined')
        for v in migrate_versions:
            self._schema_migrations[v]()
        self._update_schema_version(latest_schema_version)

    def _migrate_0_to_1(self):
        for statement in [
            'CREATE TABLE schema_version (v INTEGER)',
            'INSERT INTO schema_version (v) VALUES(1)',
            'CREATE TABLE events (timestamp INTEGER, event_type TEXT, event_host TEXT)'
        ]:
            with sqlite_execute(self.db_path, statement):
                pass

    def _get_schema_version(self) -> int:
        if not self._if_schema_version_exists():
            return 0
        with sqlite_execute(self.db_path, 'SELECT v FROM schema_version') as cursor:
            result = cursor.fetchone()
            return result[0]

    def _if_schema_version_exists(self) -> bool:
        with sqlite_execute(self.db_path, 'PRAGMA table_info(schema_version)') as cursor:
            results = cursor.fetchall()
            return len(results) != 0

    def _update_schema_version(self, v: int):
        with sqlite_execute(self.db_path, 'UPDATE schema_version SET v = ?', (v,)):
            pass
