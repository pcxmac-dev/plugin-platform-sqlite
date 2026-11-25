"""The SQLite plugin on real SQLite files of the test's own (nothing of the app's is opened, no process started): its
own instance is the data folder, opened as the app opens it; a new database is made in write-ahead logging and says
what it is; one that exists is connected only when it is a database; an instance is opened for reading unless asked
otherwise; a share is kept; and the same through the link's helper (a loopback link inside the test's process)."""
from __future__ import annotations

import json
import sqlite3
from types import SimpleNamespace

import pytest

from liminal_libs import mounts
from liminal_libs.apps import EnvironmentLogin
from liminal_libs.storage import link as lk
from liminal_libs.storage.databases import Instance, Refusal, Share
from plugin_platform_sqlite import DATABASE, MARKER, SqlitePlugin, __version__, counted


def table(path, name="kv") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(path)) as raw:
        raw.execute(f"CREATE TABLE {name} (key TEXT PRIMARY KEY, value TEXT)")
        raw.execute(f"INSERT INTO {name} VALUES ('a', '1')")
        raw.execute("PRAGMA user_version = 7")
    raw.close()


@pytest.fixture
def sqlite(tmp_path):
    """The plugin attached to an app whose data folder is the test's: a main file, two feeds' files, a backup."""
    data = tmp_path / "data"
    for name in ("liminal.db", "feeds/massive.db", "feeds/massive-ticks.db", "feeds/tiingo.db", "gov/gov.db", "backups/pre.db",
                 "login/charts/users/ada.db"):
        table(data / name)
    for name in ("history/massive/2026-09.1.duckdb", "mongo/collection-0.db", "logs/old.db", "feeds/massive.db-wal", "feeds/notes.txt"):
        (data / name).parent.mkdir(parents=True, exist_ok=True)
        (data / name).write_bytes(b"not one of its files")
    env: dict = {}
    plugin = SqlitePlugin()
    plugin.attach(SimpleNamespace(db_path=data / "liminal.db"), EnvironmentLogin(env=env))
    return plugin, data, env


def test_its_own_instance_is_the_data_folder_opened_as_the_app_opens_it(sqlite):
    plugin, data, env = sqlite
    assert DATABASE.name == "sqlite" and isinstance(DATABASE, SqlitePlugin) and plugin.driver() == (True, "")
    (own,) = plugin.instances()
    assert (own.name, own.where, own.method, own.builtin, own.folder) == ("data", "./", "file", True, True)
    assert own.holds == ("main", "bars", "ticks", "series", "documents") and plugin.path_of(own) == data
    state = plugin.state(own)
    assert state["state"] == "ready" and state["method"] == "file" and state["foreign"] is False
    tested = plugin.test("data")
    assert tested["ok"] and tested["said"].startswith("data answers (file, ")
    assert tested["lines"] == [f"SQLite {sqlite3.sqlite_version}, opened here",
                               "liminal.db: 1 table, journal mode delete, schema version 7",
                               "7 SQLite files in the folder (1 at its top, 3 in feeds/, 1 in gov/, 1 in login/, 1 in backups/)"]
    assert counted(data / "nowhere") == "0 SQLite files in the folder" and counted(data / "gov") == "1 SQLite file in the folder"
    (data / "platform").mkdir()
    table(data / "platform" / "state.sqlite")
    assert counted(data).endswith("1 in backups/, 1 in platform/)") and counted(data).startswith("8 SQLite files")
    (data / "platform" / "state.sqlite").unlink()  # (every file of the folder is counted, wherever it is: as the view lists them)
    # a file of it by its path in it; for reading unless asked otherwise
    conn = plugin.open(own, "feeds/massive.db")
    assert conn.execute("SELECT value FROM kv").fetchone() == ("1",)
    with pytest.raises(sqlite3.OperationalError, match="readonly"):
        conn.execute("INSERT INTO kv VALUES ('b', '2')")
    conn.close()
    writes = plugin.open(own, r"feeds\tiingo.db", read_only=False)
    writes.execute("INSERT INTO kv VALUES ('b', '2')")
    writes.commit()
    writes.close()
    assert plugin.file_of(own) == data / "liminal.db" and plugin.file_of(own, "gov/gov.db") == data / "gov" / "gov.db"
    for part in ("../outside.db", "feeds/notes.txt", "C:/else.db", "/etc/x.db", "feeds/"):
        with pytest.raises(Refusal, match="is not a SQLite file of data"):
            plugin.open(own, part)
    with pytest.raises(FileNotFoundError, match="no such database"):  # never made by an open
        plugin.open(own, "feeds/nobody.db", read_only=False)
    assert not (data / "feeds" / "nobody.db").exists() and env == {}
    status = plugin.status()
    assert (status["engine"], status["engineTitle"], status["shares"], status["server"]) == ("sqlite", "SQLite", True, False)
    assert status["can"]["new"] and status["can"]["connect"] and status["can"]["share"]
    assert plugin.api_facts() == {"SQLite": {"SQLite in this Python": sqlite3.sqlite_version}}


