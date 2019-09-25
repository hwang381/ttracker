import sqlite3
from .ping import Ping
from .time_entry import TimeEntry
from .external_ping import ExternalPing
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


class SqliteStore(object):
    def __init__(self, db_path: str):
        self.pings = []  # type: List[Ping]
        self.PING_FLUSH_THRESHOLD = 5

        self.external_pings = {}  # type: Dict[str, List[ExternalPing]]
        self.EXTERNAL_PING_FLUSH_THRESHOLD = 5

        self.db_path = db_path
        self._schema_migrations = {
            0: self._migrate_0_to_1,
        }
        self._migrate_schema()

        last_time_entry = self._get_last_time_entry()
        if not last_time_entry:
            self.gen = 0
        elif last_time_entry.gen == 0:
            self.gen = 1
        else:
            self.gen = 0

    def desktop_ping(self, ping: Ping):
        self.pings.append(ping)
        if len(self.pings) >= self.PING_FLUSH_THRESHOLD:
            self._flush_pings()

    def external_ping(self, external_ping: ExternalPing):
        ping_type = external_ping.ping_type
        if ping_type not in self.external_pings:
            self.external_pings[ping_type] = []
        queue = self.external_pings[ping_type]
        queue.append(external_ping)
        # TODO: flush

    def get_time_entries(self, from_timestamp: int, to_timestamp: int) -> List[TimeEntry]:
        with sqlite_execute(
                self._new_conn(),
                'SELECT from_timestamp, type, origin, to_timestamp, gen from time_entry '
                'WHERE from_timestamp >= ? AND from_timestamp < ?',
                (from_timestamp, to_timestamp)
        ) as cursor:
            results = []
            for result in cursor.fetchall():
                results.append(TimeEntry(
                    from_timestamp=result[0],
                    entry_type=result[1],
                    origin=result[2],
                    to_timestamp=result[3],
                    gen=result[4]
                ))
            return results

    ###
    # base methods for desktop time entries
    ###
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
                    to_timestamp=self.pings[i + 1].timestamp if i + 1 != len(self.pings) else now_milliseconds(),
                    gen=self.gen
                ))
            else:
                time_entries[-1].to_timestamp = ping.timestamp

        for i in range(len(time_entries)):
            if i != len(time_entries) - 1:
                time_entries[i].to_timestamp = 0
            time_entry = time_entries[i]
            if i == 0:
                last_time_entry = self._get_last_time_entry()
                if last_time_entry and last_time_entry.gen == time_entry.gen:
                    if last_time_entry.entry_type == time_entry.entry_type \
                            and last_time_entry.origin == time_entry.origin:
                        print("Merging into last time entry")
                        self._update_last_time_entry(time_entry.to_timestamp)
                        continue
                    else:
                        print("Updating last time entry")
                        self._update_last_time_entry(0)
            print(f"Flushing time entry {time_entry}")
            self._append_time_entry(time_entry)

        self.pings = []  # type: List[Ping]

    def _get_last_time_entry(self) -> Optional[TimeEntry]:
        with sqlite_execute(
                self._new_conn(),
                'SELECT from_timestamp, type, origin, to_timestamp, gen FROM time_entry ORDER BY ROWID DESC LIMIT 1'
        ) as cursor:
            result = cursor.fetchone()
            if not result:
                return None
            return TimeEntry(
                from_timestamp=result[0],
                entry_type=result[1],
                origin=result[2],
                to_timestamp=result[3],
                gen=result[4]
            )

    def _update_last_time_entry(self, to_timestamp: int):
        with sqlite_execute(
                self._new_conn(),
                'UPDATE time_entry SET to_timestamp = ? WHERE ROWID = (SELECT MAX(ROWID) FROM time_entry)',
                (to_timestamp,)
        ):
            pass

    def _append_time_entry(self, time_entry: TimeEntry):
        with sqlite_execute(
                self._new_conn(),
                'INSERT INTO time_entry (from_timestamp, type, origin, to_timestamp, gen) VALUES(?, ?, ?, ?, ?)',
                (time_entry.from_timestamp, time_entry.entry_type, time_entry.origin, time_entry.to_timestamp,
                 time_entry.gen)
        ):
            pass

    ###
    # base methods
    ###
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
            'CREATE TABLE time_entry '
            '(from_timestamp INTEGER, type TEXT, origin TEXT, to_timestamp INTEGER, gen INTEGER)',
            'CREATE TABLE browser_time_entry '
            '(from_timestamp INTEGER, origin TEXT, to_timestamp INTEGER, gen INTEGER)'
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
