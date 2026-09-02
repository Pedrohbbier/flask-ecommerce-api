#!/usr/bin/env bash
# Wait for MySQL, apply migrations, then hand over to the container command.
set -e

host="${MYSQL_HOST:-db}"
port="${MYSQL_PORT:-3306}"

echo "Waiting for MySQL at ${host}:${port}..."
until mysqladmin ping -h "${host}" -P "${port}" --silent >/dev/null 2>&1; do
  sleep 1
done
echo "MySQL is up."

echo "Applying database migrations..."
flask db upgrade

exec "$@"
