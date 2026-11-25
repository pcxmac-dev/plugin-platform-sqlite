"""What the SQLite plugin attaches to (plugin API 2.2, liminal_libs.sources.apis; the user, 2026-11-11: "each plugin
should reflect the the API its attached to, and present links that provide documentation ... it should also expose more
of what the API is about"): SQLite itself, through Python's sqlite3 module. Local only: nothing is sent anywhere.

Every address is one of SQLite's own pages (sqlite.org) or Python's (docs.python.org), each read on 2026-11-16
(`VERIFIED`): the documentation index, Write-Ahead Logging, File Locking And Concurrency, SQLite Over a Network, How To
Corrupt An SQLite Database File, Uniform Resource Identifiers, ATTACH DATABASE, Compile-Time Authorization Callbacks,
the pragmas, VACUUM, the Database File Format, the release history (3.54.1 of 2026-10-16 the newest) and the copyright
page (public domain); and Python's sqlite3 page for connect()'s parameters and the Connection methods named here.

Three of those pages are why a file is never opened across systems, and the card says so: the write-ahead log needs
every process to share memory, which processes on separate hosts cannot; file locking is unreliable on network
filesystems, which can corrupt a database; and SQLite's own advice for a database another machine must reach is to do
every read and write on the database's machine, through a proxy. Liminal's helper (liminal_libs.storage.link) is that
proxy."""
from __future__ import annotations

from liminal_libs.sources.apis import Api, Area, Call, Link

VERIFIED = "2026-11-16"
SITE = "https://www.sqlite.org/"
DOCS = SITE + "docs.html"
WAL = SITE + "wal.html"
LOCKING = SITE + "lockingv3.html"
OVER_NET = SITE + "useovernet.html"
CORRUPT = SITE + "howtocorrupt.html"
URI = SITE + "uri.html"
ATTACH = SITE + "lang_attach.html"
AUTHORIZER = SITE + "c3ref/set_authorizer.html"
PRAGMA = SITE + "pragma.html"
VACUUM = SITE + "lang_vacuum.html"
FORMAT = SITE + "fileformat2.html"
CHANGES = SITE + "changes.html"
COPYRIGHT = SITE + "copyright.html"
PYTHON = "https://docs.python.org/3/library/sqlite3.html"