def test_a_new_database_is_in_write_ahead_logging_and_says_what_it_is(sqlite, tmp_path, monkeypatch):
    plugin, data, env = sqlite
    made = plugin.new_database("archive", holds="bars, ticks", title="Old bars")
    path = data / "instances" / "archive.db"
    assert made["ok"] and made["said"] == f"archive made: {path}"
    assert made["lines"][:2] == [f"archive.db made in {path.parent}", "in write-ahead logging, as the app's own files are"]
    with sqlite3.connect(str(path)) as raw:
        assert raw.execute("PRAGMA journal_mode").fetchone() == ("wal",)
        said = dict(raw.execute(f"SELECT key, value FROM {MARKER}"))
    raw.close()
    assert said["name"] == "archive" and said["holds"] == "bars,ticks" and said["by"] == f"plugin-platform-sqlite {__version__}"
    assert said["made"] == plugin.instance("archive").at and not path.with_name("archive.db-wal").exists()
    tested = plugin.test("archive")
    assert tested["ok"] and tested["lines"][1] == "archive.db: 1 table, journal mode wal, schema version 0"
    assert tested["lines"][2] == f"made here on {said['made'][:10]} to hold bars,ticks"
    assert plugin.state(plugin.instance("archive"))["bytes"] == path.stat().st_size
    # one file: it has no parts; written through an open that asks for it
    with pytest.raises(Refusal, match="archive is one file"):
        plugin.open(plugin.instance("archive"), "other.db")
    conn = plugin.open(plugin.instance("archive"), read_only=False)
    conn.execute("CREATE TABLE bars (ts INTEGER PRIMARY KEY, c REAL)")
    conn.commit()
    conn.close()
    assert plugin.test("archive")["lines"][1].startswith("archive.db: 2 tables")
    # at a whole path elsewhere; never over a file
    other = tmp_path / "disk2"
    other.mkdir()
    assert plugin.new_database("second", where=str(other / "second.sqlite3"))["ok"] and (other / "second.sqlite3").is_file()
    for args, why in ((("x", "backups/pre.db"), "goes in its instances/ folder"), (("x", str(other / "second.sqlite3")), "is there already"),
                      (("x", "instances/x.duckdb"), "a SQLite file ends in"), (("x", "", "history"), "cannot hold history")):
        with pytest.raises(Refusal, match=why):
            plugin.new_database(*args)
    assert [i["name"] for i in json.loads(env["SQLITE_INSTANCES"])["instances"]] == ["archive", "second"]
    # one that fails while it is made leaves no half-made file: the next try starts clean
    monkeypatch.setattr("plugin_platform_sqlite.now_iso", lambda: 1 / 0)
    with pytest.raises(ZeroDivisionError):
        plugin.make(Instance("half", where="instances/half.db"), data)
    assert not list((data / "instances").glob("half.db*"))
    monkeypatch.undo()
    # forgotten: the file stays
    assert plugin.forget("archive")["ok"] and path.is_file() and [i.name for i in plugin.instances()] == ["data", "second"]


