"""What the SQLite plugin attaches to (plugin API 2.2): its card is sound, every address one of SQLite's or Python's
own pages; it names the statements the plugin itself runs; what it knows of SQLite here asks nothing; and the card's
pages answer (LIMINAL_VENDOR_PAGES=1 only, the one test that reaches the network)."""
from __future__ import annotations

import inspect
import os
import sqlite3

import pytest

import plugin_platform_sqlite as module
from liminal_libs.sources.apis import dead_links, problems, urls
from plugin_platform_sqlite import DATABASE
from plugin_platform_sqlite import apis as cards


def test_the_card_is_sound_and_links_the_makers_own_pages():
    assert problems(DATABASE.apis) == [] and DATABASE.apis == cards.APIS == (cards.SQLITE,)
    api = cards.SQLITE
    assert (api.name, api.kind, api.verified, api.costs) == ("SQLite", "sdk", "2026-11-16", "") and api.docs == cards.DOCS
    assert all(u.startswith(("https://www.sqlite.org/", "https://docs.python.org/3/library/sqlite3.html")) for u in urls(DATABASE.apis))
    assert len(urls(DATABASE.apis)) == 14 and {x.kind for x in api.links} == {"docs", "reference", "guide", "spec", "changelog", "terms"}
    assert len(api.areas) > len(api.covered) >= 8 and len(api.calls) > len(api.used) >= 12
    assert {c.area for c in api.calls} <= {a.name for a in api.areas}
    # why a file is never opened across systems is on the card, with SQLite's own pages for it
    assert {cards.WAL, cards.LOCKING, cards.OVER_NET, cards.CORRUPT} <= {a.docs for a in api.areas}
    assert "through Liminal's helper" in next(a.covered for a in api.areas if a.name == "Over a network")


def test_the_card_names_what_the_plugin_itself_runs():
    src = inspect.getsource(module)
    used = " ".join(c.name for c in cards.SQLITE.used)
    for statement in ("SELECT sqlite_version()", "PRAGMA journal_mode", "PRAGMA user_version", "sqlite_master"):
        assert statement in src and statement in used
    assert f"CREATE TABLE {module.MARKER} " in used and "CREATE TABLE {MARKER} " in src
    assert "link import connect" in src and "sqlite3.connect(" not in src  # every open goes through the library's one way
    assert module.SqlitePlugin().api_facts() == {"SQLite": {"SQLite in this Python": sqlite3.sqlite_version}}


@pytest.mark.skipif(os.environ.get("LIMINAL_VENDOR_PAGES") != "1", reason="reaches SQLite's and Python's pages: LIMINAL_VENDOR_PAGES=1")
def test_the_cards_pages_answer():
    assert dead_links(DATABASE.apis) == []
