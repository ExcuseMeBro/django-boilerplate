#!/bin/sh
set -e

cd "$(dirname "$0")"

uv sync --locked
uv run --locked python manage.py migrate
exec uv run --locked python manage.py runserver 0.0.0.0:8000