SQLITE = Api(
    name="SQLite",
    maker="The SQLite project (sqlite.org); Python's sqlite3 module (python.org)",
    about=("A database engine in a library: a database is one file, read and written by the processes that open it, "
           "with no server. Everything the app keeps in SQLite is such a file in the data folder. The plugin reaches it "
           "through Python's sqlite3 module, and never across systems: a file on another system's drive is opened by "
           "that system, through Liminal's helper, over a private pipe."),
    kind="sdk",
    base="the files of the data folder (liminal.db, feeds/, datasets/, gov/, instances/) and wherever an instance is",
    version="SQLite 3 (written against 3.53.4, this Python's; 3.54.1 of 2026-10-16 was the newest)",
    auth=("none of its own: a file's rights on its system. From another system, the share set on its instance, kept to by "
          "Liminal's helper"),
    limits="one writer at a time on a file; in write-ahead logging readers go on beside it",
    costs="",
    links=(
        Link("SQLite Documentation", DOCS, "docs"),
        Link("Python's sqlite3 module (DB-API 2.0 interface for SQLite databases)", PYTHON, "reference"),
        Link("Write-Ahead Logging", WAL, "guide"),
        Link("File Locking And Concurrency In SQLite Version 3", LOCKING, "guide"),
        Link("SQLite Over a Network, Caveats and Considerations", OVER_NET, "guide"),
        Link("How To Corrupt An SQLite Database File", CORRUPT, "guide"),
        Link("Database File Format", FORMAT, "spec"),
        Link("Release History Of SQLite", CHANGES, "changelog"),
        Link("SQLite Copyright (public domain)", COPYRIGHT, "terms"),
    ),
    areas=(
        Area("Database files", "a database is one file of pages (B-trees), its journal or its write-ahead log beside it",
             FORMAT, covered="the data folder's files are its own instance; a new file is made; one that exists is connected"),
        Area("Write-ahead logging", "readers and one writer at once, through a log and an index in memory that every "
             "process of the file shares: all of them on one host", WAL,
             covered="a database made here is in it, as the app's own files are; Test says a file's journal mode"),
        Area("Over a network", "SQLite's advice for a database another machine must reach: a client/server engine, or "
             "every read and write done on the database's own machine, through a proxy", OVER_NET,
             covered="a file on another system's drive is opened by that system alone, through Liminal's helper"),
        Area("File locking", "how readers and writers take turns on a file; unreliable on network filesystems, where a "
             "database can then be corrupted", LOCKING),
        Area("What corrupts a file", "the ways a database file gets corrupted, filesystems with broken locks among them",
             CORRUPT),
        Area("URI filenames", "a file named as a URI, opened as its mode says: ro, rw, rwc or memory", URI,
             covered="an instance is opened for reading with mode=ro; one shared for reading alone is opened so by the "
                     "helper whatever was asked; a file is never made for another system (mode=rw)"),
        Area("ATTACH DATABASE", "another database file added to a connection", ATTACH,
             covered="the helper attaches only a file in its folders, and as the share on that file's instance says"),
        Area("The authorizer", "a callback asked while a statement is compiled, that allows or denies each thing the "
             "statement would do", AUTHORIZER,
             covered="the helper's: an ATTACH of a file outside its folders, or of one not shared for writing, is denied"),
        Area("Pragmas", "the statements that read and set a database's own settings", PRAGMA,
             covered="Test reads journal_mode and user_version; a database made here is set to write-ahead logging"),
        Area("VACUUM", "a database rebuilt; VACUUM INTO writes the rebuilt copy to a new file", VACUUM,
             covered="VACUUM INTO is not made through the helper: a copy is made by the system that holds the files"),
        Area("The SQL language", "the SQL SQLite understands, its functions and its types"),
        Area("The C interface and the other bindings", "the library's own functions; the plugin uses none but through "
             "Python's module"),
        Area("Python's sqlite3 module", "the standard library's interface to SQLite", PYTHON,
             covered="every connection; in the helper its authorizer, progress handler, trace callback and interrupt"),
    ),
    calls=(
        Call("sqlite3.connect(file, timeout=, uri=)", "a connection to a database file", "Python's sqlite3 module",
             used="every open of an instance, here or in the helper (liminal-libs' link.connect)", docs=PYTHON),
        Call("file:<path>?mode=ro", "a file opened for reading alone", "URI filenames",
             used="an instance opened for reading; a file shared with the suite that asks for reading only", docs=URI),
        Call("file:<path>?mode=rw", "a file opened for reading and writing, never made", "URI filenames",
             used="a file opened for another system: none is made there from here", docs=URI),
        Call("file:<path>?mode=rwc", "a file opened for reading and writing, made when it is not there", "URI filenames",
             docs=URI, writes=True),
        Call("SELECT sqlite_version()", "the library's version", "The SQL language",
             used="Test: which SQLite answers, this Python's or the helper's"),
        Call("SELECT count(*) FROM sqlite_master", "the schema's own table", "Database files",
             used="Test: how many tables the file has", docs=FORMAT),
        Call("PRAGMA journal_mode", "the journal's mode, read or set", "Pragmas",
             used="Test reads it; a database made here is set to WAL", docs=PRAGMA, writes=True),
        Call("PRAGMA user_version", "a number the application keeps in the file's header", "Pragmas",
             used="Test: the schema version the app keeps there", docs=PRAGMA),
        Call("PRAGMA query_only", "a connection that refuses every write", "Pragmas", docs=PRAGMA),
        Call("PRAGMA page_size, page_count, freelist_count", "a file's page size, its pages and its unused pages", "Pragmas",
             docs=PRAGMA),
        Call("CREATE TABLE liminal_instance (...) WITHOUT ROWID", "a table made", "The SQL language",
             used="a database made here says what it is in it: its name, the day, what it is to hold", writes=True),
        Call("ATTACH DATABASE ? AS name", "another file added to a connection, named by a parameter", "ATTACH DATABASE",
             used="the storage's own (a feed's file beside the main one): checked by the helper, opened as its share says",
             docs=ATTACH),
        Call("Connection.set_authorizer(callback)", "the authorizer set on a connection", "The authorizer",
             used="the helper: an ATTACH it may not make is denied", docs=PYTHON),
        Call("Connection.set_progress_handler(handler, n)", "a callback every n instructions, that can stop the statement",
             "Python's sqlite3 module", used="the helper's time limit on a page's read", docs=PYTHON),
        Call("Connection.interrupt()", "the statement running on a connection stopped, from another thread",
             "Python's sqlite3 module", used="a page's read given up, through the helper", docs=PYTHON),
        Call("Connection.set_trace_callback(callback)", "each statement SQLite runs told to a callback",
             "Python's sqlite3 module", used="the helper, when the statements run are asked for", docs=PYTHON),
        Call("VACUUM INTO file", "a rebuilt copy of the database written to a new file", "VACUUM", docs=VACUUM, writes=True),
    ),
    verified=VERIFIED,
)

APIS = (SQLITE,)
