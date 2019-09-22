import sqlite3
from multiprocessing import Lock
from .ping import Ping
from .time_entry import TimeEntry
from typing import List
from contextlib import contextmanager
from utils.time import now_milliseconds


@contextmanager
def sqlite_execute(conn, q, params=()):
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
        self.pings = []  # type: List[Ping]
        self.ping_lock = Lock()
        self.PING_FLUSH_THRESHOLD = 5
        self.db_path = db_path
        self._schema_migrations = {
            0: self._migrate_0_to_1,
        }
        self._migrate_schema()

    def ping(self, ping: Ping):
        with self.ping_lock:
            self.pings.append(ping)
            if len(self.pings) >= self.PING_FLUSH_THRESHOLD:
                self._flush_pings()

    def _flush_pings(self):
        if not self.pings:
            return
        time_entries = []  # type: List[TimeEntry]
        for i, ping in enumerate(self.pings):
            if not time_entries \
                    or time_entries[-1].entry_type != ping.ping_type \
                    or time_entries[-1].origin != ping.origin:
                time_entries.append(TimeEntry(
                    from_timestamp=ping.timestamp,
                    entry_type=ping.ping_type,
                    origin=ping.origin,
                    to_timestamp=self.pings[i + 1].timestamp if i + 1 != len(self.pings) else now_milliseconds()
                ))
            else:
                time_entries[-1].to_timestamp = ping.timestamp
        for i in range(len(time_entries)):
            if i != len(time_entries) - 1:
                time_entries[i].to_timestamp = -1
            print(f"Flushing time entry {time_entries[i]}")

        self.pings = []  # type: List[Ping]

    def _new_conn(self):
        return sqlite3.connect(self.db_path)

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
            print(f"Executing schema migration for version {v}")
            self._schema_migrations[v]()
        self._update_schema_version(latest_schema_version)

    def _migrate_0_to_1(self):
        for statement in [
            'CREATE TABLE schema_version (v INTEGER)',
            'INSERT INTO schema_version (v) VALUES(1)',
            'CREATE TABLE time_entry (from_timestamp INTEGER, type TEXT, origin TEXT, to_timestamp INTEGER)'
        ]:
            with sqlite_execute(self._new_conn(), statement):
                pass

    def _get_schema_version(self) -> int:
        if not self._if_schema_version_exists():
            return 0
        with sqlite_execute(self._new_conn(), 'SELECT v FROM schema_version') as cursor:
            result = cursor.fetchone()
            return result[0]

    def _if_schema_version_exists(self) -> bool:
        with sqlite_execute(self._new_conn(), 'PRAGMA table_info(schema_version)') as cursor:
            results = cursor.fetchall()
            return len(results) != 0

    def _update_schema_version(self, v: int):
        with sqlite_execute(self._new_conn(), 'UPDATE schema_version SET v = ?', (v,)):
            pass
