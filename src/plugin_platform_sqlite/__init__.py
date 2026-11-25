"""SQLite for Liminal: the data folder's SQLite files as an instance of their own, new files and files elsewhere
beside it (a database plugin, plugin API 2.3: liminal_libs.storage.databases; the platform's,
drawn in its Databases section, since 0.2.0: it was plugin-integrator-sqlite).

The user, 2026-11-15: "for the integrator i need plugins for each type of database and in each plugin can setup either
new databases or connections to existing databases using many different types of IP or IPC methods. each instance in
the plugin has it's own configuration how it's shared, ports, permissions etc".

Its own instance, `data`, is what the app keeps in SQLite today, where it is and opened as it is: the main file
(liminal.db), each feed's bars and trades (feeds/<feed>.db, <feed>-ticks.db), the datasets' series (datasets/), the
agencies' items (gov/gov.db). With nothing set, nothing changes. Beside it you may make a new database (a file in the
data folder's instances/, or at a whole path) or connect one that exists (a backup to look into, a file on another
disk), and say for each who else may attach: a suite on another system (the one inside WSL: linux::Ubuntu) reading
only, or writing too.

Two methods. `file`: the file opened directly, on this machine's own disk. `helper`: a file on another system's drive
is opened by that system, through a helper process this one starts there and speaks to over a private pipe (no port,
nothing listening: liminal_libs.storage.link); it is chosen by itself where the file is, and it is the helper that
keeps to the shares. SQLite's own pages say why a file is never opened across systems (its locks and its write-ahead
log's shared memory do not cross a network filesystem); the plugin's API card links them.

Every database it opens it opens through `open` (liminal_libs.storage.link.connect: the one way a SQLite file is
opened), and a database it makes is in write-ahead logging like the app's own, with a small table saying what it is
(`liminal_instance`)."""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path

from liminal_libs import layout, mounts
from liminal_libs.storage.databases import DATA, SUFFIXES, DatabasePlugin, Instance, Refusal, now_iso, variable_of

from .apis import APIS, SQLITE

__version__ = "0.2.0"
TIMEOUT_S = 5.0  # how long an open waits for a lock, as the app's own
MARKER = "liminal_instance"  # the table a database made here says what it is in
FOLDERS = ("feeds", "datasets", "gov", "login", "backups", "instances")  # the data folder's own, in the order they are said
NOT_ITS = ("mongo", "logs", "history")  # top folders that hold no SQLite file: MongoDB's own, the logs, DuckDB's months
MAX_DEPTH, MAX_SEEN = 5, 50_000  # how far down, and how many names, a count looks at
ENDS = SUFFIXES["sqlite"]


def sqlite_files(folder: Path) -> dict[str, int]:
    """The SQLite files under a data folder, counted by the top folder each is in ("" for the folder itself); their
    -wal and -shm are none. Names alone: nothing is opened. What cannot be listed counts nothing."""
    counts: dict[str, int] = {}
    stack, seen = [(Path(folder), "", 0)], 0
    while stack:
        here, top, depth = stack.pop()
        try:
            with os.scandir(here) as it:
                for e in it:
                    seen += 1
                    if seen > MAX_SEEN:
                        return counts
                    try:
                        if e.is_dir(follow_symlinks=False):
                            if depth < MAX_DEPTH and not (depth == 0 and e.name in NOT_ITS):
                                stack.append((Path(e.path), top or e.name, depth + 1))
                        elif e.name.lower().endswith(ENDS) and e.is_file(follow_symlinks=False):
                            counts[top] = counts.get(top, 0) + 1
                    except OSError:
                        continue
        except OSError:
            continue
    return counts


def counted(folder: Path) -> str:
    """The data folder's SQLite files, in words: how many, and in which of its folders (the app's own first)."""
    counts = sqlite_files(folder)
    total = sum(counts.values())
    order = ["", *FOLDERS, *sorted(n for n in counts if n and n not in FOLDERS)]
    detail = ", ".join(f"{counts[n]} {'at its top' if not n else f'in {n}/'}" for n in order if counts.get(n))
    return f"{total} SQLite file{'' if total == 1 else 's'} in the folder" + (f" ({detail})" if detail and total > 1 else "")


