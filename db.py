"""
Database helper functions.

Every function uses parameterized queries (the %s placeholders) so that
user input is never concatenated into SQL. This protects against SQL
injection.

Each helper opens its own short-lived connection. This is simple and works
well for a beginner-friendly Flask app. For a larger app you would use a
connection pool.
"""

import pymysql

from config import Config


def get_connection():
    """Open a new MySQL connection using the values from .env."""
    return pymysql.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )


def execute(query, params=()):
    """
    Run an INSERT / UPDATE / DELETE and return the number of affected rows.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            rows = cursor.execute(query, params)
        conn.commit()
        return rows
    finally:
        conn.close()


def fetch_all(query, params=()):
    """Run a SELECT and return every matching row as a list of dicts."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
    finally:
        conn.close()


def fetch_one(query, params=()):
    """Run a SELECT and return the first matching row as a dict (or None)."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchone()
    finally:
        conn.close()