def test_a_file_that_exists_is_connected_only_when_it_is_a_database(sqlite, tmp_path):
    plugin, data, env = sqlite
    got = plugin.connect_to("backup", "backups/pre.db", holds="main")
    assert got["ok"] and got["lines"][0] == f"SQLite {sqlite3.sqlite_version}, opened here"
    assert got["lines"][1] == "pre.db: 1 table, journal mode delete, schema version 7"
    elsewhere = tmp_path / "old" / "bars.db"
    table(elsewhere, "bars")
    assert plugin.connect_to("old", str(elsewhere))["ok"] and plugin.test("old")["ok"]
    notes = tmp_path / "notes.db"
    notes.write_text("these are not the pages of a database, however the file is named\n" * 40, encoding="utf-8")
    with pytest.raises(Refusal, match="did not answer, so it is not kept: file is not a database"):
        plugin.connect_to("notes", str(notes))
    for where, why in (("liminal.db", "one of the data folder's own files"), ("feeds/massive.db", "holds it already"),
                       ("backups/gone.db", "is no file here"), (str(tmp_path / "old" / "bars.txt"), "a SQLite file ends in")):
        with pytest.raises(Refusal, match=why):
            plugin.connect_to("x", where)
    assert sorted(i.name for i in plugin.instances()) == ["backup", "data", "old"]
    # gone since: said by its state and by a test, never an error
    elsewhere.unlink()
    assert plugin.state(plugin.instance("old"))["state"] == "absent" and "no such database" in plugin.test("old")["said"]


def test_a_share_on_an_instance_is_kept_for_the_helper_to_keep_to(sqlite):
    plugin, data, env = sqlite
    assert plugin.share("data", "linux::Ubuntu", "read")["said"] == "linux::Ubuntu reads data"
    plugin.new_database("archive")
    plugin.share("archive", "linux::Ubuntu", "write")
    kept = json.loads(env["SQLITE_INSTANCES"])
    assert kept["builtin"] == {"data": {"shared": [{"who": "linux::Ubuntu", "access": "read"}]}}
    assert kept["instances"][0]["shared"] == [{"who": "linux::Ubuntu", "access": "write"}]
    assert plugin.instance("data").shared == (Share("linux::Ubuntu", "read"),)
    rows = {r["name"]: r["sharedWords"] for r in plugin.status()["instances"]}
    assert rows == {"data": "linux::Ubuntu reads only; no other suite attaches",
                    "archive": "linux::Ubuntu reads and writes; no other suite attaches"}
    # what the helper reads of it (liminal_libs.storage.instances.SharePolicy): the same value, by the file asked for
    from liminal_libs.storage.instances import SharePolicy

    policy = SharePolicy(lambda: env["SQLITE_INSTANCES"], data)
    assert policy.access(str(data / "feeds" / "massive.db"), "linux::Ubuntu")[0] == "read"
    assert policy.access(str(data / "instances" / "archive.db"), "linux::Ubuntu")[0] == "write"
    assert policy.access(str(data / "liminal.db"), "linux::Fedora")[0] == ""


def test_through_the_helper_an_instance_answers_as_it_does_here(sqlite, monkeypatch):
    plugin, data, env = sqlite
    monkeypatch.setenv("LIMINAL_LINK", "loopback")  # every file through a link inside this process: the whole protocol
    try:
        conn = plugin.open(plugin.instance("data"), "feeds/massive.db")
        assert isinstance(conn, lk.Connection) and conn.execute("SELECT value FROM kv").fetchone() == ("1",)
        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            conn.execute("INSERT INTO kv VALUES ('b', '2')")
        conn.close()
        assert plugin.test("data")["lines"][1] == "liminal.db: 1 table, journal mode delete, schema version 7"
        assert plugin.new_database("linked")["ok"] and plugin.test("linked")["lines"][1].startswith("linked.db: 1 table, journal mode wal")
        facts = plugin.api_facts()["SQLite"]
        assert facts["SQLite in the helper"] == sqlite3.sqlite_version and "liminal-libs" in facts["The helper"]
    finally:
        lk._close_links()


def test_a_file_on_another_systems_drive_is_reached_through_the_helper_and_changed_from_there(sqlite, monkeypatch):
    plugin, data, env = sqlite
    plugin.new_database("archive")
    monkeypatch.setattr(mounts, "foreign", lambda path, mounts=None: True)
    monkeypatch.setattr("liminal_libs.config.UserEnvironment.saved", lambda self: {"SQLITE_INSTANCES": env["SQLITE_INSTANCES"]})
    assert [(i.name, plugin.effective_method(i)) for i in plugin.instances()] == [("data", "helper"), ("archive", "helper")]
    assert plugin.status()["can"]["new"] is False and "changed from that system" in plugin.status()["can"]["why"]
    with pytest.raises(mounts.NotHere, match="done from that system"):
        plugin.new_database("x")
    with pytest.raises(mounts.NotHere, match="done from that system"):
        plugin.make(Instance("x", where="instances/x.db"), data)
    assert not (data / "instances" / "x.db").exists()
