# Changelog

## 0.2.0 (2026-11-25)

Renamed `plugin-platform-sqlite` (the package `plugin_platform_sqlite`; it was `plugin-integrator-sqlite`): a platform
plugin of the Databases section (Monday list item 30, step 3; the user, 2026-11-25: the packages renamed
`plugin-platform-sqlite`, `-duckdb`, `-mongodb`, plugin names and settings kept). Since liminal-libs 1.90.0
`DatabasePlugin` is a `PlatformPlugin` (SYSTEM "platform", SECTION "databases"; KIND "database" kept), so the
platform draws it and the integrator and the charts include the platform to open it.

- Its name is still `sqlite`: every instance kept under `SQLITE_INSTANCES` and every kept sign-in is untouched.
- The entry point group is the same (`liminal.providers`), as for every platform plugin.
- A database it makes now says `by: plugin-platform-sqlite 0.2.0` in its `liminal_instance`; ones made before keep
  what they said.
- Uninstall `plugin-integrator-sqlite` and take its checkout out of `plugins/` in the same step: the registry refuses a
  second plugin for one engine.
- Needs liminal-libs>=1.90.0.

## 0.1.0 (2026-11-16)

The first release: SQLite as a database plugin (plugin API 2.3, liminal-libs 1.61.0; the user, 2026-11-15: "for the
integrator i need plugins for each type of database and in each plugin can setup either new databases or connections
to existing databases using many different types of IP or IPC methods. each instance in the plugin has it's own
configuration how it's shared, ports, permissions etc").

- Its own instance `data`: the data folder's SQLite files, opened as the app opens them. With nothing set, nothing
  changes.
- New database (a file in `instances/` or at a whole path, in write-ahead logging, saying what it is) and Connect (a
  file that exists, kept only when it is a database).
- Two methods: `file`, and `helper` for a file on another system's drive, chosen by itself.
- Shares, kept to by the link's helper: a suite on another system reads, reads and writes, or does not attach.
- Its API card: SQLite through Python's sqlite3 module, every address one of sqlite.org's or python.org's own pages,
  read on 2026-11-16, with the three pages that say why a file is never opened across systems.
