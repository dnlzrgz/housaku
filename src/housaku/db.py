import sqlite3
from contextlib import contextmanager


def init_db(sqlite_url: str) -> None:
    conn = sqlite3.connect(sqlite_url)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS documents USING fts5 (
        uri, title, type, content, tokenize="porter unicode61"
    );
    """)

    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA synchronous=NORMAL;")
    cursor.execute("PRAGMA busy_timeout=5000;")
    cursor.execute("PRAGMA temp_store=MEMORY;")
    cursor.execute("PRAGMA cache_size = 2000;")

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
