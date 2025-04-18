#! /usr/bin/env bash

set -e
set -x

# Let the DB start
python app/scripts/backend_pre_start.py

# Run migrations
alembic upgrade head

# # Create initial data in DB
# python app/initial_data.py
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080} --workers 4