class SqlitePlugin(DatabasePlugin):
    name = "sqlite"
    title = "SQLite"
    about = ("The data folder's SQLite files as an instance of their own (the main file, each feed's bars and trades, the "
             "datasets' series, the agencies' items), with new files and files elsewhere beside it, each shared with "
             "another system's suite as you set it")
    api = "2.3"
    order = 700
    options = (variable_of("sqlite"),)  # SQLITE_INSTANCES: what you add, kept through the login
    apis = APIS
    ENGINE = "sqlite"
    METHODS = ("file", "helper")
    HOLDS = ("main", "bars", "ticks", "series", "documents")
    SHARES = True  # kept to by the helper (liminal_libs.storage.link)

    # -- the hooks ---------------------------------------------------------------------------------------------------
    def builtin(self, data_dir: Path) -> tuple[Instance, ...]:
        return (Instance(DATA, "The data folder", where="./", holds=self.HOLDS,
                         note="every SQLite file the app keeps: liminal.db, feeds/<feed>.db and <feed>-ticks.db, "
                              "datasets/, gov/"),)

    def file_of(self, instance: Instance, part: str = "", data_dir: Path | None = None) -> Path:
        """The file an instance is, or the one of a folder instance that `part` names (its path in it; the main file
        when none is named). Refusal for a part that is no SQLite file of it."""
        path = self.path_of(instance, data_dir)
        if path is None:
            raise mounts.NotHere(f"{instance.name} is at {instance.where}, on the system that holds the data: this one "
                                 "has no name for that path")
        if not instance.folder:
            if part:
                raise Refusal(f"{instance.name} is one file: there is no {str(part)[:60]!r} in it")
            return path
        named = str(part or layout.MAIN).replace("\\", "/")
        pieces = [p for p in named.split("/") if p not in ("", ".")]
        if not pieces or ".." in pieces or ":" in named or named.startswith("/") or not named.lower().endswith(ENDS):
            raise Refusal(f"{str(part)[:60]!r} is not a SQLite file of {instance.name}")
        return path.joinpath(*pieces)

    def open(self, instance: Instance, part: str = "", read_only: bool = True, data_dir: Path | None = None):
        """A connection to the instance's file (a folder's: the file `part` names, its main file by default), for
        reading unless asked otherwise: through the helper where the file is another system's. Never makes one."""
        from liminal_libs.storage.link import connect

        path = self.file_of(instance, part, data_dir)
        if not path.is_file():
            raise FileNotFoundError(f"{path}: no such database")
        return connect(path, timeout=TIMEOUT_S, read_only=read_only)

    def probe(self, instance: Instance, data_dir: Path) -> list[str]:
        path = self.file_of(instance, "", data_dir)
        conn = self.open(instance, data_dir=data_dir)
        try:
            one = lambda sql: conn.execute(sql).fetchone()[0]  # noqa: E731
            version = one("SELECT sqlite_version()")
            tables = one("SELECT count(*) FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'")
            journal, schema = one("PRAGMA journal_mode"), one("PRAGMA user_version")
            made = _made(conn)
        finally:
            conn.close()
        helper = self.effective_method(instance, data_dir) == "helper"
        lines = [f"SQLite {version}, " + ("opened by the system that holds it, through the helper" if helper else "opened here"),
                 f"{path.name}: {tables} table{'' if tables == 1 else 's'}, journal mode {journal}, schema version {schema}"]
        if made:
            lines.append(f"made here on {made.get('made', '?')[:10]} to hold {made.get('holds') or 'nothing yet'}")
        if instance.folder:
            lines.append(counted(self.path_of(instance, data_dir)))
        return lines

    def make(self, instance: Instance, data_dir: Path, **given) -> list[str]:
        from liminal_libs.storage.link import connect

        path = self.file_of(instance, "", data_dir)
        mounts.owner_only(path.parent if path.parent.exists() else data_dir, "making a SQLite database")
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            raise Refusal(f"{path} is there already: a new database is never made over a file")
        conn = connect(path, timeout=TIMEOUT_S)
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute(f"CREATE TABLE {MARKER} (key TEXT PRIMARY KEY, value TEXT) WITHOUT ROWID")
            conn.executemany(f"INSERT INTO {MARKER} VALUES (?, ?)", [
                ("name", instance.name), ("made", instance.at or now_iso()), ("holds", ",".join(instance.holds)),
                ("by", f"plugin-platform-sqlite {__version__}")])
            conn.commit()
        except Exception:
            conn.close()
            _unmade(path)  # no half-made file is left: the next try would find it there and refuse
            raise
        conn.close()
        return [f"{path.name} made in {path.parent}", "in write-ahead logging, as the app's own files are"]

    def api_facts(self) -> dict:
        """What is known of SQLite here without asking anything: the library this Python carries, and the one the
        helper carries when this process reaches its files through one."""
        from liminal_libs.storage import link

        facts = {"SQLite in this Python": sqlite3.sqlite_version}
        owner = link.owner_link()  # (never started to be asked)
        if owner is not None and not owner.dead:
            facts["SQLite in the helper"] = str(owner.info.get("sqlite") or "?")
            facts["The helper"] = f"{owner.name}, liminal-libs {owner.info.get('library') or '?'}"
        return {SQLITE.name: facts}


def _unmade(path: Path) -> None:
    """A file this plugin was making, and what SQLite left beside it, taken away again (it failed before it was one)."""
    for name in (path.name, path.name + "-wal", path.name + "-shm", path.name + "-journal"):
        try:
            path.with_name(name).unlink()
        except OSError:
            pass


def _made(conn) -> dict | None:
    """What a database made here says of itself (its liminal_instance table); None for any other."""
    try:
        return {str(k): str(v) for k, v in conn.execute(f"SELECT key, value FROM {MARKER}").fetchall()}
    except sqlite3.Error:
        return None


DATABASE = SqlitePlugin()
