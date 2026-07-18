import os

import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

# One shared connection pool for the whole app.
#
# Opening a new connection per query is what made the USSD flow time out:
# every connect costs a TCP + TLS handshake. A pool opens connections once
# and reuses them, so each query costs milliseconds.
_pool = None


def _build_pool():
    """
    Creates the connection pool once, on first use.
    """
    return pool.ThreadedConnectionPool(
        minconn=1,
        maxconn=int(os.getenv("DB_POOL_SIZE", "5")),
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "5432")),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD"),
        dbname=os.getenv("DB_NAME", "freshlink"),
        connect_timeout=5,
        sslmode=os.getenv("DB_SSLMODE", "prefer"),
    )


def _get_pool():
    global _pool
    if _pool is None:
        _pool = _build_pool()
    return _pool


def fetch_one(query, params=None):
    """
    Runs a SELECT query and returns one row as a dictionary.
    """
    conn = _get_pool().getconn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params or ())
            row = cursor.fetchone()
            return dict(row) if row else None
    finally:
        _get_pool().putconn(conn)


def fetch_all(query, params=None):
    """
    Runs a SELECT query and returns many rows as dictionaries.
    """
    conn = _get_pool().getconn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params or ())
            return [dict(row) for row in cursor.fetchall()]
    finally:
        _get_pool().putconn(conn)


def execute_query(query, params=None):
    """
    Runs INSERT, UPDATE, or DELETE.

    PostgreSQL has no cursor.lastrowid. To get a new id back, add
    RETURNING to the INSERT and this returns it automatically.

        execute_query("INSERT INTO t (a) VALUES (%s) RETURNING t_id", (1,))
    """
    conn = _get_pool().getconn()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params or ())

            new_id = None
            if cursor.description is not None:
                row = cursor.fetchone()
                if row:
                    new_id = row[0]

            conn.commit()
            return new_id
    except Exception:
        conn.rollback()
        raise
    finally:
        _get_pool().putconn(conn)


def warm_up_pool():
    """
    Opens the pool at startup so the first farmer does not pay the
    connection cost during their USSD session.
    """
    try:
        fetch_one("SELECT 1 AS ok")
        print("Database pool ready.")
    except Exception as error:
        print("\n========== DATABASE WARM-UP FAILED ==========")
        print(error)
        print("=============================================\n")


def close_pool():
    """
    Closes all pooled connections on shutdown.
    """
    global _pool
    if _pool is not None:
        _pool.closeall()
        _pool = None