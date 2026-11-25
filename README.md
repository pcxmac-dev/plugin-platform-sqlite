# plugin-platform-sqlite

SQLite for [Liminal](https://github.com/pcxmac-dev/liminal-charts): the data folder's SQLite files as an
instance of their own, with new files and files elsewhere beside it, each shared with another system's suite as you
set it.

## What a database plugin is

A Liminal plugin of the platform's (plugin API 2.3, `liminal_libs.storage.databases`), drawn in its Databases
section: one engine's. It holds
**instances**. An instance is a database the plugin made, or a connection to one that exists, and each has its own
configuration: what it holds, where it is, the method it is reached by, its port, who else may attach and how far,
and on a server the role used there. The platform's Databases section lists them, tests them and changes them;
the integrator and the charts include the platform and open them in their own process.

- **With nothing set, nothing changes.** The plugin's own instance is what the app keeps in this engine today, where
  it is and opened as it is.
- **What you add is kept through the plugin's login**, as one value under `SQLITE_INSTANCES`: never in a file of this
  software's. A sign-in is two more pairs through the login, never in that value and never shown.
- **A change is made by the system that holds the data alone.** The suite on another system (the one inside WSL) reads
  what is kept there and changes nothing of it.
- **Forgetting an instance removes nothing**: what it holds stays where it is. Only you remove data.

## Installing

The app finds it through the entry point group `liminal.providers` and lists it as `package:
plugin-platform-sqlite`, with this package's version; a checkout in the workspace's `plugins/` folder is loaded
from there. It needs `liminal-libs` 1.90.0 or newer.

```
python -m pip install -e ".[dev]"
python -m pytest -q
```

It was `plugin-integrator-sqlite` (0.1.x) until 0.2.0. The plugin's name is still `sqlite`, so every instance kept
under `SQLITE_INSTANCES` and every kept sign-in stays as it was. Only one of the two may be installed or in
`plugins/`: the registry refuses a second plugin for one engine.

The tests open only files of their own (real SQLite files in a temporary folder, the link's helper as a thread of the test); one of them reads the makers' documentation pages, and only with
`LIMINAL_VENDOR_PAGES=1`.

## Its instances

- **`data`, its own**: every SQLite file the app keeps, in the data folder: the main file (`liminal.db`), each feed's
  bars and trades (`feeds/<feed>.db`, `<feed>-ticks.db`), the datasets' series (`datasets/`), the agencies' items
  (`gov/gov.db`). Test opens the main file for reading and says which SQLite answered, its tables, its journal mode,
  and how many SQLite files the folder has.
- **New database**: a file in the data folder's `instances/` (or at a whole path, in a folder that is there), never
  over a file that is there. It is in write-ahead logging like the app's own files, and says what it is in a small
  table (`liminal_instance`: its name, the day, what it is to hold).
- **Connect**: a file that exists, kept only when it is a SQLite database: a backup to look into (`backups/...`), a
  file on another disk. The data folder's own files are the `data` instance's already.

## Its methods

- **`file`**: the file opened directly, on this machine's own disk.
- **`helper`**: a file on another system's drive is opened by that system, through a helper process this one starts
  there and speaks to over a private pipe: no port, nothing listening (`liminal_libs.storage.link`). It is chosen by
  itself where the file is. SQLite's own pages say why a file is never opened across systems: its write-ahead log
  needs every process to share memory, and file locking is unreliable on network filesystems.

## Sharing

A share names a suite as it is named on a database (`linux::Ubuntu`, `windows::NEPTUNE`) and how far it may go: `read`,
`write`, or `none` to take it away. The helper keeps to it: the suite that asks says who it is, and a file is opened
for it for reading and writing, for reading alone whatever it asked, or not at all (an attached file too). With no
share set on an instance, whoever can start a helper on this system reads and writes it, as before. An instance you
added, shared, and outside the data folder becomes one of the folders the helper opens; one shared with nobody stays
closed to it.

## Its API

Its page in every app shows what it attaches to (`DATABASE.apis`): the maker's pages, every part of the engine with what the plugin does with it, and the calls it makes among the rest; and what it knows of the engine here without asking anything (`DATABASE.api_facts()`).
