import psycopg2
import psycopg2.extras
from contextlib import contextmanager
from backend.app.config import settings


@contextmanager
def get_db_connection():
    """
    Yields a psycopg2 connection, and guarantees it's closed afterward
    even if an error occurs inside the 'with' block.

    Using a context manager here (rather than opening/closing connections
    ad hoc in every tool) means we have ONE place that knows how to
    connect to the database - if connection settings or pooling
    strategy change later, only this function changes.
    """
    conn = psycopg2.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        dbname=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
    )
    try:
        yield conn
    finally:
        conn.close()


def run_query(query: str, params: tuple = ()) -> list[dict]:
    """
    Runs a parameterized SELECT query and returns rows as a list of
    dicts (column name -> value), rather than raw tuples - much easier
    for tool functions to work with and to return to the LLM.

    IMPORTANT: `query` must use %s placeholders and `params` must be a
    tuple of values - NEVER build the query string with f-strings or
    .format() using untrusted input. This is what makes the query safe
    from SQL injection; psycopg2 handles the escaping.

    Example:
        run_query(
            "SELECT * FROM orders WHERE customer_id = %s",
            (customer_id,)
        )
    """
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, params)
            rows = cur.fetchall()
            return [dict(row) for row in rows]


def run_write(query: str, params: tuple = ()) -> int:
    """
    Runs a parameterized INSERT/UPDATE query, commits it, and returns
    the affected row's ID if the query used RETURNING, otherwise the
    row count affected.

    Same safety rule as run_query: %s placeholders + params tuple only.
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            conn.commit()
            if cur.description:  # query used RETURNING
                return cur.fetchone()[0]
            return cur.rowcount