from housaku.db import db_connection


def search(
    sqlite_url: str, query: str, limit: int = 20
) -> list[tuple[str, str, str, str]]:
    with db_connection(sqlite_url) as conn:
        cursor = conn.cursor()
        sql_query = """
            SELECT uri, title, type, substr(body, 0, 300)
            FROM documents
            WHERE ROWID IN (
                SELECT ROWID
                FROM documents_fts
                WHERE documents_fts MATCH ?
                ORDER BY bm25(documents_fts)
                LIMIT ?
            )
            """

        cursor.execute(sql_query, (query, limit))
        results = cursor.fetchall()
        return results
