from contextlib import contextmanager
from sqlalchemy.orm import Session
from housaku.models import Base


def init_db(engine) -> None:
    Base.metadata.create_all(engine)
    with engine.connect() as connect:
        cursor = connect.connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA synchronous=NORMAL;")
        cursor.execute("PRAGMA synchronous=NORMAL;")
        cursor.execute("PRAGMA busy_timeout=5000;")
        cursor.execute("PRAGMA temp_store=MEMORY;")
        cursor.execute("PRAGMA nmap_size = 134217728;")
        cursor.execute("PRAGMA journal_size_limit = 67108864;")
        cursor.execute("PRAGMA cache_size = 2000;")


@contextmanager
def session_manager(engine):
    session = Session(engine)

    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()
