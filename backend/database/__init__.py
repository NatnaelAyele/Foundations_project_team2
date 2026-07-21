import os
from urllib.parse import parse_qs, unquote, urlparse

from dotenv import load_dotenv
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor

from backend.config import Config
from backend.database.connection import Base, get_db

load_dotenv()

_pool = None


def _build_pool():
    database_url = Config.get_database_url()
    parsed = urlparse(database_url)

    host = parsed.hostname or Config.DATABASE_HOST
    port = parsed.port or int(Config.DATABASE_PORT)
    user = parsed.username or Config.DATABASE_USER
    password = unquote(parsed.password or "") or Config.DATABASE_PASSWORD
    dbname = parsed.path.lstrip("/") or Config.DATABASE_NAME
    query_params = parse_qs(parsed.query)
    sslmode = query_params.get("sslmode", [Config.DATABASE_SSL_MODE])[0]
    if sslmode is None:
        sslmode = "prefer"
    elif sslmode.lower() in {"false", "0", "no", "off"}:
        sslmode = "prefer"

    return pool.ThreadedConnectionPool(
        minconn=1,
        maxconn=int(os.getenv("DATABASE_POOL_SIZE", "5")),
        host=host,
        port=port,
        user=user,
        password=password,
        dbname=dbname,
        connect_timeout=5,
        sslmode=sslmode,
    )


def _get_pool():
    global _pool
    if _pool is None:
        _pool = _build_pool()
    return _pool


def fetch_one(query, params=None):
    conn = _get_pool().getconn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params or ())
            row = cursor.fetchone()
            return dict(row) if row else None
    finally:
        _get_pool().putconn(conn)


def fetch_all(query, params=None):
    conn = _get_pool().getconn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params or ())
            return [dict(row) for row in cursor.fetchall()]
    finally:
        _get_pool().putconn(conn)


def execute_query(query, params=None):
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
    try:
        fetch_one("SELECT 1 AS ok")
        print("Database pool ready.")
    except Exception as error:
        print("\n========== DATABASE WARM-UP FAILED ==========")
        print(error)
        print("=============================================\n")


def close_pool():
    global _pool
    if _pool is not None:
        _pool.closeall()
        _pool = None


__all__ = ["Base", "get_db", "fetch_one", "fetch_all", "execute_query", "warm_up_pool", "close_pool"]
