"""Every plugin here conforms to the class contract (plugin API 2.3): liminal_libs.sources.conformance, read from
the plugin alone (nothing opened, nothing sent)."""
from __future__ import annotations

import pathlib

import plugin_platform_sqlite as module
from liminal_libs.sources.conformance import assert_module_conforms
from liminal_libs.sources.registry import _plugins_in
from liminal_libs.storage.databases import DatabasePlugin, variable_of
from liminal_libs.ui import STATIC


def test_every_plugin_here_conforms_to_the_class_contract():
    found = assert_module_conforms(module)
    assert [p.name for p in found] == ["sqlite"] and all(p.api == "2.3" and not p.is_record for p in found)
    (p,) = found
    assert isinstance(p, DatabasePlugin) and (p.SYSTEM, p.KIND, p.ENGINE) == (DatabasePlugin.SYSTEM, "database", "sqlite")
    assert p.SYSTEM == "platform" and p.SECTION == "databases"  # the platform's Databases section (liminal-libs 1.90.0)
    assert module.__name__ == "plugin_platform_sqlite" and pathlib.Path(module.__file__).resolve().is_relative_to(
        pathlib.Path(__file__).resolve().parents[1] / "src")  # this checkout's, not the old install
    assert p.METHODS == ('file', 'helper') and p.HOLDS == ('main', 'bars', 'ticks', 'series', 'documents') and p.SERVER is False
    assert p.options[0] == variable_of("sqlite") == "SQLITE_INSTANCES"
    assert p.apis and p.interface()["apis"] == [a.name for a in p.apis]  # what it attaches to (2.2)
    assert set(p.interface()["hooks"]) >= {"builtin", "open", "probe", "make"}
    assert f"    {p.ICON}: '" in (STATIC / "icons.js").read_text(encoding="utf-8")
    assert module.__version__ == "0.2.0" and [q.name for q in _plugins_in(module, "test")] == ["sqlite"]
