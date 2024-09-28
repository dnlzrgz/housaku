from housaku.db import db_connection


def search(sqlite_url: str, query: str, limit: int = 20) -> list[tuple[str, str, str]]:
    with db_connection(sqlite_url) as conn:
        cursor = conn.cursor()
        sql_query = f"""
            SELECT uri, title, type FROM documents WHERE documents MATCH '{query}' ORDER BY bm25(documents) LIMIT ?
            """

        cursor.execute(sql_query, (limit,))
        results = cursor.fetchall()
        return results
