#!/bin/sh
# ─────────────────────────────────────────────────────────────────────────────
#  entrypoint.sh
#  Waits for the MySQL container to accept connections, then:
#    1. Runs the database schema / seed script (database.sql).
#    2. Starts the Flask application.
# ─────────────────────────────────────────────────────────────────────────────

set -e

# Defaults (overridden by environment variables from docker-compose / .env)
DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-3306}"
DB_USER="${DB_USER:-sms_user}"
DB_PASSWORD="${DB_PASSWORD:-sms_password}"
DB_NAME="${DB_NAME:-student_management}"

echo "⏳  Waiting for MySQL at ${DB_HOST}:${DB_PORT} ..."

# Poll until MySQL accepts a TCP connection (max 60 s)
MAX_TRIES=30
COUNT=0
until nc -z "$DB_HOST" "$DB_PORT" 2>/dev/null; do
  COUNT=$((COUNT + 1))
  if [ "$COUNT" -ge "$MAX_TRIES" ]; then
    echo "❌  MySQL did not become ready in time. Exiting."
    exit 1
  fi
  echo "   still waiting ($COUNT/$MAX_TRIES) ..."
  sleep 2
done

echo "✅  MySQL is up."

# Give MySQL a couple of extra seconds to finish its own initialization
# (the first boot of the mysql:8 image runs init scripts).
sleep 3

echo "📦  Initialising database schema and seed data ..."
mysql \
  --host="$DB_HOST" \
  --port="$DB_PORT" \
  --user="$DB_USER" \
  --password="$DB_PASSWORD" \
  < /app/database.sql && echo "✅  Schema applied." || {
    echo "⚠️   Schema script returned an error (probably safe — tables already exist)."
  }

echo "🚀  Starting Flask application ..."
exec python app.py
