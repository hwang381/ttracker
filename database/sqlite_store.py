import sqlite3
import logging
from .ping import Ping
from .time_entry import TimeEntry
from typing import List, Optional, Dict
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


SANCTIONED_PING_TYPES = [
    'desktop',
    'browser'
]

PING_FLUSH_THRESHOLD_SECONDS = 5
assert PING_FLUSH_THRESHOLD_SECONDS > 0

NEW_TIME_ENTRY_THRESHOLD_MILLISECONDS = 5 * 1000


class SqliteStore(object):
    def __init__(self, db_path: str):
        self.pings = {}  # type: Dict[str, List[Ping]]

        self.db_path = db_path
        self._schema_migrations = {
            0: self._migrate_0_to_1,
        }
        self._migrate_schema()

    ###
    # Write API
    ###
    def ping(self, ping: Ping):
        ping_queue = self._get_ping_queue_or_raise(ping.ping_type)
        ping_queue.append(ping)
        if len(ping_queue) >= PING_FLUSH_THRESHOLD_SECONDS:
            self._flush_pings(ping.ping_type, now_milliseconds())

    ###
    # Read API
    ###
    def get_time_entries(self, from_timestamp: int, to_timestamp: int, entry_type: str) -> List[TimeEntry]:
        with sqlite_execute(
                self._new_conn(),
                'SELECT from_timestamp, origin, to_timestamp '
                f'from {self._get_time_entry_table_name_or_raise(entry_type)} '
                'WHERE from_timestamp >= ? AND from_timestamp < ?',
                (from_timestamp, to_timestamp)
        ) as cursor:
            results = []
            for result in cursor.fetchall():
                results.append(TimeEntry(
                    from_timestamp=result[0],
                    entry_type=entry_type,
                    origin=result[1],
                    to_timestamp=result[2],
                ))
            return results

    ###
    # Logic methods
    ###
    def _flush_pings(self, ping_type: str, flush_at_milliseconds: int):
        ping_queue = self._get_ping_queue_or_raise(ping_type)
        time_entries = []  # type: List[TimeEntry]

        # merge in-memory pings into in-memory time entries
        for ping in ping_queue:
            if not time_entries \
                    or time_entries[-1].entry_type != ping.ping_type \
                    or time_entries[-1].origin != ping.origin:
                if time_entries:
                    # end the previous time entry properly
                    time_entries[-1].to_timestamp = ping.timestamp
                time_entries.append(TimeEntry(
                    from_timestamp=ping.timestamp,
                    entry_type=ping.ping_type,
                    origin=ping.origin,
                    to_timestamp=-1
                ))
            else:
                time_entries[-1].to_timestamp = ping.timestamp

        # end the last time entry properly
        time_entries[-1].to_timestamp = ping_queue[-1].timestamp

        # merge the first time entry if necessary
        last_time_entry = self._get_last_time_entry(ping_type)
        if last_time_entry and last_time_entry.to_timestamp + NEW_TIME_ENTRY_THRESHOLD_MILLISECONDS > time_entries[0].from_timestamp:
            logging.info(f"[{ping_type}] Merging the first time entry to {time_entries[0].to_timestamp}")
            self._update_last_time_entry(time_entries[0].to_timestamp, ping_type)
            del time_entries[0]

        # persist the rest of time entries
        for time_entry in time_entries:
            logging.info(f"[{ping_type}] Persisting time entry {time_entry}")
            self._append_time_entry(time_entry, ping_type)

        self._reset_ping_queue_or_raise(ping_type)

    ###
    # Helper methods
    ###
    def _check_ping_type(self, ping_type: str):
        if ping_type not in SANCTIONED_PING_TYPES:
            raise NotImplementedError(f"Unsupported ping type {ping_type}")

    def _get_ping_queue_or_raise(self, ping_type: str) -> List[Ping]:
        self._check_ping_type(ping_type)
        if ping_type not in self.pings:
            self.pings[ping_type] = []
        return self.pings[ping_type]

    def _reset_ping_queue_or_raise(self, ping_type: str):
        self._check_ping_type(ping_type)
        self.pings[ping_type] = []

    def _get_time_entry_table_name_or_raise(self, entry_type: str) -> str:
        self._check_ping_type(entry_type)
        return f"{entry_type}_time_entry"

    ###
    # Database logic methods
    ###
    def _get_last_time_entry(self, entry_type: str) -> Optional[TimeEntry]:
        table_name = self._get_time_entry_table_name_or_raise(entry_type)
        with sqlite_execute(
                self._new_conn(),
                f'SELECT from_timestamp, origin, to_timestamp FROM {table_name} ORDER BY ROWID DESC LIMIT 1'
        ) as cursor:
            result = cursor.fetchone()
            if not result:
                return None
            return TimeEntry(
                from_timestamp=result[0],
                entry_type=entry_type,
                origin=result[1],
                to_timestamp=result[2],
            )

    def _update_last_time_entry(self, to_timestamp: int, entry_type: str):
        table_name = self._get_time_entry_table_name_or_raise(entry_type)
        with sqlite_execute(
                self._new_conn(),
                f'UPDATE {table_name} SET to_timestamp = ? WHERE ROWID = (SELECT MAX(ROWID) FROM {table_name})',
                (to_timestamp,)
        ):
            pass

    def _append_time_entry(self, time_entry: TimeEntry, entry_type: str):
        table_name = self._get_time_entry_table_name_or_raise(entry_type)
        with sqlite_execute(
                self._new_conn(),
                f'INSERT INTO {table_name} (from_timestamp, origin, to_timestamp) VALUES(?, ?, ?)',
                (time_entry.from_timestamp, time_entry.origin, time_entry.to_timestamp,)
        ):
            pass

    ###
    # Database methods
    ###
    def _new_conn(self):
        return sqlite3.connect(self.db_path)

    def _migrate_schema(self):
        schema_version = self._get_schema_version()
        latest_schema_version = max(self._schema_migrations.keys()) + 1
        if schema_version == latest_schema_version:
            logging.info(f"Already on latest schema version {latest_schema_version}")
            return
        migrate_versions = [i for i in range(schema_version, latest_schema_version)]
        for v in migrate_versions:
            if v not in self._schema_migrations:
                raise RuntimeError(f'Schema migration for version {v} is undefined')
        for v in migrate_versions:
            logging.info(f"Executing schema migration for version {v}")
            self._schema_migrations[v]()
        self._update_schema_version(latest_schema_version)

    def _migrate_0_to_1(self):
        for statement in [
            'CREATE TABLE schema_version (v INTEGER)',
            'INSERT INTO schema_version (v) VALUES(1)',
            'CREATE TABLE desktop_time_entry '
            '(from_timestamp INTEGER, origin TEXT, to_timestamp INTEGER)',
            'CREATE TABLE browser_time_entry '
            '(from_timestamp INTEGER, origin TEXT, to_timestamp INTEGER)'
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
