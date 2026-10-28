"""
Application configuration.

Values are read from environment variables (usually from the .env file).
The second argument of os.getenv() is a fallback used during local development.
"""

import os

from dotenv import load_dotenv

# Load variables from a file named ".env" in the project root, if it exists.
load_dotenv()


class Config:
    # Flask uses this key to sign session cookies and flash messages.
    # Change it to a long random string in your .env file.
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-me")

    # MySQL connection details.
    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "student_management")
