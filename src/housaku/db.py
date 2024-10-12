import sqlite3
from contextlib import contextmanager


def init_db(sqlite_url: str) -> None:
    conn = sqlite3.connect(sqlite_url)
    cursor = conn.cursor()

    # Creates the documents table.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        uri TEXT UNIQUE NOT NULL,
        title TEXT,
        type TEXT NOT NULL,
        body TEXT NOT NULL
    );
    """)

    # Adds index on the uri column
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_uri ON documents(uri)")

    # Creates virtual FTS5 table for full-text search
    cursor.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5 (
        uri,
        title,
        type,
        body,
        content=documents,
        tokenize="porter unicode61"
    );
    """)

    # Settings
    cursor.execute("PRAGMA journal_mode = WAL;")
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.execute("PRAGMA synchronous = NORMAL;")
    cursor.execute("PRAGMA busy_timeout = 5000;")
    cursor.execute("PRAGMA temp_store = MEMORY;")
    cursor.execute("PRAGMA cache_size = 2000;")

    cursor.execute("PRAGMA transaction_mode = IMMEDIATE;")

    conn.commit()
    conn.close()


def purge_db(sqlite_url: str) -> None:
    conn = sqlite3.connect(sqlite_url)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS documents;")
    cursor.execute("DROP TABLE IF EXISTS documents_fts;")
    cursor.execute("DROP INDEX IF EXISTS idx_uri;")

    cursor.execute("VACUUM;")

    conn.commit()
    conn.close()


def rebuilt_fts_table(sqlite_url: str) -> None:
    conn = sqlite3.connect(sqlite_url)
    cursor = conn.cursor()

    cursor.execute("INSERT INTO documents_fts(documents_fts) VALUES('rebuild');")

    conn.commit()
    conn.close()


@contextmanager
def db_connection(sqlite_url: str):
    conn = sqlite3.connect(sqlite_url)

    try:
        yield conn
        conn.commit()
    except:
        conn.rollback()
        raise
    finally:
        conn.close()
